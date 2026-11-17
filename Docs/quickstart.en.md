# OpenNarrate quickstart

[Français](quickstart.fr.md) · [English README](../README.md)

OpenNarrate turns a researched script into a narrated video. You can bring your own illustrations and narration or generate them through the production workflow.

## Check your installation

Install Python 3.12 and FFmpeg. Copy `config.exemple.json` to `config.json` and set the executable paths for your computer. Run the following commands from the repository root.

```powershell
python Outils/fabriquer.py --help
python Outils/fabriquer.py doctor
```

The `python_outils` environment runs the planning and transcription tools. The `python_voix` environment runs Chatterbox and PyTorch. The full production workflow was developed on Windows with an NVIDIA GPU. Image generation uses Codex when you choose to generate new illustrations.

### Test rendering first

With FFmpeg and NumPy installed, run:

```powershell
python Tests/smoke_render.py
```

This creates a temporary episode inside OpenNarrate using test tones and color cards. It checks the inputs, verifies the rendered media, confirms that an unchanged render reuses both shots, then replaces one image and checks that only that shot is rebuilt. It removes the temporary project and media at the end. It requires no voice model, image generator or GPU.

## Make an episode

To use the [`videomaker` agent](../.claude/agents/videomaker.md), run `claude --agent videomaker` from the repository root and give it a topic and your narration language. To run the steps yourself, follow the commands below.

1. Run `python Outils/fabriquer.py new 2026-12-01_my-topic` for the English template. Add `--language fr` for the French template.
2. Fill in `sources.md` and `script.md`. Keep the visual markers in the script template and put spoken text on lines beginning with `>`.
3. Add images to the project and map them to block numbers in `montage_images.json`. Set `langue` to `en` for English narration or `fr` for French.
4. Set `narrateur` to `default` for Chatterbox's built-in voice, or use your narrator's folder name under `Narrateurs/`. Review a sample with `voice my-topic --only b02` before generating the rest.
5. Check your inputs, plan the timeline and render. Review the preview before sharing or publishing.

```powershell
python Outils/fabriquer.py blocks my-topic
python Outils/fabriquer.py voice my-topic
python Outils/fabriquer.py select my-topic
python Outils/fabriquer.py clean my-topic
python Outils/fabriquer.py check my-topic
python Outils/fabriquer.py plan my-topic
python Outils/fabriquer.py render my-topic
python Outils/fabriquer.py finish my-topic
python Outils/fabriquer.py verify my-topic --report
```

For a targeted voice correction, run `voice`, `select` and `clean` with `--only b02` or a comma-separated block list. Planning a render creates a new timeline and output name. The renderer can reuse unchanged still-image shots.

The optional JSON verification report is saved in the project as `verification.json`. When chapter titles are present after the opening, the renderer writes a `.chapters.txt` file beside the MP4.

For a vertical excerpt, fill in `shorts.json` and run `python Outils/short.py my-topic`. Changes to source images, narration, music or the render plan refresh the intermediate video automatically. Text-only changes can reuse the intermediate video.
