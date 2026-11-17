"""Enlève les respirations et petits bruits ENTRE les mots d'une narration déjà assemblée.
Usage (Python 3.12 du système, qui a faster-whisper) :
  python -I Outils\\voix\\voix_nettoyer.py <dossier_narration> [b02 b03 ...]
Pour chaque bNN.wav :
  - repère chaque mot avec whisper (horodatage mot par mot) ;
  - baisse de 30 dB tout ce qui est hors des mots, avec des fondus de 20 ms (pas de coupure audible) ;
  - sécurité : une zone hors-mots qui ressemble à de la voix (son périodique) n'est pas touchée ;
  - contrôle : retranscrit le résultat et signale si des mots ont disparu.
L'original est gardé dans <dossier>/_bruts/. Relancer voix_choisir.py écrase le nettoyage : relancer ce script ensuite.
"""
import difflib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG

SR = 24000
AVANT, APRES = 0.06, 0.10   # marge gardée autour de chaque mot (s)
BAISSE_DB = -30.0
CENTRE_MAX = 1200           # Hz : en dessous, c'est de la voix (fin de mot) ; au-dessus, un souffle


def lire(f, sr):
    out = subprocess.run([FFMPEG, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def ecrire(f, a):
    subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(f)], input=a.astype(np.float32).tobytes(), check=True)


def mots(modele, a16):
    segs, _ = modele.transcribe(a16, language=LANGUE, word_timestamps=True, condition_on_previous_text=False)
    return [w for s in segs for w in (s.words or [])]


def norme(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def voise(tr):
    """Vrai si la trame est périodique (voix) : pic d'autocorrélation entre 80 et 320 Hz."""
    tr = tr - tr.mean()
    e = float((tr * tr).sum())
    if e < 1e-7:
        return False
    c = np.correlate(tr, tr, "full")[len(tr) - 1:]
    return float(c[SR // 320:SR // 80].max() / e) > 0.55


def fragments(a, mots_garde):
    """Bouts de son isolés (< 0,35 s, entourés d'au moins 0,25 s de silence) : marmonnements de l'IA restés entre deux
    phrases, ou début de mot coupé en fin de fichier. Ils s'entendent comme une « coupure bizarre ».
    On garde un fragment si whisper y entend un mot du texte du bloc (vrai mot court, ex. « Non. »)."""
    pas = int(0.02 * SR)
    db = np.array([20 * np.log10(np.sqrt((a[i:i + pas] ** 2).mean()) + 1e-9) for i in range(0, len(a) - pas + 1, pas)])
    runs, i = [], 0
    while i < len(db):
        if db[i] > -45:
            j = i
            while j < len(db) and db[j] > -45:
                j += 1
            if runs and (i - runs[-1][1]) * 0.02 < 0.12:
                runs[-1] = (runs[-1][0], j)
            else:
                runs.append((i, j))
            i = j
        else:
            i += 1
    duree, out = len(a) / SR, []
    for k, (i, j) in enumerate(runs):
        a0, a1 = i * 0.02, j * 0.02
        avant = a0 - (runs[k - 1][1] * 0.02 if k else 0.0)
        apres = (runs[k + 1][0] * 0.02 if k + 1 < len(runs) else duree) - a1
        if a1 - a0 < 0.35 and avant >= 0.25 and (apres >= 0.25 or k + 1 == len(runs)):
            if not any(w.start < a1 and w.end > a0 and norme(w.word) and len(norme(w.word)[0]) >= 3 and norme(w.word)[0] in mots_garde for w in avant_mots):
                out.append((a0, a1))
    return out


def texte_bloc(nom):
    """Mots attendus du bloc (blocs.json, ou blocs_en.json pour la piste anglaise)."""
    ep = racine.parent.parent
    for fb in ((ep / "blocs_en.json", ep / "blocs.json") if LANGUE == "en" else (ep / "blocs.json",)):
        if fb.exists():
            for b in json.loads(fb.read_text(encoding="utf-8")):
                if f"b{b['n']:02d}" == nom:
                    return set(norme(re.sub(r"\{[^}]*\}", " ", b["texte"])))
    return set()


racine = Path(sys.argv[1])
noms = sys.argv[2:] or sorted(p.stem for p in racine.glob("b*.wav"))
modele = WhisperModel("small", device="cpu", compute_type="int8")
# langue lue dans le plan.json d'un bloc (voix_narrateur.py --langue en pour la piste anglaise)
_plans = sorted(racine.glob("b*/plan.json"))
LANGUE = json.loads(_plans[0].read_text(encoding="utf-8")).get("langue", "fr") if _plans else "fr"
(racine / "_bruts").mkdir(exist_ok=True)
# "filtre_voix" dans montage_images.json : filtre ffmpeg propre à une voix (ex. voix râpeuse, Docs/voix.md)
reglages = racine.parent.parent / "montage_images.json"
filtre_voix = json.loads(reglages.read_text(encoding="utf-8")).get("filtre_voix", "") if reglages.exists() else ""
for nom in noms:
    f = racine / f"{nom}.wav"
    brut = racine / "_bruts" / f"{nom}.wav"
    if not brut.exists():
        shutil.copy(f, brut)
    a = lire(brut, SR)
    avant = mots(modele, lire(brut, 16000))
    garde = np.zeros(len(a), dtype=bool)
    for w in avant:
        garde[max(0, int((w.start - AVANT) * SR)):int((w.end + APRES) * SR)] = True
    # sécurité : on rend les zones hors-mots qui ressemblent à de la voix
    # (une fin de mot est forte et grave ; une respiration est un souffle aigu : vu au diagnostic, « Forever » perdait son r)
    n, pas = int(0.04 * SR), int(0.02 * SR)
    fen = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    voix_ici = []
    for i in range(0, max(len(a) - n, 0), pas):
        tr = a[i:i + n]
        rms = np.sqrt((tr ** 2).mean())
        sp = np.abs(np.fft.rfft(tr * fen)) ** 2
        centre = float((sp * freqs).sum() / (sp.sum() + 1e-12))
        if rms > 0.0056 and (centre < CENTRE_MAX or voise(tr)):
            voix_ici.append(i)
    for i in voix_ici:                                   # on garde aussi un peu autour
        garde[max(0, i - pas):i + n + pas] = True
    gain = np.where(garde, 1.0, 10 ** (BAISSE_DB / 20)).astype(np.float32)
    k = np.hanning(int(0.02 * SR))
    gain = np.convolve(gain, k / k.sum(), "same").astype(np.float32)
    propre = a * gain
    avant_mots = avant
    for a0, a1 in fragments(propre, texte_bloc(nom)):
        i0, i1 = int(a0 * SR), min(len(propre), int(a1 * SR) + int(0.02 * SR))
        propre[i0:i1] *= 10 ** (-40 / 20)
        print(f"  {nom} : bout de son isolé retiré à {a0:.2f}-{a1:.2f} s", flush=True)
    # bords du fichier : jamais un son qui démarre ou s'arrête net (clic, mot coupé)
    fi, fo = int(0.01 * SR), int(0.03 * SR)
    propre[:fi] *= np.linspace(0, 1, fi, dtype=np.float32)
    propre[-fo:] *= np.linspace(1, 0, fo, dtype=np.float32)
    ecrire(f, propre)
    apres = mots(modele, lire(f, 16000))
    t0, t1 = [norme(" ".join(w.word for w in x)) for x in (avant, apres)]
    ratio = difflib.SequenceMatcher(None, t0, t1).ratio() if t0 else 1.0
    bruit = a[~garde]
    pic = 20 * np.log10(float(np.abs(bruit).max()) + 1e-9) if len(bruit) else -120
    etat = "ok" if ratio >= 0.93 and len(t1) >= len(t0) - 2 else "ALERTE"
    print(f"{nom} {etat} mots {len(t0)}->{len(t1)} ressemblance {ratio:.2f} | hors-mots {100 * (~garde).mean():.0f} % du temps, pic retiré {pic:.0f} dB", flush=True)
    if filtre_voix:   # dernier traitement, après le contrôle ; comme on repart de _bruts, il ne s'applique jamais deux fois
        tmp = f.with_suffix(".filtre.wav")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(f), "-af", filtre_voix, "-ac", "1", "-ar", str(SR),
                        "-c:a", "pcm_s16le", str(tmp)], check=True)
        tmp.replace(f)
