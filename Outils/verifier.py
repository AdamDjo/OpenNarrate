"""Contrôle automatique d'une vidéo finie, obligatoire avant de la montrer.
Usage : python -I Outils/verifier.py Episodes/<projet>   (ou : fabriquer.py verifier <projet>)
Vérifie : durée image = son, voix qui se chevauchent, musique sous la voix dans les pauses, plans figés ou noirs, niveaux.
Il ne remplace pas une écoute : il ne sait pas si c'est beau.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG, FFPROBE, RACINE

sys.stdout.reconfigure(encoding="utf-8")
SR, ECART_MIN, MARGE_DB = 16000, 0.6, -3.0
FPS = 30


def lire(f):
    o = subprocess.run([FFMPEG, "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(o, dtype=np.float32).copy()


def bornes(a):
    n = 320
    r = np.sqrt(np.mean(a[:len(a) // n * n].reshape(-1, n) ** 2, axis=1))
    i = np.where(r > 10 ** (-38 / 20))[0]
    return float(i[0]) * n / SR, float(i[-1] + 1) * n / SR


def mm(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


ep = Path(sys.argv[1])
m = json.loads((ep / "episode.json").read_text(encoding="utf-8"))["magique"]
video = RACINE / "A_publier" / f"{m['nom']}.mp4"
p = m["morceaux"]
S = [0.0]
for i in range(1, len(p)):
    S.append(S[i - 1] + p[i - 1]["duree"] - (p[i].get("tduree", 0) if p[i].get("transition") else 1 / FPS))

problemes = []
print("Vidéo :", video.name)

# Durée image = son
d = {}
sortie = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout
for l in sortie.split():
    k, v = l.split(",")
    d[k] = float(v)
print(f"Durée : image {d['video']:.2f} s, son {d['audio']:.2f} s")
if abs(d["video"] - d["audio"]) > 0.15:
    problemes.append("l'image et le son n'ont pas la même durée")

# Voix : silences et musique dans les pauses
mix = lire(video)


def db(a, b):
    x = mix[int(a * SR):int(b * SR)]
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)


voix = []
for s in m["sons"]:
    if s.get("voix"):
        a, b = bornes(lire(ep / s["fichier"]))
        t = S[s["morceau"]] + s["dt"]
        voix.append((s["fichier"][-7:-4], t + a, t + b))
bruitages = [S[s["morceau"]] + s["dt"] for s in m["sons"] if "ambiance/s_" in s["fichier"]]
ecarts, marges = [], []
for a, b in zip(voix, voix[1:]):
    g = b[1] - a[2]
    ecarts.append(g)
    if g < ECART_MIN:
        problemes.append(f"{mm(a[2])} : seulement {g:.2f} s entre {a[0]} et {b[0]}")
    if g > 0.45 and not any(a[2] - 1 <= t <= b[1] + 1 for t in bruitages):
        marge = db(a[2] + 0.2, b[1] - 0.1) - db(a[1], a[2])
        marges.append((round(float(marge), 1), mm(a[2])))
        if marge > MARGE_DB:
            problemes.append(f"{mm(a[2])} : la musique est trop proche de la voix ({marge:.1f} dB)")
print(f"Silences entre voix : minimum {min(ecarts):.2f} s, médiane {sorted(ecarts)[len(ecarts) // 2]:.2f} s")
print("Musique par rapport à la voix (pires pauses, en dB) :", sorted(marges, reverse=True)[:3])

# Plans figés ou noirs (le fondu final est normal)
fin = d["video"] - 3.5
err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(video), "-an", "-vf",
                      "scale=480:-1,freezedetect=n=-70dB:d=2,blackdetect=d=0.5:pix_th=0.05", "-f", "null", "-"],
                     capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
for genre, t in re.findall(r"(freeze_start|black_start):\s*([\d.]+)", err):
    if float(t) < fin:
        problemes.append(f"{mm(float(t))} : plan {'figé' if genre == 'freeze_start' else 'noir'}")

# Niveaux
err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(video), "-map", "0:a", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                     capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])
pic = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
print(f"Niveau : {lufs} LUFS, pic {pic} dB")
if not -16 <= lufs <= -13:
    problemes.append(f"niveau général hors cible : {lufs} LUFS")
if pic > -1:
    problemes.append(f"pic trop haut ({pic} dB) : lancer « finir »")

print("\nRÉSULTAT :", "tout est bon" if not problemes else f"{len(problemes)} point(s) à regarder")
for x in problemes:
    print(" -", x)
