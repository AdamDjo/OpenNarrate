---
name: storytelling-images
description: Crée les images d'une vidéo racontée avec Codex/ChatGPT - illustrations 16:9, portraits de narrateurs, cartes sur parchemin, miniatures, avatar, bannière - dans le style de l'univers du sujet. À utiliser pour toute image de la chaîne ou d'un projet (nouvelle image, correction d'une image, nouveau narrateur, miniature).
---

# Images d'une vidéo racontée

Réponds en français simple. Lis `Docs/images.md`. Pendant une vidéo, les images sont validées **toutes ensemble sur une planche**. Hors vidéo (avatar, bannière, narrateur) : une image à la fois.

## Avant de générer
- **Chercher une vraie référence de l'univers** (capture, page du wiki) et la passer en `-i` : les descriptions en mots seules ont souvent échoué.
- Préciser le style dans chaque prompt, et ce qu'on refuse (par exemple « not photorealistic, not Disney »).
- Respecter les proportions de l'univers. Vérifier les mains et les visages en zoomant avant de montrer.
- Pas de logo officiel. Pas de texte dans l'image : les textes viennent du montage.
- **Narrateur** : toujours `Narrateurs/<nom>/portrait.png` en `-i`, pour garder le même visage. **Jamais le portrait d'un autre narrateur**, même pour le style : son décor reviendrait dans l'image.
- **Intro, titre et fin** : inventés pour chaque vidéo, avec le narrateur grand et bien visible dans l'intro (`Docs/images.md`).
- **Gros plan d'une main** : compter les doigts et vérifier que la peau a la couleur du personnage.
- **Continuité d'un lieu** : générer la 1ʳᵉ image, puis « Edit the FIRST attached image: keep EXACTLY… ONLY ONE CHANGE: … ».

## Générer
Dans le terminal de l'utilisateur (`run_in_terminal`, onglet réutilisable), jamais dans le sandbox. Pour plusieurs images, écrire un `.ps1` dans le projet, sur le modèle de `Modeles/generer_images.ps1`.
- Prompt sur **une seule ligne**, **avant** les `-i`, sans le mot « using ».
- « wide 16:9 landscape format » (vidéo) ou « vertical 9:16 » (Short).
- L'image est dans `$env:CODEX_HOME\generated_images\<session id>\`. Prendre celle de **sa** session.

## Narrateur (une fois)
Portrait de buste dans un lieu qui appartient à son sujet, jamais le décor d'un autre narrateur. Ranger dans `Narrateurs/<nom>/` : `portrait.png`, `fiche.md`, `reference.wav`.

## Formats
| Image | Taille | Remarque |
|---|---|---|
| Vidéo | 1920×1080 minimum | 16:9 |
| Avatar | carré ≥ 800×800, < 1 Mo | Lisible en tout petit |
| Bannière YouTube | 2560×1440, < 6 Mo | Zone sûre centrale 1546×423 |
| Miniature | 1280×720, < 2 Mo | Sujet fort, 3 mots maximum, 2 versions à tester |
| Miniature de Short | 1080×1920 | Un visage ou un lieu |
