# OpenNarrate

Un sujet donne une vidéo racontée. Réponds dans la langue de l'utilisateur, simplement.

## Comment on travaille
- L'utilisateur demande de créer ou de reprendre une vidéo : utilise l'agent **`videomaker`** (`.claude/agents/videomaker.md`), qui suit `Docs/workflow.md`.
- Confirme la langue de narration avant d'écrire si elle n'est pas indiquée. La valeur `langue` de `montage_images.json` fait foi pour l'épisode. Note les validations et la prochaine action dans `A_REPRENDRE.md`.
- **3 validations** : le texte (avant toute génération), la planche d'images avec un test de voix, la vidéo montée avec les images fixes. **Les animations sont optionnelles**, seulement sur demande. Puis une seule confirmation pour publier. « Mode auto », uniquement si l'utilisateur l'écrit.
- Montre un aperçu avant toute étape longue. Regroupe les retours avant de relancer un montage (30 à 40 min).
- **Ne déplace ni ne modifie rien dans `Outils/` ou le projet pendant un montage.**

## Règles
- Le narrateur **raconte** : pas de consignes au spectateur, pas de blagues ajoutées, phrases reliées (`Docs/ecriture.md`).
- **La musique ne dépasse jamais la voix.** Pas de bruitage bizarre (`Docs/son_et_montage.md`).
- Chaque sujet a son propre narrateur, avec son portrait, sa voix et son décor. Chaque fait a 2 sources.
- Chaque vidéo a sa propre intro, sa propre fin et son propre thème de titres (`Docs/images.md`, `Docs/son_et_montage.md`).
- On ne copie aucune autre chaîne.
- L'IA est toujours déclarée sur les plateformes. Rien n'est publié sans l'accord de l'utilisateur.

## Partage
Ne jamais ajouter au dépôt : voix de référence, musiques, images de projets, vidéos ni `config.json` (`Docs/droits.md`). Exceptions : l'exemple libre de `Exemples/pyramides/`, la vidéo explicative approuvée dans `Exemples/walkthrough/` et les captures de `Docs/assets/`.
