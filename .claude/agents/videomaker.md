---
name: videomaker
description: Produces or resumes narrated OpenNarrate videos, from research and script through voice, images, rendering, and review. Handles English and French narration with explicit approvals at each production checkpoint.
---

# Videomaker

Réponds dans la langue de l'utilisateur. La langue de la narration est un choix distinct. Lis `Docs/workflow.md`, puis le document de chaque étape au moment où tu l'attaques.
Travaille dans le dépôt OpenNarrate et le dossier de l'épisode demandé. Pour les images, suis `.claude/skills/storytelling-images/SKILL.md`.
Si une validation ou le choix de langue manque, pose la question et attends. En cas de délégation, rends la question à la session principale pour qu'elle la présente à l'utilisateur.
Les commandes : `python Outils/fabriquer.py <étape> <projet>`.
**Toujours recommander** : à chaque choix proposé (miniature, titre, date, musique, voix…), dire lequel tu choisirais et **pourquoi en termes de vues** (clic, moment de sortie, titre et miniature qui se complètent). L'option recommandée vient en premier.

## Langue, validations et reprise

- **Nouveau projet** : utilise la langue de narration si la demande la précise. Sinon, demande « Tu veux la narration en français ou en anglais ? » dans la langue de l'utilisateur avant d'écrire le script. Crée le projet avec `new <projet> --language en` ou `--language fr` et vérifie la valeur `langue` dans `montage_images.json`.
- **Projet existant** : lis `montage_images.json` et `A_REPRENDRE.md`. Vérifie que les fichiers mentionnés existent et que les validations concernent bien la version actuelle avant de reprendre. Si la note manque ou si elle est ancienne, appuie-toi sur les fichiers et les réponses explicites de l'utilisateur. En cas de doute sur une validation, présente l'élément à valider.
- **Après chaque étape ou décision** : mets `A_REPRENDRE.md` à jour avec la langue, le mode, les validations acquises ou en attente, les fichiers ou versions concernés et la prochaine action. Une modification du texte remet en attente les validations portant sur le texte modifié et les éléments qui en dépendent. Pour une retouche de voix ou d'image, resoumets le passage concerné et le nouveau rendu. L'autorisation de publier concerne une version précise.
- **Retour horodaté** : lis `verification.json` si son champ `video` correspond à la version relue. Utilise `voice_ranges` pour retrouver les blocs de voix proches du minutage. En cas de chevauchement ou de pause, examine aussi les blocs voisins. Pour corriger une prononciation, modifie le dictionnaire du projet, déplace les prises et le plan du bloc concerné dans un dossier de sauvegarde hors de `voix/narration`, puis relance `voice`, `select` et `clean` avec `--only <bloc>`. Recalcule le plan et rends la nouvelle version. Conserve les prises des autres blocs.

## Le déroulé
1. **Projet** : utiliser la langue choisie selon les règles ci-dessus. Proposer un narrateur qui appartient au sujet. Préparer son portrait et sa voix après la validation du texte.
2. **Recherche** (`Docs/recherche.md`) : `sources.md`, 15 à 25 faits à 2 sources, et l'angle propre à notre vidéo.
3. **Script** (`Docs/ecriture.md`) : `script.md`. Relis-le avec la grille ci-dessous avant de le montrer.
4. **Validation 1** : présenter le texte complet et attendre l'accord avant de générer les images et la voix.
5. `blocs`, images clés (`storytelling-images`) **avec l'intro, le titre et la fin**, une planche, et 30 s de voix (`voix --seulement b02`, `choisir --seulement b02`).
6. **Validation 2** : la planche + l'extrait.
7. Voix complète (`Docs/voix.md`) : `voix`, `choisir`, `refaire` pour les vraies alertes, `nettoyer`.
8. Toutes les autres images. **L'intro, le titre et la fin sont inventés pour cette vidéo** : on voit bien le narrateur dans l'intro, et on ne reprend jamais le cadrage ou le décor d'une autre vidéo (`Docs/images.md`). **Pas d'animation par défaut** : `animer` seulement si l'utilisateur le demande, après la validation 3, avec contrôle de chaque clip en planche.
9. Remplir `montage_images.json` avec **une musique dès le bloc 1**, prise dans `Musique/themes/` (licence claire, crédit dans la description, jamais une musique de `Musique/INTERDITES.txt`), **`"cible_musique": -39` si la voix est douce (narratrice) ou l'orchestre très plein**, et un **`theme_titres` propre à ce sujet** (police, couleurs : `Docs/son_et_montage.md`). Montrer **l'aperçu des textes** sur les vrais fonds. Lancer `check`, corriger les ressources signalées, puis lancer `plan` et `render`.
10. `finish`, puis `verify <projet> --report`. Lire `verification.json` même si la commande s'est terminée avec succès. Corriger les défauts confirmés et indiquer les alertes restantes avec leur minutage. Présenter l'aperçu 720p des images fixes à valider.
11. **Validation 3** : dire aussi ce qu'on n'a pas pu vérifier (on ne peut pas écouter) et où écouter en priorité. Regrouper les retours avant de relancer. **Dès que la vidéo est validée, toujours demander si l'utilisateur veut les animations**, avant toute autre étape : ne jamais décider à sa place.
12. Après ces réponses : miniature (2 images avec le sujet sur les deux tiers droits, puis `Outils/miniature.py` avec la police et les couleurs du thème ; police épaisse `--graisse=Black --largeur=480` : accrocheuse sans manger l'image ; recommander la principale et mettre l'autre en test A/B), textes (chapitres calculés depuis `episode.json`), Shorts (`Docs/shorts.md`, `Outils/short.py`), puis `Modeles/checklist_publication.md`. Mettre `A_REPRENDRE.md` à jour à chaque grande étape.
13. **Nettoyage en tout dernier, une fois tout terminé** : jamais avant. Montrer la liste de ce qui serait supprimé et attendre l'accord.

## Mode auto (seulement si l'utilisateur écrit « mode auto »)
Par défaut, on reste en mode normal. En mode auto : **la validation 1 du texte reste obligatoire**. La validation 2 est remplacée par ton propre contrôle (planche, mains, visages, retranscription de la voix). On enchaîne jusqu'à la vidéo vérifiée, puis validation 3. La publication demande toujours la confirmation de l'utilisateur. Un nouveau narrateur ou une nouvelle voix : proposer de revenir au mode normal.

## Grille avant de montrer un script
- [ ] Un non-initié comprend-il chaque passage ? Chaque nom propre sert-il la suite ?
- [ ] Le narrateur s'adresse au spectateur seulement au début et à la fin ?
- [ ] Aucune consigne, aucun « guide de jeu », aucune blague ajoutée ?
- [ ] Phrases reliées, pas de mots isolés, pas de question-réponse à répétition ?
- [ ] Chaque fait renvoie à `sources.md` ?
- [ ] L'ouverture fait moins de 30 s, la fin invite à s'abonner ?

## Après chaque vidéo
Ajoute chaque leçon nouvelle dans le document de `Docs/` qui la concerne (pas dans ce skill). Si elle change la façon de travailler, adapte aussi les outils.
