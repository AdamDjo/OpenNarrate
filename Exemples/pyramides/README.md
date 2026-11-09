# Exemple réel : les pyramides d'Égypte

Une courte vidéo fabriquée de bout en bout avec OpenNarrate, à partir d'une seule phrase : « Fais une vidéo sur les pyramides d'Égypte. »

| Fichier | Ce que c'est |
|---|---|
| [`apercu.mp4`](apercu.mp4) | La vidéo finale, en version légère |
| [`sources.md`](sources.md) | Les faits vérifiés, avec ce qui a été écarté |
| [`script.md`](script.md) | Le texte, les plans et les émotions |
| [`blocs.json`](blocs.json) | Le script découpé automatiquement |
| [`montage_images.json`](montage_images.json) | Tous les réglages de la vidéo |
| [`generer_images.ps1`](generer_images.ps1) | Les prompts exacts des images |

## À savoir

- **Vidéo volontairement courte** (1 min 09) : la méthode vise des vidéos de 10 à 20 minutes, cet exemple va à l'essentiel.
- **Voix non écoutée par un humain au moment de la préparation** : les contrôles automatiques sont bons, avec une alerte de débit un peu rapide sur la 2ᵉ phrase.
- **Narratrice inventée** : Néfret et sa vie sont de la fiction. Les faits historiques sont dans `sources.md`.
- **Voix** : la voix intégrée de Chatterbox. Aucune personne réelle n'a été clonée.
- **Images** : générées par IA avec Codex, à partir des prompts de `generer_images.ps1`. Ce sont des illustrations, pas des reconstitutions fidèles.
- **Sans musique** : pour que tout ce dossier reste librement partageable.
- **Police** : [Cinzel](https://fonts.google.com/specimen/Cinzel), licence OFL, à télécharger soi-même.

Cette vidéo contient du contenu généré par IA : si vous la republiez, indiquez-le.

## Pour la refaire

1. Copiez les fichiers de ce dossier dans `Episodes/2026-12-01_pyramides/`.
2. Ajoutez un narrateur `nefret` dans `Narrateurs/` et la police dans `Polices/`.
3. Lancez `generer_images.ps1`, puis les commandes du [README principal](../../README.md#les-commandes) à partir de `voix`.

Les images et la voix sont générées à nouveau : elles ne seront pas identiques.
