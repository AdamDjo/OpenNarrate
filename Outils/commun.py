"""Réglages propres à ce PC, lus dans config.json (à la racine, voir config.exemple.json). Une valeur vide est cherchée automatiquement."""
import json
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
_fichier = RACINE / "config.json"
CONFIG = json.loads(_fichier.read_text(encoding="utf-8")) if _fichier.exists() else {}

FFMPEG = CONFIG.get("ffmpeg") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = CONFIG.get("ffprobe") or shutil.which("ffprobe") or "ffprobe"
# Python qui a PyTorch + CUDA, Chatterbox et Pillow (voix, zooms, textes)
PYTHON_VOIX = CONFIG.get("python_voix") or sys.executable
# Python qui a faster-whisper et numpy (choix des prises, nettoyage, plan, contrôle)
PYTHON_OUTILS = CONFIG.get("python_outils") or sys.executable
COMFY_URL = CONFIG.get("comfy_url") or "http://127.0.0.1:8188"
COMFY_ENTREE = CONFIG.get("comfy_entree") or ""
# Polices : voir Polices/README.md
POLICE_TITRES = CONFIG.get("police_titres") or str(RACINE / "Polices" / "titres.ttf")
POLICE_PHRASE = CONFIG.get("police_phrase") or str(RACINE / "Polices" / "phrase.ttf")
