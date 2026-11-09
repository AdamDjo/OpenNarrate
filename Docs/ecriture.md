# Écrire le script

Le but : **raconter une histoire de façon fluide, sans bla-bla**, pour que le spectateur oublie comment la vidéo est fabriquée.
10 min ≈ 1 300 mots.

## Le narrateur raconte, il ne demande rien
- Il dit « je » pour ses **souvenirs** : c'est ce qui le rend crédible (« Je l'ai vu ramasser de la poussière… »).
- Il s'adresse au spectateur **une fois au début** et **une fois à la fin**. Jamais entre les deux.
- Interdit : « retiens bien ça », « souviens-toi », « il faut que tu saches », « va voir par toi-même », « à toi maintenant », « dis-lui que… », répéter un surnom (« voyageur ») à chaque passage.
- **Pas de blagues** ajoutées pour faire vivre le texte : elles ont toutes été retirées. Une ironie née de l'histoire peut rester (« Les preuves sont arrivées. En marchant. »).

## L'histoire avant le guide
- Une suite d'événements dans l'ordre : ce qui s'est passé, puis ce qui en a découlé. Chaque passage répond à « et alors ? ».
- **Pas de consignes ni de mode d'emploi.** On le raconte comme un fait (« On raconte que… ») ou on l'enlève.
- **Un nouveau nom seulement s'il sert la suite.** Sinon on dit « un mage », « un village ». Chaque nom gardé est expliqué en une demi-phrase, pour qu'un non-initié suive.
- Un élément planté plus tôt est rappelé clairement quand il revient, sans ordre au spectateur (« Ces égouts par lesquels je me suis enfui… »).

## Le style : relier les phrases
Les phrases hachées sont la signature de l'écriture par IA, et ce que la voix de synthèse dit le plus mal.

| À éviter | À faire |
|---|---|
| « Les magiciens. On les surveillait. On les craignait. Alors, un jour, ils sont partis. » | « On surveillait les magiciens et on les craignait, si bien qu'un jour, ils ont pris la route. » |
| Mots isolés : « Trop de magie. », « Toutes. », « Violet. Opaque. » | Dans la phrase : « un immense dôme violet, opaque » |
| Question suivie de sa réponse : « Pourquoi ? Certains disent… » | « Certains disent que… » |
| « Ce n'était plus une ville. C'était une plaie. » | « Il ne restait de la ville qu'une plaie ouverte. » |
| Points de suspension partout | Rares, pour une vraie hésitation |

Garder quelques phrases très courtes pour les chocs, là où elles frappent vraiment.

## La structure
| Moment | Contenu |
|---|---|
| **Ouverture (moins de 30 s)** | Le narrateur invite à s'asseoir, dit le sujet et qui il est. Puis le fait qui accroche. Pas de blague |
| **Titre** | Le **sujet** en grand, pas le nom de la chaîne |
| **4 à 6 chapitres** | Dans l'ordre du temps, avec un titre court qui donne envie |
| **Ce que peu de gens savent** | Le plus étrange, raconté comme la suite de l'histoire |
| **Fin** | Une dernière image forte, une phrase d'abonnement dite par le narrateur, son mot de la fin, un écran de 15 s |

## Le format de `script.md`
```
## 1. Titre du chapitre

🌫️ VISION — Description de l'image.

> {confidence} Texte dit par le narrateur. [#3]
>
> {peur} Une ligne vide après « > » marque une longue pause.
```
- Une ligne qui commence par 🔥 FEU, 🌫️ VISION, 🌍 MONDE ou 📜 CARNET ouvre un plan.
- `[#3]` renvoie au fait n°3 de `sources.md`.
- Émotions possibles : `{neutre}` `{confidence}` `{triste}` `{peur}` `{emerveillement}` `{colere}` `{amuse}` `{joie}`. Elles valent jusqu'à la suivante.
- Mots étrangers gardés tels quels, avec l'accent français : ajouter leur son dans `"prononciation"` de `montage_images.json`.
- Toujours finir une phrase par un point : voir `voix.md`.
