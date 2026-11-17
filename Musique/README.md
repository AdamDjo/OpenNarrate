# Musiques et sons

Seulement des fichiers dont vous avez les droits (bibliothèque audio YouTube, Pixabay…), notés dans le `sources.md` du projet.

- `themes/` : musiques, réglées dans `"musiques"` de `montage_images.json`
- `ambiance/` : ambiances et bruitages (`"feu_passages"`, `"bruitages"`)

## Éviter les réclamations Content ID
Une musique annoncée « libre de droits » peut quand même être réclamée par YouTube (Content ID) : la vidéo perd alors ses
revenus, ou la musique doit être coupée dans Studio. Préférez des musiques sous licence claire (CC BY avec crédit dans la
description, CC0, achat) et notez la licence dans `sources.md`.
Dès qu'une réclamation arrive : ajoutez le fichier dans `INTERDITES.txt`, supprimez-le, remplacez-le dans les configs et
remontez la vidéo. `Outils/plan_montage.py` et `Outils/short.py` refusent alors cette musique (voir `Outils/musique.py`).
