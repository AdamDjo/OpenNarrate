"""Calcule le montage d'une vidéo (section "magique" de episode.json) pour Outils/montage.py.
Usage : fabriquer.py plan <projet>
Entrées : blocs.json, montage_images.json (tous les réglages de la vidéo, voir Modeles/projet/), voix/narration/bNN.wav.
Règles :
- durée d'un bloc = durée de sa voix + 0,9 s (+ silence demandé) ; ses images se partagent ce temps ;
- chaque image bouge (zoom lent qui alterne avant / arrière) ; jamais d'image figée ;
- transitions selon la couche : Vision = fondu long, Feu = fondu, Monde = fondu, Carnet = page qui glisse ;
  un bloc listé dans "chocs" = coupe nette + secousse + flash ;
- la musique est calée sous la voix, 0,7 s de silence minimum entre deux passages.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG, FFPROBE

ECART_MIN = 0.7  # s de silence minimum entre deux blocs de voix
# Règle : la musique ne dépasse JAMAIS la voix (voix ≈ -24 à -26 LUFS).
# Chaque fichier a son propre niveau (de -7 à -16 LUFS) : le volume est calculé pour que toutes arrivent à ce niveau.
CIBLE_MUSIQUE = -36.0  # environ 12 dB sous la voix
_bornes = {}
ep = Path(sys.argv[1])
nom = sys.argv[2] if len(sys.argv) > 2 else ep.name + "_v1"
blocs = [b for b in json.loads((ep / "blocs.json").read_text(encoding="utf-8")) if b["mots"]]
conf = json.loads((ep / "montage_images.json").read_text(encoding="utf-8"))
alias, centres = conf["alias"], conf["centres"]
MUS = "../../Musique/themes/"
AMB = "../../Musique/ambiance/"
CHOC = set(conf.get("chocs", []))
CLIP_TITRE = conf.get("clip_titre")
COULEUR = {"couleur": conf["couleur_titres"]} if conf.get("couleur_titres") else {}  # ancien réglage : préférer "theme_titres"
TRANS = {"VISION": ("dissolve", 1.0), "FEU": ("fade", 0.7), "MONDE": ("dissolve", 0.8), "CARNET": ("slideleft", 0.6)}


def duree(f):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def niveau(f, d):
    """Niveau réel (LUFS) d'un fichier sur ses d premières secondes."""
    err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-t", str(d), "-i", str(f), "-af", "ebur128=framelog=quiet",
                          "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def fin_utile(f):
    """Fin de la vraie musique, avant le silence final éventuel (en secondes)."""
    d = duree(f)
    err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(f), "-af", "silencedetect=n=-50dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    debuts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    fin_sil = re.findall(r"silence_end: (-?[\d.]+)", err)
    if debuts and (len(fin_sil) < len(debuts) or float(fin_sil[-1]) >= d - 0.05):
        return debuts[-1]
    return d


def debut_utile(f):
    """Début de la vraie musique, après le silence éventuel du début du fichier (en secondes)."""
    err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-t", "15", "-i", str(f), "-af", "silencedetect=n=-50dB:d=0.1", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    m = re.search(r"silence_start: (-?[\d.]+)\s.*?silence_end: ([\d.]+)", err, re.S)
    return float(m.group(2)) if m and float(m.group(1)) <= 0.01 else 0.0


def bornes_parole(f):
    """(début, fin) de la vraie parole dans un fichier voix, en secondes (fenêtres de 20 ms au-dessus de -38 dB)."""
    f = str(f)
    if f not in _bornes:
        brut = subprocess.run([FFMPEG, "-v", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                              capture_output=True, check=True).stdout
        a = np.frombuffer(brut, dtype=np.float32)
        n = 320
        rms = np.sqrt(np.mean(a[:len(a) // n * n].reshape(-1, n) ** 2, axis=1))
        i = np.where(rms > 10 ** (-38 / 20))[0]
        _bornes[f] = (float(i[0]) * n / 16000, float(i[-1] + 1) * n / 16000)
    return _bornes[f]


def departs():
    """Heure de début de chaque morceau, fondus déduits (mêmes règles que montage.py)."""
    t = [0.0]
    for i in range(1, len(morceaux)):
        td = morceaux[i].get("tduree", 0.0) if morceaux[i].get("transition") else 1 / 30
        t.append(t[-1] + morceaux[i - 1]["duree"] - td)
    return t


def choisir_anim(cle, emo):
    """Animation prévue pour cette image ("animations" de montage_images.json), selon l'émotion du bloc."""
    base = cle if cle in alias else cle[:-1]
    a = conf.get("animations", {}).get(base)
    if not a:
        return None
    r = {"clip": a.get("selon_emotion", {}).get(emo, a["clip"])}
    if a.get("boucle"):
        r["boucle"] = True
    if a.get("longueur"):
        r["longueur"] = a["longueur"]
    return r


def image(cle):
    base = cle if cle in alias else cle[:-1]  # « C03a » = même image que C03 avec un autre centre
    return alias[base], centres.get(cle, centres.get(base, [0.5, 0.5]))


morceaux, titres, sons, debut_bloc, duree_bloc = [], [], [], {}, {}
chap_vu = None
k = 0
for b in blocs:
    n = b["n"]
    voix = ep / "voix" / "narration" / f"b{n:02d}.wav"
    dv = duree(voix)
    total = dv + 0.9 + b.get("silence_apres", 0.0)
    imgs = conf["blocs"][str(n)]
    part = max(3.0, total / len(imgs))
    debut_bloc[n] = len(morceaux)
    duree_bloc[n] = total
    emo = (re.search(r"\{([a-zé]+)\}", b["texte"]) or [None, "neutre"])[1]
    for j, cle in enumerate(imgs):
        chemin, centre = image(cle)
        z = [1.0, 1.08] if k % 2 == 0 else [1.08, 1.0]
        if cle == "F2":
            z = [1.04, 1.12]
        dm = round(part if j < len(imgs) - 1 else max(3.0, total - part * (len(imgs) - 1)), 2)
        m = {"image": chemin, "duree": dm, "zoom": z, "centre": centre}
        # animation Wan disponible pour cette image ? (dossier anim/clips) → on l'utilise à la place de l'image fixe
        anim = choisir_anim(cle, emo)
        if anim and (ep / "anim" / "clips" / f"{anim['clip']}.mp4").exists():
            m = {"clip": anim["clip"], "duree": dm}
            if anim.get("boucle"):
                m["boucle"] = True
            else:
                m.update({"de": 0, "a": min(anim["longueur"], dm)})
                if dm > anim["longueur"]:
                    m["gel"] = round(dm - anim["longueur"], 2)  # on reste sur la dernière image (le poing fermé…)
        if morceaux:
            if j == 0:
                tr, td = TRANS[b["couche"]]
                if n in CHOC:
                    m.update({"secousse": 22, "flash": True})
                else:
                    m.update({"transition": tr, "tduree": td})
            else:
                m.update({"transition": "dissolve", "tduree": 0.6})
        morceaux.append(m)
        k += 1
    # titre de chapitre
    c = b["chapitre"]
    if c != chap_vu:
        chap_vu = c
        propre = c.split(". ", 1)[1] if c[:1].isdigit() and ". " in c else c
        if c and not c.startswith("0.") and c not in conf.get("chapitres_sans_titre", []):
            titres.append({"texte": propre, "style": "chapitre", "morceau": debut_bloc[n], "dt": 0.7, "duree": 4.2, **COULEUR})
    sons.append({"fichier": f"voix/narration/b{n:02d}.wav", "morceau": debut_bloc[n], "dt": 0.35, "voix": True, "volume": 1.0})
    # après l'étincelle : le titre de la chaîne sur le feu
    if n == conf.get("titre_apres_bloc", 2):
        titre_m = {"image": alias["F3"], "duree": 4.5, "zoom": [1.0, 1.05], "centre": [0.35, 0.6]}
        if CLIP_TITRE and (ep / "anim" / "clips" / f"{CLIP_TITRE}.mp4").exists():
            titre_m = {"clip": CLIP_TITRE, "boucle": True, "duree": 4.5}
        morceaux.append({**titre_m, "transition": "fadeblack", "tduree": 1.0})
        # titre sur le sujet de la vidéo, pas sur la chaîne → "titre_ouverture" de montage_images.json
        ouv = conf["titre_ouverture"]
        titres.append({"texte": ouv["grand"], "sous": ouv["petit"], "style": "ouverture", "morceau": len(morceaux) - 1, "dt": 0.5, "duree": 3.8, **COULEUR})

# écran de fin : on reste sur le dernier plan, avec le texte d'abonnement.
# YouTube permet d'y poser ses éléments de fin (5 à 20 s). "ecran_fin": {"duree", "texte", "sous"} dans montage_images.json
if conf.get("ecran_fin"):
    fin_e, dernier = conf["ecran_fin"], morceaux[-1]
    titres.append({"texte": fin_e["texte"], "sous": fin_e.get("sous"), "style": "fin", "morceau": len(morceaux) - 1,
                   "dt": round(dernier["duree"] + 0.3, 2), "duree": fin_e["duree"] - 1.5, **COULEUR})
    dernier["duree"] = round(dernier["duree"] + fin_e["duree"], 2)

# fond sonore sous toute la vidéo : seulement si montage_images.json en donne un ("fond": {"fichier", "volume"}).
if conf.get("fond"):
    sons.append({"fichier": AMB + conf["fond"]["fichier"], "morceau": 0, "dt": 0,
                 "volume": conf["fond"].get("volume", 0.3), "fondu_in": 2})
musiques_placees = []
# 16 nov. 2026 (« des bruits et des coupures d'une scène à l'autre, trouver la cause une fois pour toutes ») : chaque
# musique finissait pile au changement de scène et la suivante commençait après, en fondu → 0,3 à 1 s de SILENCE TOTAL à
# chaque changement de musique (mesuré : 5 trous dans une vidéo de 7 min). Maintenant elles se chevauchent : la nouvelle
# commence CHEVAUCHE s avant le changement de scène, l'ancienne s'éteint CHEVAUCHE s après (fondu enchaîné). Après une
# musique « coupe_net », la suivante démarre tout de suite, avec un fondu court.
CHEVAUCHE = 1.5
prec = None
# Jamais une musique réclamée par Content ID (liste dans Musique/INTERDITES.txt) : la vidéo perdrait ses revenus.
import musique
for mu in conf["musiques"]:
    try:
        musique.verifier(mu["fichier"])
    except musique.MusiqueRefusee as e:
        sys.exit(f"ARRÊT : {e}")
for mu in sorted(conf["musiques"], key=lambda x: x["de_bloc"]):
    d = sum(duree_bloc[n] for n in duree_bloc if mu["de_bloc"] <= n <= mu["a_bloc"])
    niv = niveau(ep / (MUS + mu["fichier"]), d)
    # Une voix douce (narratrice) ou un orchestre très plein masquent la voix même à -36 : "cible_musique": -39 dans
    # montage_images.json pour cette vidéo, et toutes les musiques sont creusées dans les fréquences de la voix (creux_voix).
    cible = conf.get("cible_musique", CIBLE_MUSIQUE)
    vol = round(10 ** ((cible - niv) / 20), 4)  # le "volume" de montage_images.json n'est plus utilisé
    print(f"  musique {mu['fichier']} : fichier à {niv:.1f} LUFS → volume {vol} pour {cible} LUFS")
    enchaine = prec is not None and prec["a_bloc"] + 1 >= mu["de_bloc"]
    dt, fin_in = 0.2, 2.5
    if enchaine:
        dt, fin_in = (0.0, 0.6) if prec.get("coupe_net") else (-CHEVAUCHE, 2 * CHEVAUCHE)
    s = {"fichier": MUS + mu["fichier"], "morceau": debut_bloc[mu["de_bloc"]], "dt": dt, "volume": vol,
         "duree": round(d, 2), "fondu_in": fin_in, "fondu_out": 0.05 if mu.get("coupe_net") else 2 * CHEVAUCHE, "creux_voix": True}
    if mu.get("debut"):  # commencer plus loin dans le morceau (ex. un vrai silence au milieu du fichier)
        s["debut"] = mu["debut"]
    elif (d0 := debut_utile(ep / (MUS + mu["fichier"]))) > 0.1:  # silence au début du fichier : on le saute (sinon petit creux)
        s["debut"] = round(d0, 2)
    prec = mu
    sons.append(s)
    musiques_placees.append((s, mu))
for br in conf["bruitages"]:
    s = {"fichier": AMB + br["fichier"], "morceau": debut_bloc[br["bloc"]], "dt": br.get("dt", 0.0), "volume": br["volume"]}
    if br.get("grave"):
        s["grave"] = br["grave"]
    sons.append(s)
# feu de camp seulement à quelques moments calmes
for fp in conf.get("feu_passages", []):
    fichier = AMB + conf.get("feu_fichier", "feu_reel.mp3")
    if not (ep / fichier).exists():
        print(f"(pas de feu : {fichier} absent)")
        break
    sons.append({"fichier": fichier, "morceau": debut_bloc[fp["bloc"]], "dt": fp.get("dt", 0.0), "debut": fp.get("debut", 0),
                 "volume": fp.get("volume", 0.35), "duree": fp["duree"], "fondu_in": 1.5, "fondu_out": 2.0})

# Silence minimum entre deux passages.
# Les fondus entre images mangent le temps prévu pour chaque bloc : on mesure la vraie parole et on rallonge seulement
# ce qui est trop serré, pour garder le rythme du reste. Par défaut ECART_MIN ; "ecarts_min": {"2": 1.2} = après le bloc 2.
for a, b in zip([s for s in sons if s.get("voix")], [s for s in sons if s.get("voix")][1:]):
    n_a = int(re.search(r"b(\d+)\.wav", a["fichier"]).group(1))
    voulu = conf.get("ecarts_min", {}).get(str(n_a), ECART_MIN)
    t = departs()
    ecart = (t[b["morceau"]] + b["dt"] + bornes_parole(ep / b["fichier"])[0]) - (t[a["morceau"]] + a["dt"] + bornes_parole(ep / a["fichier"])[1])
    if ecart < voulu:
        m = morceaux[b["morceau"] - 1]
        m["duree"] = round(m["duree"] + voulu - ecart, 2)
        if "gel" in m or ("a" in m and m["duree"] > m["a"] - m.get("de", 0)):
            m["gel"] = round(m["duree"] - (m["a"] - m.get("de", 0)), 2)
        print(f"  pause rallongée après b{n_a:02d} : {ecart:+.2f} s → {voulu:.2f} s")

# Chaque musique s'arrête où son dernier bloc finit vraiment (sinon, avec les fondus, deux musiques se superposaient quelques secondes).
t = departs()
for s, mu in musiques_placees:
    suivants = [debut_bloc[n] for n in debut_bloc if n > mu["a_bloc"]]
    fin = t[min(suivants)] if suivants else t[-1] + morceaux[-1]["duree"]
    if suivants and not mu.get("coupe_net"):
        fin += CHEVAUCHE  # fondu enchaîné avec la musique suivante (voir CHEVAUCHE)
    s["duree"] = round(fin - t[s["morceau"]] - s["dt"], 2)
    # Fichier plus court que le passage : on le relance en fondu enchaîné JUSTE AVANT son silence de fin. (une répétition simple
    # rejouait le silence de fin du fichier : 5 s de trou en pleine vidéo.)
    utile = fin_utile(ep / s["fichier"]) - s.get("debut", 0)
    if s["duree"] > utile:
        total, pas, k = s["duree"], max(utile - 2 * CHEVAUCHE, 1.0), 1
        fondu_fin = s["fondu_out"]
        s.update({"duree": round(utile, 2), "fondu_out": 2 * CHEVAUCHE})
        while k * pas + utile < total:
            sons.append({**s, "dt": round(s["dt"] + k * pas, 2), "fondu_in": 2 * CHEVAUCHE})
            k += 1
        sons.append({**s, "dt": round(s["dt"] + k * pas, 2), "fondu_in": 2 * CHEVAUCHE,
                     "duree": round(total - k * pas, 2), "fondu_out": fondu_fin})
        print(f"  musique {mu['fichier']} relancée {k} fois en fondu (fichier utile {utile:.1f} s, passage {total:.1f} s)")

ep_json = {"magique": {"format": "16:9", "nom": nom, "bloom": 0.18, "fin_son": 8.0, "fin_image": 3.0, "dossier_clips": "anim/clips",
                       "theme_titres": conf.get("theme_titres", {}), "morceaux": morceaux, "titres": titres, "sons": sons}}
(ep / "episode.json").write_text(json.dumps(ep_json, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(m["duree"] for m in morceaux)
print(f"{len(morceaux)} morceaux, {len(titres)} titres, {len(sons)} sons, ≈ {tot/60:.1f} min → {ep / 'episode.json'}")
