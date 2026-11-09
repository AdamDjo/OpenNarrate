# Son et montage

Vidéo 16:9, 1920×1080, 30 i/s. **La voix décide du rythme** : chaque plan dure le temps de sa voix.

## Le son
| Règle | Valeur | Réglage |
|---|---|---|
| **La musique ne dépasse jamais la voix** | -36 LUFS, voix ≈ -24 | `CIBLE_MUSIQUE`, calcul automatique par fichier |
| Pas de passage oublié sans musique | Tout silence doit être un choix | `"musiques"` de `montage_images.json` |
| Une musique trop courte | Elle se répète seule | automatique |
| Pas de fond sonore continu | Feu seulement à 2 ou 3 moments calmes, très bas | `"feu_passages"`, volume 0,12 à 0,15 |
| **Peu de bruitages, jamais bizarres** | 1 ou 2 par vidéo, dans le doute aucun | `"bruitages"` |
| Silence entre deux passages | 0,7 s minimum | `"ecarts_min"` pour plus |
| Volume final | -14 LUFS, pics sous -1 dB | `montage` et `finir` |

Le volume seul ne veut rien dire : deux musiques au même réglage peuvent différer de 8 dB. On ne règle donc jamais une musique à la main.

## L'image
- Zoom lent calculé au sous-pixel sur la carte graphique (`kenburns.py`) : le zoom de FFmpeg fait trembler l'image.
- Pas de grain animé : il fourmille.
- Durées et fondus en nombre entier d'images, sinon l'image s'arrête en cours de vidéo.

## Les textes à l'écran
- Grand nom net, contour franc, **rien autour** (`titres_png.py`).
- **Chaque vidéo a son thème** : `"theme_titres"` dans `montage_images.json`, choisi selon le sujet. Exemple : `{"police": "Polices/X.ttf", "couleur": [r,g,b], "couleur_sous": [r,g,b], "contour": [r,g,b], "casse": "telle_quelle", "fin": {"couleur": [r,g,b], "y": 380}}`. Sections possibles : `ouverture`, `chapitre`, `fin` (taille, y, taille_sous, y_sous, couleurs). La police doit être libre (OFL) et avoir les accents de la langue : la noter dans `sources.md`.
- Le grand titre parle du **sujet**, pas de la chaîne (`"titre_ouverture"`).
- Police en majuscules si ses minuscules sont ambiguës.
- **Toujours un aperçu sur les vrais fonds avant le rendu**, y compris un fond clair, où un contour coloré ressort moins.

## La fin
Jamais de coupure nette : le narrateur invite à s'abonner, puis **écran de fin de 15 s** sur le dernier plan (`"ecran_fin"`), son et image en fondu long. YouTube y place ses éléments de fin (5 à 20 s).

## Le contrôle (`verifier`, obligatoire avant de montrer)
Image et son de même durée, aucun chevauchement de voix, musique sous la voix, aucun plan figé ni noir, niveaux. Le rapport signale ce qui ne va pas. Il ne remplace pas une écoute : l'outil ne sait pas si c'est beau.
