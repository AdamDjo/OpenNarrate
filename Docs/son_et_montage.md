# Son et montage

Vidéo 16:9, 1920×1080, 30 i/s. **La voix décide du rythme** : chaque plan dure le temps de sa voix.

## Le son
| Règle | Valeur | Réglage |
|---|---|---|
| **La musique ne dépasse jamais la voix** | -36 LUFS, voix ≈ -24 | `CIBLE_MUSIQUE`, calcul automatique par fichier |
| **Voix douce (narratrice) ou orchestre très plein** | `"cible_musique": -39` dans `montage_images.json` ; toutes les musiques sont creusées à 1-4 kHz sous la voix | `creux_voix`, automatique (« musique trop forte » alors que -36 était respecté) |
| **Aucune musique réclamée** | Licence claire, crédit dans la description | `Musique/INTERDITES.txt`, `Outils/musique.py` refuse les musiques réclamées |
| Pas de passage oublié sans musique | Tout silence doit être un choix | `"musiques"` de `montage_images.json` |
| Une musique trop courte | Elle est relancée en fondu enchaîné juste avant son silence de fin (une simple répétition laissait un trou de 5 s) | automatique (`fin_utile`) |
| **Pas de bout de voix isolé** | Un son de moins de 0,35 s entre deux silences (marmonnement de l'IA, mot coupé) s'entend comme une « coupure bizarre » | `nettoyer` les retire, `verifier` les signale ; bords de chaque voix en fondu |
| Baisse de la musique sous la voix | Douce (ratio 3, relâche 0,7 s) : sinon la musique « pompe » à chaque pause | `montage` |
| Silence au début d'une musique | Sauté automatiquement | `debut_utile` |
| Pas de fond sonore continu | Feu seulement à 2 ou 3 moments calmes, très bas | `"feu_passages"`, volume 0,12 à 0,15 |
| **Peu de bruitages, jamais bizarres** | 1 ou 2 par vidéo, dans le doute aucun | `"bruitages"` |
| Silence entre deux passages | 0,7 s minimum | `"ecarts_min"` pour plus |
| Volume final | -14 LUFS, pics sous -1 dB | `montage`, puis `finir` mesure et corrige le volume (un rendu court sortait à -12,7) |

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

## Pas de trou de son entre deux scènes
Une musique qui s'arrête pile au changement de scène, avant que la suivante ne démarre en fondu, laisse 0,3 à 1 s de **silence total** : on l'entend comme une coupure, et le moindre bruit de la voix ressort. `plan_montage.py` fait maintenant un **fondu enchaîné** (`CHEVAUCHE`, 1,5 s) entre deux musiques qui se suivent, et la musique doit commencer **dès le bloc 1** (jamais d'intro sans musique). Si un morceau a lui-même un silence, le faire commencer plus loin (`"debut": 17.8` dans `"musiques"`).
`verifier.py` signale tout **trou de son** (> 0,25 s sous -55 dB) et tout **bruit avant ou après une phrase** : une vidéo avec un de ces points n'est jamais montrée.
