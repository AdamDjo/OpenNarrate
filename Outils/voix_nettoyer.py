"""Enlève les respirations et petits bruits ENTRE les mots d'une narration déjà assemblée.
Usage (Python 3.12 du système, qui a faster-whisper) :
  python -I Outils\\voix_nettoyer.py <dossier_narration> [b02 b03 ...]
Pour chaque bNN.wav :
  - repère chaque mot avec whisper (horodatage mot par mot) ;
  - baisse de 30 dB tout ce qui est hors des mots, avec des fondus de 20 ms (pas de coupure audible) ;
  - sécurité : une zone hors-mots qui ressemble à de la voix (son périodique) n'est pas touchée ;
  - contrôle : retranscrit le résultat et signale si des mots ont disparu.
L'original est gardé dans <dossier>/_bruts/. Relancer voix_choisir.py écrase le nettoyage : relancer ce script ensuite.
"""
import difflib
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


args = sys.argv[1:]
LANGUE = "fr"
if "--langue" in args:
    i = args.index("--langue")
    LANGUE = args[i + 1]
    del args[i:i + 2]
racine = Path(args[0])
noms = args[1:] or sorted(p.stem for p in racine.glob("b*.wav"))
modele = WhisperModel("small", device="cpu", compute_type="int8")
(racine / "_bruts").mkdir(exist_ok=True)
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
    # (une fin de mot est forte et grave ; une respiration est un souffle aigu)
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
    ecrire(f, propre)
    apres = mots(modele, lire(f, 16000))
    t0, t1 = [norme(" ".join(w.word for w in x)) for x in (avant, apres)]
    ratio = difflib.SequenceMatcher(None, t0, t1).ratio() if t0 else 1.0
    bruit = a[~garde]
    pic = 20 * np.log10(float(np.abs(bruit).max()) + 1e-9) if len(bruit) else -120
    etat = "ok" if ratio >= 0.93 and len(t1) >= len(t0) - 2 else "ALERTE"
    print(f"{nom} {etat} mots {len(t0)}->{len(t1)} ressemblance {ratio:.2f} | hors-mots {100 * (~garde).mean():.0f} % du temps, pic retiré {pic:.0f} dB", flush=True)
