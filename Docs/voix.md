# La voix du narrateur

Outil : **Chatterbox multilingue** (local, gratuit, licence MIT). Contrôle par **faster-whisper**.

## Le narrateur
**Chaque sujet a son propre narrateur**, un personnage qui lui appartient. `Narrateurs/<nom>/` contient `reference.wav` (8 à 20 s d'une seule personne, sans musique, **dans la langue de la vidéo**, sinon l'accent passe, et dont vous avez le droit d'utiliser la voix), `portrait.png` et `fiche.md`.
Le narrateur et la langue se règlent dans `montage_images.json` : `"narrateur": "<nom>"`, `"langue": "fr"`.

## La méthode (à refaire pour chaque narrateur)
1. Préparer la référence (environ 9 s, 24 kHz, mono, -23 LUFS) :
   `ffmpeg -i replique.ogg -ac 1 -ar 24000 -af loudnorm=I=-23:TP=-3 Narrateurs/<nom>/reference.wav`
2. Si plusieurs répliques sont fournies, tester chacune sur le même paragraphe et faire choisir à l'oreille.
3. Faire écouter 30 s avant le reste : le rythme, les émotions, les mots étrangers.
4. Sont déjà réglés dans les outils : 3 prises, morceaux d'au moins 12 mots, ralenti 0,88, plafond de débit, émotions `{…}`, nettoyage des respirations.
5. Les réglages d'émotion ont été faits sur une voix d'homme âgé : réécouter avec une autre voix et les ajuster si besoin (`EMOTIONS` dans `voix_narrateur.py`).

## La chaîne
| Commande | Ce qu'elle fait |
|---|---|
| `voix <projet>` | 3 prises par morceau de texte. Option `--seulement b05,b09` |
| `choisir <projet>` | Réécoute chaque prise, garde la meilleure, assemble avec pauses, ralenti et émotions. Option `--seulement` |
| `refaire <projet>` | 3 prises de plus pour les morceaux en alerte, puis refaire `choisir` |
| `nettoyer <projet>` | Retire respirations et petits bruits entre les mots. À refaire après chaque `choisir` |

## Lire les alertes
L'outil de vérification comprend mal les noms propres : un nom inventé mal retranscrit n'est pas une erreur de voix. **À regarder vraiment** :
- des mots ordinaires changés (« qui s'accueille » au lieu de « qu'ils accueillent ») ;
- un débit au-dessus de 3,6 mots/s : couper la phrase en deux dans le `plan.json` du bloc ;
- une fin inventée (« Oh ! I est… », « Assi… ») ;
- un mot inventé que l'outil entend comme un autre mot courant : c'est un vrai défaut. Tester 2 ou 3 orthographes phonétiques sur une phrase courte, garder la meilleure dans `"prononciation"`, puis enlever les anciennes prises et régénérer seulement les blocs concernés ;
- un mot qui reste raté après plusieurs essais : le **faire écouter**, ou choisir un autre mot.

## Ce qu'on a appris
| Problème | Solution |
|---|---|
| Il parle trop vite | Morceaux séparés, ralenti 0,88, plafond de débit (réglés dans les outils) |
| Fin inventée, bégaiement | **Un morceau finit toujours par un point**, jamais par une virgule ou deux-points. Au moins 5 mots par morceau |
| Mot étranger massacré | Écrire son son dans `"prononciation"` de `montage_images.json`, utilisé seulement à la génération |
| Accent étranger | Référence dans la langue de la vidéo |
| Voix artificielle sur les passages hachés | Relier les phrases (`ecriture.md`) |
| Respirations audibles | `nettoyer`, qui protège les fins de mots |
| Voix qui en recouvre une autre | `plan` garantit 0,7 s de silence entre deux blocs (`"ecarts_min"` pour plus) |
| Voix de référence râpeuse qui grésille après génération | Garder la référence d'origine et filtrer seulement le résultat : `"filtre_voix": "adeclick,highshelf=f=4000:g=-9,lowpass=f=10000"` dans `montage_images.json`, appliqué par `nettoyer`. Mesurer d'abord (aigus 4-8 kHz, clics par seconde) par rapport à une voix validée, puis faire choisir à l'oreille. Adoucir la référence ou débruiter a donné une voix « éclatée » |

## Marmonnements avant et après une phrase
La voix de synthèse ajoute parfois un « aa aa » ou un bruit juste après le dernier mot d'une prise (plus rarement avant le premier). Le nettoyage ne les enlève pas, car ils ressemblent à de la voix. `voix_choisir.py` coupe donc chaque prise 0,25 s après le dernier mot entendu et commence 0,15 s avant le premier, avec un court fondu. Sur une vidéo de 7 min, cela a retiré 20 à 30 s de marmonnements.
