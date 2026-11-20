"""Mesure à quel point des fichiers audio ressemblent à une voix de référence (encodeur de voix de Chatterbox).
Usage (Python des voix) : voix_ressemblance.py <reference.wav> <fichier_ou_dossier> [...]
Sert à vérifier que deux répliques de l'addon sont LA MÊME voix avant de les coller pour faire une référence
plus longue (≥ 15 s) : ressemblance ≥ 0,9 = même voix (exemple : deux répliques du même acteur à 0,95, des voix différentes sous 0,8).
"""
import glob
import os
import sys

import librosa
import numpy as np
import torch
from huggingface_hub import hf_hub_download

import chatterbox.mtl_tts as mtl
from chatterbox.models.voice_encoder import VoiceEncoder

sys.stdout.reconfigure(encoding="utf-8")
ve = VoiceEncoder()
ve.load_state_dict(torch.load(hf_hub_download(mtl.REPO_ID, "ve.pt", local_files_only=True), map_location="cpu", weights_only=True))
ve.eval()


def empreinte(f):
    w, _ = librosa.load(f, sr=16000)
    e = ve.embeds_from_wavs([w], sample_rate=16000, as_spk=True)
    return e / np.linalg.norm(e)


ref = empreinte(sys.argv[1])
for cible in sys.argv[2:]:
    fichiers = sorted(glob.glob(os.path.join(cible, "*.wav"))) if os.path.isdir(cible) else [cible]
    for f in fichiers:
        print(f"{float(np.dot(ref, empreinte(f))):.3f}  {f}")
