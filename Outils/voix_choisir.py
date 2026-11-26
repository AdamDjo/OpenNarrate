"""Étape 2/2 de la voix : réécoute chaque prise (faster-whisper), garde la plus fidèle au texte, assemble.

Usage (Python 3.12 du système, qui a faster-whisper) :
  python -I Outils\\voix\\voix_choisir.py <dossier_sortie> [--vitesse 0.92] [nom1 nom2 ...]
Pour chaque <dossier_sortie>/<nom>/plan.json :
  - transcrit toutes les prises, note la ressemblance avec le texte (0 à 1) et le débit (mots/s) ;
  - privilégie le texte fidèle, puis départage selon le débit et les bruits en bordure ;
  - signale les transcriptions peu fiables, le débit encore excessif après correction et les bruits en bordure ;
  - assemble : prises choisies + pauses du plan, ralenti --vitesse (ffmpeg atempo, même hauteur de voix),
    → <dossier_sortie>/<nom>.wav ; rapport dans <dossier_sortie>/<nom>/choix.json.
"""
import difflib
import json
import re
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG

DEBIT_MAX = 3.15   # mots/s après ralenti (≈ 190 mots/min) : au-delà, le morceau est ralenti automatiquement
ATEMPO_MIN = 0.72  # ralenti maximal, pour ne pas déformer la voix
DEBIT_MIN = 1.3
DEBIT_CIBLE = 2.6
BRUIT_BORD = 10 ** (-36 / 20)


def option(args, nom, defaut):
    if nom in args:
        i = args.index(nom)
        val = args[i + 1]
        del args[i:i + 2]
        return val
    return defaut


def norme(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\b(\d+)\b", " ", t)  # whisper écrit les nombres en chiffres : on ignore les nombres des deux côtés
    return [w for w in re.sub(r"[^a-z ]+", " ", t).split() if w not in NOMBRES]


NOMBRES = set("zero un une deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize "
              "vingt vingts trente quarante cinquante soixante cent cents mille million millions".split())


def lire16k(f):
    out = subprocess.run([FFMPEG, "-v", "error", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.int16).astype(np.float32) / 32768


def bruit_bord(audio, debut, fin):
    """Measure the strongest 20 ms RMS outside the transcribed speech."""
    zones = (audio[:max(0, round((debut - 0.15) * 16000))],
             audio[round((fin + 0.25) * 16000):])
    niveaux = []
    for zone in zones:
        trames = zone[:len(zone) // 320 * 320].reshape(-1, 320)
        if len(trames):
            niveaux.append(float(np.sqrt(np.mean(trames ** 2, axis=1)).max()))
    return max(niveaux, default=0.0)


args = sys.argv[1:]
vitesse = float(option(args, "--vitesse", "0.88"))
etirement_opt = option(args, "--etirement", None)
racine = Path(args[0])
# Réglages par vidéo dans montage_images.json (voix qui parle naturellement vite : un gros ralenti la déforme) :
# "vitesse_voix" (ralenti global, défaut 0,88), "debit_max_voix", "ralenti_min_voix", "etirement_voix": "rubberband"
# (ralenti de meilleure qualité qu'atempo quand on ralentit beaucoup).
_reglages = racine.parent.parent / "montage_images.json"
_r = json.loads(_reglages.read_text(encoding="utf-8")) if _reglages.exists() else {}
ETIREMENT = etirement_opt or _r.get("etirement_voix", "atempo")
if "--vitesse" not in sys.argv:
    vitesse = float(_r.get("vitesse_voix", vitesse))
DEBIT_MAX = float(_r.get("debit_max_voix", DEBIT_MAX))
ATEMPO_MIN = float(_r.get("ralenti_min_voix", ATEMPO_MIN))
for _o, _v in (("--debit-max", "DEBIT_MAX"), ("--ralenti-min", "ATEMPO_MIN")):
    _x = option(args, _o, None)
    if _x:
        globals()[_v] = float(_x)


def ralenti(tempo):
    if ETIREMENT == "rubberband":
        return f"rubberband=tempo={tempo:.3f}:transients=smooth:detector=soft:window=long:pitchq=quality:formant=preserved"
    return f"atempo={tempo:.3f}"


noms = args[1:] or sorted(p.name for p in racine.iterdir() if (p / "plan.json").exists())
rapport = racine / "alertes.json"
modele = WhisperModel("small", device="cpu", compute_type="int8")

alertes = []
if args[1:] and rapport.exists():
    alertes = [a for a in json.loads(rapport.read_text(encoding="utf-8")) if a["bloc"] not in noms]
for nom in noms:
    d = racine / nom
    plan = json.loads((d / "plan.json").read_text(encoding="utf-8"))
    cache_f = d / "transcriptions.json"  # évite de retranscrire les prises déjà écoutées
    cache = json.loads(cache_f.read_text(encoding="utf-8")) if cache_f.exists() else {}
    choix, liste = [], []
    for i, m in enumerate(plan["morceaux"], 1):
        attendu = [w for w in norme(m["texte"])]
        meilleur = None
        for f in sorted(d.glob(f"c{i:02d}_p*.wav")):
            if not re.fullmatch(rf"c{i:02d}_p\d+\.wav", f.name):
                continue
            audio = lire16k(f)
            cle = f"{f.name}:{f.stat().st_mtime_ns}"
            if cle not in cache or f"{cle}:debut" not in cache:
                segs = list(modele.transcribe(audio, language=plan.get("langue", "fr"), word_timestamps=True)[0])
                cache[cle] = " ".join(s.text for s in segs)
                cache[f"{cle}:fin"] = max((w.end for s in segs for w in (s.words or [])), default=None)
                cache[f"{cle}:debut"] = min((w.start for s in segs for w in (s.words or [])), default=None)
            entendu = cache[cle]
            fin_mots, debut_mots = cache[f"{cle}:fin"], cache[f"{cle}:debut"]
            score = difflib.SequenceMatcher(None, attendu, norme(entendu)).ratio()
            duree = len(audio) / 16000
            parole = debut_mots is not None and fin_mots is not None and fin_mots > debut_mots
            # Débit mesuré sur TOUTE la prise. Mesuré sur la seule parole, il paraît plus élevé : le ralenti devient
            # beaucoup plus fort (0,77 au lieu de 0,88) et la voix « dérape ». Ne pas y revenir.
            debit = len(m["texte"].split()) / max(duree, 0.1)
            tempo = vitesse * m.get("tempo", 1.0)
            if debit * tempo > DEBIT_MAX:
                tempo = max(ATEMPO_MIN, DEBIT_MAX / debit)
            vitesse_limite = debit * tempo > DEBIT_MAX + 0.01
            bruit = bruit_bord(audio, debut_mots, fin_mots) if parole else 0.0
            raisons = []
            if score < 0.72 or not parole:
                raisons.append("transcription")
            if debit * tempo < DEBIT_MIN or vitesse_limite:
                raisons.append("speaking_rate")
            if bruit > BRUIT_BORD:
                raisons.append("edge_noise")
            # mots ajoutés après la fin de la phrase (la voix IA répète ou invente) : une prise propre au score un peu
            # plus bas doit toujours passer avant
            _ops = difflib.SequenceMatcher(None, attendu, norme(entendu)).get_opcodes()
            trop = bool(_ops) and _ops[-1][0] in ("insert", "replace") and (_ops[-1][4] - _ops[-1][3]) - (_ops[-1][2] - _ops[-1][1]) >= 2
            if trop:
                raisons.append("mots_en_trop")
            classement = (parole, not trop, score, not raisons, bruit <= BRUIT_BORD, -abs(debit * tempo - DEBIT_CIBLE), -bruit)
            if meilleur is None or classement > meilleur_classement:
                meilleur_classement = classement
                meilleur = {"fichier": f.name, "score": round(score, 2), "debit": round(debit, 2), "note": score, "entendu": entendu.strip(),
                            "fin_mots": fin_mots, "debut_mots": debut_mots, "duree": duree,
                            "tempo_final": round(tempo, 3), "reasons": raisons}
        if meilleur is None:
            sys.exit(f"No complete takes for {nom} c{i:02d}")
        alerte = bool(meilleur["reasons"])
        meilleur["alerte"] = alerte
        meilleur["texte"] = m["texte"]
        if alerte:
            alertes.append({"bloc": nom, "morceau": i, "texte": m["texte"], "score": meilleur["score"],
                            "debit": meilleur["debit"], "reasons": meilleur["reasons"]})
        choix.append(meilleur)
        # la voix IA ajoute parfois des marmonnements après le dernier mot (« aa aa », 16 nov. 2026
        # déjà vu sur les Shorts) : on coupe 0,25 s après le dernier mot entendu, avec un fondu
        # (et parfois AVANT le premier mot : on commence 0,15 s avant lui)
        coupe = None
        if meilleur.get("fin_mots") and meilleur["fin_mots"] + 0.25 < meilleur["duree"]:
            coupe = meilleur["fin_mots"] + 0.25
        debut = meilleur["debut_mots"] - 0.15 if (meilleur.get("debut_mots") or 0) > 0.4 else None
        liste.append((d / meilleur["fichier"], m["pause"], meilleur["tempo_final"], m.get("volume_db", 0), coupe, debut))
        print(f"{nom} c{i:02d} {'ALERTE' if alerte else 'ok'} score {meilleur['score']} debit {meilleur['debit']} | {meilleur['entendu']}", flush=True)
    (d / "choix.json").write_text(json.dumps(choix, ensure_ascii=False, indent=1), encoding="utf-8")
    cache_f.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    # assemblage : prise, silence, prise, silence… puis ralenti
    entrees, filtres = [], []
    for k, (f, pause, tempo, vol, coupe, debut) in enumerate(liste):
        entrees += ["-i", str(f)]
        d0 = debut or 0
        fin = f"atrim={d0:.2f}:{coupe:.2f},asetpts=PTS-STARTPTS,afade=t=out:st={coupe - d0 - 0.08:.2f}:d=0.08," if coupe else ""
        if debut and not coupe:
            fin = f"atrim=start={d0:.2f},asetpts=PTS-STARTPTS,"
        if debut:
            fin += "afade=t=in:d=0.05,"
        # ralenti global × rythme de l'émotion (triste = plus lent…), volume de l'émotion, puis la pause
        filtres.append(f"[{k}]{fin}aresample=24000,{ralenti(tempo)},volume={vol}dB,"
                       f"apad=pad_dur={pause if k < len(liste) - 1 else 0}[a{k}]")
    # limiteur final : une voix « chaude » + le volume d'une émotion pouvaient saturer
    concat = ("".join(f"[a{k}]" for k in range(len(liste))) + f"concat=n={len(liste)}:v=0:a=1,"
              "alimiter=limit=0.89:attack=3:release=50:level=false[out]")
    subprocess.run([FFMPEG, "-v", "error", "-y", *entrees, "-filter_complex", ";".join(filtres) + ";" + concat,
                    "-map", "[out]", "-ac", "1", "-ar", "24000", str(racine / f"{nom}.wav")], check=True)
    # instant où commence chaque morceau dans le bloc assemblé (sert à la transition de voix de voix_nettoyer.py)
    debuts, t = [], 0.0
    for (f, pause, tempo, vol, coupe, debut) in liste:
        debuts.append(round(t, 3))
        t += ((coupe or lire16k(f).size / 16000) - (debut or 0)) / tempo + pause
    (d / "debuts.json").write_text(json.dumps(debuts), encoding="utf-8")
    (racine / "_bruts" / f"{nom}.wav").unlink(missing_ok=True)  # l'ancienne version non nettoyée n'est plus valable
    print(f"=> {racine / (nom + '.wav')}", flush=True)

temporaire = rapport.with_suffix(".tmp")
temporaire.write_text(json.dumps(alertes, ensure_ascii=False, indent=1), encoding="utf-8")
temporaire.replace(rapport)
print(f"{len(alertes)} morceau(x) en alerte -> {racine / 'alertes.json'}"
      + (" (à refaire : voix_narrateur.py … --refaire alertes.json --prises 3)" if alertes else ""), flush=True)
