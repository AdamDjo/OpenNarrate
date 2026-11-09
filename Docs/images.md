# Images et animations

## Les 4 couches
| Couche | Quand | Style |
|---|---|---|
| 🔥 **Feu** | Le narrateur à l'écran | Style de l'univers, lumière chaude. Une scène par narrateur, donc nouvelle à chaque sujet |
| 🌫️ **Vision** | Le passé, ce qu'il raconte | Style de l'univers, bords qui se perdent dans la fumée |
| 🌍 **Monde** | Ce qui existe aujourd'hui | Rendu le plus proche de la source |
| 📜 **Carnet** | Géographie, noms, explications | Encre sur parchemin, sans texte |

Le **style de l'univers est non négociable** : le préciser dans chaque prompt, dire ce qu'on refuse, et donner une vraie référence en image.

## Générer avec Codex (skill `storytelling-images`)
- À lancer dans le terminal de l'utilisateur, jamais dans le sandbox.
- Prompt **sur une seule ligne, avant les `-i`** : `codex.cmd exec --skip-git-repo-check "<prompt>" -i <ref>`.
- Prendre l'image dans le dossier de **sa** session (`session id` dans la sortie), pas la plus récente.
- Corriger une image : « Edit the FIRST attached image, keep EXACTLY… ONLY ONE CHANGE: … », avec l'image d'origine en `-i`. Résultat très fidèle.
- Comparer avant/après en zoom sur le détail changé.
- Un lieu qui ne doit pas flotter, un visage à garder : le dire explicitement, à chaque image.

## L'intro, le titre et la fin
Ce sont les images les plus vues : on les **invente pour chaque vidéo**, jamais de recette répétée.
- **Intro** : on voit bien le narrateur, grand dans l'image (jamais perdu dans un plan large), dans un lieu de son sujet, avec une action liée à ce qu'il dit.
- **Titre** : une image forte, avec de la place vide là où le titre s'affiche. Dans `montage_images.json`, c'est toujours l'alias `F3`.
- **Fin** : une dernière image qui raconte quelque chose, avec de la place pour « Abonne-toi ».
- Ne jamais passer le portrait d'un autre narrateur en `-i`, même pour le style. Varier l'angle, la distance, l'heure, la lumière d'une vidéo à l'autre.

## Les animations (optionnelles, Wan 2.2 par ComfyUI)
Seulement si l'utilisateur les demande : des images fixes avec un zoom lent suffisent souvent.
On n'anime pas tout : **environ 8 plans** (≈ 13 min chacun). Le reste a un zoom lent et fluide.

| Règle | Pourquoi |
|---|---|
| Un seul mouvement simple par plan | Les mouvements complexes déforment |
| **Personnage qui ne fait rien = mains baissées, posture naturelle** | Un personnage figé la main tendue paraît faux |
| Pour les plans qui durent : **seule l'ambiance bouge** (feu, ciel, nuages, lumières, herbe) | C'est beau, et sans risque pour le visage |
| Image de fin = image de début pour les boucles | Boucle sans saut, adoucie au montage |
| Toujours : « The camera is locked and perfectly still. » | Évite les dérives |
| Contrôler chaque clip en planche (`fps=1.5,tile=4x2`) | Avant le montage, pas après |

Les plans à animer se décrivent dans `anim/episode.json`, leur usage dans `"animations"` de `montage_images.json` : `{"F1": {"clip": "boucle_ambiance", "boucle": true}}`. Sans animation, laisser `{}`.
ComfyUI doit tourner avant `animer`. `animer` refait tous les plans du fichier : après un arrêt, relancer seulement ceux qui manquent, un par un (`animer <projet> <plan>`).

## Planche de validation
Toutes les images clés sur une seule planche : mains, visages, cohérence, lieux. Une seule question à l'utilisateur.
