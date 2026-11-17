"""Bibliothèque de musique : un seul endroit pour savoir quelles musiques ont le droit d'être utilisées.

Règle : toute musique vient de `Musique/themes/` (rangée par ambiance si vous voulez : `triste/piano.mp3`) avec une licence
connue (CC BY, CC0, achat…), et n'est jamais une musique réclamée par Content ID. Une musique « libre » trouvée au hasard peut
quand même être réclamée par YouTube : la vidéo perd alors ses revenus. Dès qu'une réclamation arrive, ajouter le nom du
fichier dans `Musique/INTERDITES.txt` (une ligne : `fichier.mp3 = titre réclamé`) et supprimer le fichier : plus aucun
outil ne l'acceptera, même dans une vieille config.
Utilisé par Outils/plan_montage.py et Outils/short.py.

Usage en ligne de commande :
  python Outils/musique.py                 liste la bibliothèque par ambiance
  python Outils/musique.py triste          liste une ambiance
"""
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
THEMES = RACINE / "Musique" / "themes"
AMBIANCE = RACINE / "Musique" / "ambiance"
LISTE = RACINE / "Musique" / "INTERDITES.txt"


def interdites():
    """Musiques réclamées : nom du fichier → titre réclamé (Musique/INTERDITES.txt)."""
    if not LISTE.exists():
        return {}
    lignes = (l.split("#")[0].strip() for l in LISTE.read_text(encoding="utf-8").splitlines())
    return {nom.strip(): titre.strip() for nom, _, titre in (l.partition("=") for l in lignes if l)}


class MusiqueRefusee(Exception):
    pass


def verifier(chemin):
    """Refuse une musique interdite ou hors de la bibliothèque. `chemin` : relatif à Musique/themes, ou chemin complet."""
    p = Path(chemin)
    refus = interdites()
    if p.name in refus:
        raise MusiqueRefusee(f"{p.name} est interdite (réclamée : « {refus[p.name] or '?'} ») : choisir une autre musique")
    complet = p if p.is_absolute() else THEMES / p
    dedans = [d for d in (THEMES, AMBIANCE) if complet.resolve().is_relative_to(d.resolve())]
    if not dedans:
        raise MusiqueRefusee(f"{chemin} n'est pas dans la bibliothèque (Musique/themes/)")
    if not complet.exists():
        raise MusiqueRefusee(f"{chemin} introuvable dans Musique/themes/")
    return complet


def lister(ambiance=None):
    dossiers = [THEMES / ambiance] if ambiance else [THEMES] + sorted(d for d in THEMES.iterdir() if d.is_dir())
    return {d.name: sorted(f.name for f in d.glob("*.mp3")) for d in dossiers}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for amb, fs in lister(sys.argv[1] if len(sys.argv) > 1 else None).items():
        if fs:
            print(f"== {amb} ({len(fs)})")
            for f in fs:
                print("  ", f)
