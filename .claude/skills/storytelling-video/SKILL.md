---
name: storytelling-video
description: Fabrique de A à Z une vidéo racontée de 10 à 20 min (16:9) sur un sujet donné - recherche vérifiée, script, voix du narrateur, images, montage, contrôle, animations en option - en suivant le workflow du dossier. À utiliser dès que l'utilisateur donne un sujet, dit « fais la vidéo sur … », « prochaine vidéo », « on attaque … », ou veut reprendre une vidéo en cours.
---

# Fabriquer une vidéo racontée

Réponds en français simple. Tu es le réalisateur. Lis `Docs/workflow.md`, puis le document de chaque étape **au moment où tu l'attaques**.
Si `Episodes/<projet>/A_REPRENDRE.md` existe, reprends là où ça s'est arrêté.
Les commandes : `python Outils/fabriquer.py <étape> <projet>`.

## Le déroulé
1. **Projet** : `nouveau AAAA-MM-JJ_sujet` (date de publication visée). **Chaque sujet a son propre narrateur** : proposer un personnage qui appartient à ce sujet, puis le créer (portrait avec `storytelling-images`, voix avec `Docs/voix.md`, à partir d'une référence dont l'utilisateur a les droits).
2. **Recherche** (`Docs/recherche.md`) : `sources.md`, 15 à 25 faits à 2 sources, et l'angle propre à notre vidéo.
3. **Script** (`Docs/ecriture.md`) : `script.md`. Relis-le avec la grille ci-dessous avant de le montrer.
4. **Validation 1** : le texte complet, facile à lire. `wrap_up` « Oui, lance » / « Modifier ». Rien n'est généré avant.
5. `blocs`, images clés (`storytelling-images`) **avec l'intro, le titre et la fin**, une planche, et 30 s de voix (`voix --seulement b02`, `choisir --seulement b02`).
6. **Validation 2** : la planche + l'extrait.
7. Voix complète (`Docs/voix.md`) : `voix`, `choisir`, `refaire` pour les vraies alertes, `nettoyer`.
8. Toutes les autres images. **L'intro, le titre et la fin sont inventés pour cette vidéo** : on voit bien le narrateur dans l'intro, et on ne reprend jamais le cadrage ou le décor d'une autre vidéo (`Docs/images.md`). **Pas d'animation par défaut** : `animer` seulement si l'utilisateur le demande, après la validation 3, avec contrôle de chaque clip en planche.
9. Remplir `montage_images.json` avec un **`theme_titres` propre à ce sujet** (police, couleurs : `Docs/son_et_montage.md`), montrer **l'aperçu des textes** sur les vrais fonds, puis `plan` et `montage` en arrière-plan.
10. `finir`, puis `verifier`, et corriger ce qu'il signale. Envoyer l'aperçu 720p **de la vidéo sans animation** : c'est elle qu'on valide.
11. **Validation 3** : dire aussi ce qu'on n'a pas pu vérifier (on ne peut pas écouter) et où écouter en priorité. Regrouper les retours avant de relancer.
12. Après accord : miniature, textes, Shorts, puis `Modeles/checklist_publication.md`. Mettre `A_REPRENDRE.md` à jour à chaque grande étape.

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
