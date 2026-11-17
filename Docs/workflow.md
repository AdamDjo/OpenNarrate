# Le workflow : d'un sujet à une vidéo racontée

Tu donnes **un sujet**. Claude fait tout le reste et s'arrête seulement **3 fois** pour ta validation (texte, planche et voix, vidéo), puis une dernière fois avant de publier.
Compter environ 2 h de calcul pour le PC sans animation (2 h de plus avec) et 20 à 30 min pour toi. **Les animations sont optionnelles** : par défaut, la vidéo est montée avec les images fixes et un zoom lent.

Toutes les commandes passent par `Outils/fabriquer.py`, depuis la racine du dossier :

```
python Outils/fabriquer.py <étape> <projet>
```

| # | Étape | Qui | Commande | Ce qui sort |
|---|---|---|---|---|
| 0 | Créer le projet | Claude | `nouveau AAAA-MM-JJ_sujet` | `Episodes/<projet>/` copié de `Modeles/projet/` |
| 1 | Recherche | Claude | — (voir `recherche.md`) | `sources.md` : faits numérotés, 2 sources chacun |
| 2 | Script | Claude | — (voir `ecriture.md`) | `script.md` |
| ✅ | **Validation 1 : le texte** | **Toi** | | Tu lis, tu corriges. Rien n'est généré avant |
| 3 | Blocs | Claude | `blocs` | `blocs.json` : le script découpé plan par plan |
| 4 | Images clés (avec l'intro, le titre et la fin) et test de voix (30 s) | Claude + Codex | `voix --seulement b02` | Planche d'images + un extrait |
| ✅ | **Validation 2 : la planche et la voix** | **Toi** | | |
| 5 | Toute la voix | Claude | `voix` puis `choisir` puis `refaire` tant qu'il reste de vraies alertes, puis `nettoyer` | `voix/narration/bNN.wav` |
| 6 | Toutes les autres images, et le thème des titres propre à cette vidéo | Claude + Codex | — | `images/`, `"theme_titres"` |
| 7 | Montage | Claude | `plan` puis `montage` | `A_publier/<projet>_v1.mp4` |
| 8 | Finalisation et contrôle automatique | Claude | `finir` puis `verifier` | Aperçu 720p + rapport |
| ✅ | **Validation 3 : la vidéo (images fixes)** | **Toi** | | Tes retours, regroupés avant de relancer un montage |
| Option | Animations : **Claude te pose toujours la question après la validation 3**, elles ne se font que si tu dis oui | Claude | `animer` puis `plan`, `montage` | `anim/clips/` : environ 2 h de calcul en plus. Sans clip, le montage utilise les images fixes |
| 9 | Miniature, textes, Shorts | Claude | skill `storytelling-images`, `Modeles/checklist_publication.md` | Tout prêt à poster |
| ✅ | **Une seule confirmation pour publier** | **Toi** | | Rien n'est publié sans ce « oui » |

## Le mode auto (au choix)
Écrire « mode auto » dans la demande : tu valides seulement le texte, Claude contrôle seul les images et la voix, et tu reçois la vidéo vérifiée. Rien n'est jamais publié sans ta confirmation. À éviter pour un nouveau narrateur ou une nouvelle voix.

## Le dossier d'un projet

| Fichier | Rôle | Écrit par |
|---|---|---|
| `sources.md` | Faits vérifiés, liens, crédits des musiques et polices | Claude |
| `script.md` | **La référence du texte**, avec les plans et les émotions | Claude |
| `blocs.json` | Le script découpé (généré depuis `script.md`) | `blocs` |
| `montage_images.json` | **Tous les réglages de cette vidéo** : narrateur, images par bloc, musiques, titres, animations, écran de fin | Claude |
| `anim/episode.json` | Les plans à animer et leurs prompts | Claude |
| `episode.json` | Le montage calculé (ne pas retoucher à la main) | `plan` |
| `A_REPRENDRE.md` | Où on en est, si une session s'arrête | Claude |

## Règles de sécurité (apprises à nos dépens)
- **Ne rien déplacer ni modifier dans un projet ou dans `Outils/` pendant un montage** : il lit les fichiers à la toute fin (rendu perdu le 8 nov.).
- Si le texte change : corriger `script.md`, relancer `blocs`, puis ne régénérer **que les blocs concernés** (`voix --seulement b05,b09`). Avant de régénérer un bloc, enlever ses anciennes prises.
- Après `choisir`, toujours relancer `nettoyer` sur les mêmes blocs.
- Une retouche coûte un rendu complet de 30 à 40 min : **regrouper les retours** avant de relancer.
- Montrer un aperçu (planche d'images, extrait de voix, planche des textes) avant toute étape longue.

## Temps observés (RTX 4070 Ti 12 Go, vidéo de 15 min)
| Étape | Temps |
|---|---|
| Voix complète | ≈ 1 h |
| Une image (Codex) | ≈ 1 min 30 à 3 min |
| Une animation (Wan, `--qualite`) | ≈ 13 min (8 plans ≈ 1 h 45) |
| Montage | ≈ 30 à 40 min |
