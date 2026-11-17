# Démarrage rapide d’OpenNarrate

[English](quickstart.en.md) · [README français](../README.fr.md)

## Installation et test

Installez Python 3.12 et FFmpeg. Copiez `config.exemple.json` vers `config.json` et renseignez les chemins de votre PC. Depuis la racine du dépôt, vérifiez la configuration.

```powershell
python Outils/fabriquer.py --help --ui-language fr
python Outils/fabriquer.py doctor
```

Pour essayer le montage sur CPU, installez NumPy et lancez le test. Il génère un projet temporaire avec des aplats de couleur et des sons de test, vérifie la vidéo et contrôle que seuls les plans modifiés sont recalculés.

```powershell
python -m pip install numpy
python Tests/smoke_render.py
```

## Créer un épisode

Pour piloter la production en conversation, lancez `claude --agent videomaker` depuis la racine du dépôt. Donnez à [l’agent](../.claude/agents/videomaker.md) le sujet et la langue de narration. Les étapes suivantes permettent de lancer les commandes à la main.

1. Créez un projet avec `python Outils/fabriquer.py nouveau 2026-12-01_mon-sujet`.
2. Documentez les faits dans `sources.md` et écrivez la narration dans `script.md` en suivant les marqueurs du modèle.
3. Ajoutez vos images et indiquez les alias de chaque bloc dans `montage_images.json`. Utilisez `"langue": "fr"` pour une narration française.
4. Choisissez votre narrateur ou réglez `"narrateur": "default"` pour la voix intégrée de Chatterbox. Écoutez un extrait avec `voix mon-sujet --seulement b02` avant de produire toute la voix.

```powershell
python Outils/fabriquer.py blocs mon-sujet
python Outils/fabriquer.py voix mon-sujet
python Outils/fabriquer.py choisir mon-sujet
python Outils/fabriquer.py nettoyer mon-sujet
python Outils/fabriquer.py check mon-sujet
python Outils/fabriquer.py plan mon-sujet
python Outils/fabriquer.py montage mon-sujet
python Outils/fabriquer.py finir mon-sujet
python Outils/fabriquer.py verifier mon-sujet --report
```

Regardez l’aperçu et lisez le rapport `verification.json` avant de publier. Pour préparer un extrait vertical, suivez le [guide des Shorts](shorts.md).
