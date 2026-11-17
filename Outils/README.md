# Les outils

Une seule commande à retenir : `python Outils/fabriquer.py <étape> <projet>` (la liste s'affiche sans argument). Le déroulé est dans `Docs/workflow.md`.
Les chemins propres à chaque PC sont dans `config.json` (modèle : `config.exemple.json`), lus par `commun.py`. Les réglages d'une vidéo sont dans son `montage_images.json`.

| Outil | Rôle |
|---|---|
| `fabriquer.py` | Lance chaque étape avec le bon Python, crée les projets, finalise la vidéo |
| `script_blocs.py` | Découpe `script.md` en blocs |
| `voix_narrateur.py` | Narration avec Chatterbox, plusieurs prises par morceau |
| `voix_choisir.py` | Réécoute les prises, garde la meilleure, assemble |
| `voix_nettoyer.py` | Retire respirations et bruits entre les mots |
| `animer.py` | Optionnel : anime des plans avec Wan 2.2 (ComfyUI doit tourner) |
| `plan_montage.py` | Calcule le montage : durées, zooms, transitions, musiques, textes |
| `montage.py` | Rendu final (ComfyUI sert seulement à agrandir les clips, s'il y en a) |
| `kenburns.py` | Zoom lent fluide sur la carte graphique |
| `titres_png.py` | Dessine les textes à l'écran |
| `verifier.py` | Contrôle automatique avant de montrer la vidéo |
| `identite.py` | Met le logo et la bannière de la chaîne aux formats YouTube |
| `miniature.py` | Pose le texte sur l'image d'une miniature ; `--police=`, `--couleur=`, `--couleur2=` pour reprendre le thème de la vidéo, `--graisse=Black` (police variable épaisse), `--lueur=` (halo), `--largeur=` (taille du grand texte) |
| `musique.py` | La bibliothèque de musique : liste les musiques par ambiance et refuse celles de `Musique/INTERDITES.txt` (réclamées par Content ID) |
| `short.py` | Fabrique les Shorts verticaux d'une vidéo validée, avec sa voix et ses images, sous-titres compris (`shorts.json`, voir `Docs/shorts.md`) |

## Pour plus tard (non installés)
Shorts verticaux automatiques, retouche du son sans refaire l'image, voix plus naturelle (Qwen3-TTS, MOSS-TTS), effet de profondeur 2.5D (DepthFlow).
