# Les Shorts d'une vidéo

Trois Shorts verticaux par vidéo, faits **après la validation 3**, avec la voix et les images déjà validées : rien de nouveau à générer, donc rien de nouveau à valider en dehors du résultat.

## Choisir les passages
- Un passage = 1 à 3 blocs qui se suivent dans `blocs.json`, compris sans le reste de la vidéo. Viser 45 à 70 s ; jusqu'à 100 s pour une vraie petite histoire.
- **Commencer par le bloc le plus fort**, même s'il vient après dans la vidéo : les 2 premières secondes décident de tout. Exemple : le détail étonnant d'aujourd'hui d'abord, puis le souvenir qui l'explique.
- Reprendre les idées de Shorts notées à la fin de `script.md`.

## Le fichier `shorts.json` du projet
```json
{"shorts": [{"nom": "short1", "accroche": "Personne ne les a ramassés", "fin": "L'histoire complète sur la chaîne",
             "musique": "theme.mp3", "plans": [{"bloc": 26, "images": [["M26", 0.13], ["M26", 0.58]]}]}]}
```
- `images` : l'alias de `montage_images.json` et la **position du recadrage** (0 = bord gauche, 0,5 = centre, 1 = bord droit). Le cadre vertical garde un tiers de la largeur : pour viser un sujet placé à la fraction `c` de l'image, prendre `(c - 0,16) / 0,68`. Une image longue peut revenir deux fois avec deux positions.
- `accroche` : 3 à 6 mots en haut de l'écran pendant 3 s. `fin` : renvoi vers la vidéo complète.
- Avant de lancer, faire une planche des images candidates avec un quadrillage pour choisir les positions.

## Fabriquer
```
python Outils/short.py <projet> [nom_du_short]
```
(Python « python_outils »). Résultat : `A_publier/<projet>_<nom>.mp4`. Environ 3 à 5 min par Short.
Le rendu sans textes reste dans `shorts/<nom>/rendu_sans_textes.mp4`. Relance la même commande après une correction. Le rendu intermédiaire est recalculé si les images, la voix, la musique ou le plan de montage changent.
Textes réglés à l'usage : sous-titres de 3 mots au plus, taille 96 sur 1080 de large (76 était trop petit pour un téléphone), accroche 104.
L'outil recadre, fait le zoom lent, met la musique sous la voix (même calcul de volume que la vidéo), puis incruste l'accroche, **les sous-titres** (les mots du script, calés sur la voix) et le texte de fin, avec la police et les couleurs du `theme_titres` de la vidéo (sous-titres : `"police_sous_titres"` de `shorts.json`, sinon `police_phrase` de `config.json`).

## Contrôler avant de montrer
Une planche (1 image toutes les 3 s) : visages dans le cadre, sous-titres lisibles et au bon moment, accroche et fin. Puis envoyer les Shorts à l'utilisateur avec la miniature et les textes.
