"""Usage: python Outils/fabriquer.py <command> <project> [options]
  new YYYY-MM-DD_topic [--language en|fr]  Create a project from a language template
  doctor                  Check local tools (no project needed)
  check                   Validate basic render inputs
  blocks                  Split script.md into narration blocks
  voice [--only b05,b09]  Generate narration takes
  select [--only b05,b09] Review takes and assemble narration
  retry                   Generate more takes for flagged passages
  clean [--only b05,b09]  Clean assembled narration
  animate [shot]          Generate optional animated shots
  plan                    Build the render plan and pick the next version
  listen                  Render ONLY the audio (~1 min) with voice checks: listen BEFORE rendering
  render                  Render the planned video
  finish                  Limit audio peaks and export a 720p preview
  verify [--report]       Check audio and video, optionally save JSON
Project names can be abbreviated when the match is unique.
Use --help --ui-language fr to display help in French.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG, FFPROBE, PYTHON_OUTILS, PYTHON_VOIX, RACINE

sys.stdout.reconfigure(encoding="utf-8")
EPISODES, OUTILS = RACINE / "Episodes", RACINE / "Outils"
COMMANDS = {
    "new": "nouveau", "blocks": "blocs", "voice": "voix", "select": "choisir", "retry": "refaire",
    "clean": "nettoyer", "animate": "animer", "render": "montage", "listen": "ecoute", "finish": "finir", "verify": "verifier",
}
FRENCH_HELP = """Utilisation : python Outils/fabriquer.py <commande> <projet> [options]
  nouveau AAAA-MM-JJ_sujet [--language en|fr]  Crée un projet depuis le modèle
  doctor                         Vérifie les outils installés
  check                          Vérifie les ressources du montage
  blocs                          Découpe le script en blocs
  voix [--seulement b05,b09]      Génère les prises de voix
  choisir [--seulement b05,b09]   Sélectionne et assemble les prises
  refaire                        Ajoute des prises aux passages signalés
  nettoyer [--seulement b05,b09]  Nettoie la narration
  animer [plan]                  Anime les plans sélectionnés
  plan                           Calcule le plan de montage
  ecoute                         Seulement le son (~1 min) + contrôle des voix : à écouter AVANT le montage
  montage                        Produit la vidéo
  finir                          Limite les pics et crée un aperçu 720p
  verifier [--report]            Contrôle le rendu et peut écrire un rapport JSON
Le nom du projet peut être abrégé si un seul dossier correspond.
"""


def trouver(nom):
    if (EPISODES / nom).is_dir():
        return EPISODES / nom
    c = [p for p in EPISODES.iterdir() if p.is_dir() and nom in p.name and not p.name.startswith("_")]
    if len(c) != 1:
        sys.exit(f"Project not found or ambiguous: {nom} ({len(c)} matches)")
    return c[0]


def outils(script, *a):
    subprocess.run([PYTHON_OUTILS, "-I", str(OUTILS / script), *map(str, a)], check=True, cwd=RACINE)


def voix_py(script, *a):
    subprocess.run([PYTHON_VOIX, str(OUTILS / script), *map(str, a)], check=True, cwd=RACINE)


def option(args, nom):
    if nom in args:
        i = args.index(nom)
        if i + 1 == len(args) or args[i + 1].startswith("--"):
            sys.exit(f"Missing value for {nom}")
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return None


def narrateur(ep):
    return json.loads((ep / "montage_images.json").read_text(encoding="utf-8"))["narrateur"]


def video(ep):
    nom = json.loads((ep / "episode.json").read_text(encoding="utf-8"))["magique"]["nom"]
    return RACINE / "A_publier" / f"{nom}.mp4"


def version_suivante(ep):
    v = [int(m.group(1)) for f in (RACINE / "A_publier").glob(f"{ep.name}_v*.mp4") if (m := re.fullmatch(rf"{re.escape(ep.name)}_v(\d+)", f.stem))]
    return f"{ep.name}_v{max(v, default=0) + 1}"


def lufs(f):
    err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-i", str(f), "-map", "0:a", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def finir(ep):
    f = video(ep)
    tmp, apercu = f.with_name("_tmp_" + f.name), f.with_name(f.stem + "_apercu720p.mp4")
    # Le loudnorm du montage (une seule passe) sort parfois -12,7 LUFS sur une vidéo courte : on mesure et on corrige
    # le volume vers -14 LUFS (niveau YouTube) avant de limiter les pics.
    gain = round(-14.0 - lufs(f), 1)
    gain = gain if abs(gain) > 0.4 else 0.0
    if gain:
        print(f"Volume corrigé de {gain:+.1f} dB (cible -14 LUFS)")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(f), "-map", "0:v", "-c:v", "copy", "-map", "0:a", "-af",
                    f"volume={gain}dB,aresample=192000,alimiter=limit=0.84:attack=1:release=60:level=0,aresample=48000",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(f)
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(f), "-vf", "scale=1280:720", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(apercu)], check=True)
    print("Aperçu :", apercu)


def doctor():
    checks = [
        ("FFmpeg", [FFMPEG, "-version"]),
        ("FFprobe", [FFPROBE, "-version"]),
        ("Tools Python", [PYTHON_OUTILS, "-c", "import numpy, faster_whisper"]),
        ("Voice Python", [PYTHON_VOIX, "-u", "-c",
                          "import PIL, torch; print('PyTorch ready, CUDA:', torch.cuda.is_available()); import chatterbox"]),
    ]
    failed = False
    for label, command in checks:
        try:
            timeout = 120 if label == "Voice Python" else 30
            result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout)
            lines = (result.stderr if result.returncode else result.stdout).strip().splitlines()
            detail = lines[0] if label in {"FFmpeg", "FFprobe"} else (lines[-1] if lines else "")
            print(f"{label}: {'FAILED' if result.returncode else 'OK'}" + (f" ({detail})" if detail else ""))
            failed |= result.returncode != 0
        except subprocess.TimeoutExpired as exc:
            progress = (exc.stdout or b"").decode(errors="replace").strip()
            print(f"{label}: FAILED (timed out after {exc.timeout}s)" + (f"; last output: {progress}" if progress else ""))
            failed = True
        except OSError as exc:
            print(f"{label}: FAILED ({exc})")
            failed = True
    return failed


def check_project(ep):
    problems = []
    documents = {}
    for name, expected_type in (("blocs.json", list), ("montage_images.json", dict)):
        try:
            value = json.loads((ep / name).read_text(encoding="utf-8"))
            if not isinstance(value, expected_type):
                raise ValueError(f"expected {expected_type.__name__}")
            documents[name] = value
        except (OSError, ValueError) as exc:
            problems.append(f"{name}: {exc}")
    if len(documents) == 2:
        config = documents["montage_images.json"]
        aliases = config.get("alias", {})
        images_by_block = config.get("blocs", {})
        if not isinstance(aliases, dict):
            problems.append("montage_images.json: alias must be an object")
            aliases = {}
        if not isinstance(images_by_block, dict):
            problems.append("montage_images.json: blocs must be an object")
            images_by_block = {}
        numbered_blocks = set()
        for block in documents["blocs.json"]:
            if not isinstance(block, dict) or not isinstance(block.get("n"), int):
                problems.append("blocs.json: expected a numbered block")
                continue
            if not block.get("mots"):
                continue
            number = block["n"]
            numbered_blocks.add(number)
            wav = ep / "voix" / "narration" / f"b{number:02d}.wav"
            if not wav.is_file():
                problems.append(f"Block {number}: missing {wav.name}")
            images = images_by_block.get(str(number))
            if not isinstance(images, list) or not images:
                problems.append(f"Block {number}: expected at least one image alias")
                continue
            for alias in images:
                path = (aliases.get(alias) or aliases.get(alias[:-1])) if isinstance(alias, str) else None
                if not isinstance(path, str) or not (ep / path).is_file():
                    problems.append(f"Block {number}: missing image for alias {alias!r}")
        if not numbered_blocks:
            problems.append("No narration blocks found")
        if config.get("titre_apres_bloc", 2) in numbered_blocks:
            image = aliases.get("F3")
            clip = config.get("clip_titre")
            if not (clip and (ep / "anim" / "clips" / f"{clip}.mp4").is_file()):
                if not isinstance(image, str) or not (ep / image).is_file():
                    problems.append("Opening title: missing image for alias 'F3'")
        tracks = config.get("musiques", [])
        if not isinstance(tracks, list):
            problems.append("montage_images.json: musiques must be an array")
            tracks = []
        for track in tracks:
            if not isinstance(track, dict):
                problems.append("montage_images.json: expected a music entry object")
                continue
            name = track.get("fichier")
            if not isinstance(name, str) or not (RACINE / "Musique" / "themes" / name).is_file():
                problems.append(f"Missing music file: {name!r}")
            if track.get("de_bloc") not in numbered_blocks:
                problems.append(f"Music {name!r}: invalid starting block")
    for problem in problems:
        print(f"ERROR: {problem}")
    if not problems:
        print(f"{ep.name}: basic render inputs OK")
    return bool(problems)


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        language = option(args, "--ui-language") or "en"
        if language not in {"en", "fr"}:
            sys.exit("Supported help languages: en, fr")
        print((FRENCH_HELP if language == "fr" else __doc__).strip())
        return
    if args == ["doctor"]:
        sys.exit(doctor())
    if len(args) < 2:
        sys.exit(__doc__)
    etape, nom = args.pop(0), args.pop(0)
    english_command = etape == "new"
    etape = COMMANDS.get(etape, etape)
    if etape == "nouveau":
        language = option(args, "--language") or ("en" if english_command else "fr")
        if language not in {"en", "fr"} or args:
            sys.exit("Usage: new YYYY-MM-DD_topic [--language en|fr]")
        dest = EPISODES / nom
        if dest.exists():
            sys.exit(f"Project already exists: {dest}")
        shutil.copytree(RACINE / "Modeles" / "projet", dest)
        if language == "en":
            shutil.copytree(RACINE / "Modeles" / "en", dest, dirs_exist_ok=True)
            settings_path = dest / "montage_images.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings.update(langue="en", titre_ouverture={"grand": "THE TOPIC", "petit": "A short subtitle"},
                            ecran_fin={"duree": 15, "texte": "SUBSCRIBE", "sous": "A short invitation"})
            settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for d in ("images", "refs", "anim/clips", "voix/narration"):
            (dest / d).mkdir(parents=True, exist_ok=True)
        print("Created:", dest)
        return
    ep = trouver(nom)
    if etape == "check":
        sys.exit(check_project(ep))
    narr = ep / "voix" / "narration"
    seul = option(args, "--only") or option(args, "--seulement")
    liste = seul.split(",") if seul else []
    langue = "fr"
    if (ep / "montage_images.json").exists():
        langue = json.loads((ep / "montage_images.json").read_text(encoding="utf-8")).get("langue", "fr")
    base = ["--langue", langue, "--prises", "3", "--min-mots", "12", "--blocs", ep / "blocs.json", "--prononciation", ep / "montage_images.json"]
    if etape == "blocs":
        outils("script_blocs.py", ep)
    elif etape == "voix":
        voix_py("voix_narrateur.py", narrateur(ep), narr, *base, *(["--seulement", seul] if seul else []))
    elif etape == "refaire":
        al = narr / "alertes.json"
        blocs = sorted({a["bloc"] for a in json.loads(al.read_text(encoding="utf-8"))})
        if not blocs:
            print("Aucune alerte.")
            return
        voix_py("voix_narrateur.py", narrateur(ep), narr, *base, "--seulement", ",".join(blocs), "--refaire", al)
    elif etape == "choisir":
        outils("voix_choisir.py", narr, *liste)
    elif etape == "nettoyer":
        outils("voix_nettoyer.py", narr, *liste, "--langue", langue)
    elif etape == "animer":
        outils("animer.py", ep / "anim", *args, "--qualite")
    elif etape == "plan":
        outils("plan_montage.py", ep, args[0] if args else version_suivante(ep))
    elif etape == "ecoute":
        outils("montage.py", ep.relative_to(RACINE), "--ecoute")
    elif etape == "montage":
        outils("montage.py", ep.relative_to(RACINE))
    elif etape == "verifier":
        outils("verifier.py", ep, *args)
    elif etape == "finir":
        finir(ep)
    else:
        sys.exit(__doc__)


main()
