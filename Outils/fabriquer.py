"""La seule commande à retenir : lance chaque étape avec le bon Python. Voir Docs/workflow.md.
Usage : python Outils/fabriquer.py <étape> <projet> [options]
  nouveau AAAA-MM-JJ_sujet       crée le projet depuis Modeles/projet
  blocs     découpe script.md en blocs
  voix      génère la narration (--seulement b05,b09)
  choisir   garde la meilleure prise et assemble (--seulement b05,b09)
  refaire   ajoute des prises aux morceaux en alerte
  nettoyer  retire respirations et bruits (--seulement b05,b09)
  animer    optionnel, anime les plans (nom d'un seul plan possible : animer <projet> boucle_large)
  plan      calcule le montage, version suivante (v1, v2…)
  montage   fait le rendu
  verifier  contrôle automatique de la dernière vidéo
  finir     limite les pics du son et crée l'aperçu 720p
<projet> : le nom du dossier, ou un morceau de ce nom s'il n'y en a qu'un (ex. volcans).
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG, PYTHON_OUTILS, PYTHON_VOIX, RACINE

sys.stdout.reconfigure(encoding="utf-8")
EPISODES, OUTILS = RACINE / "Episodes", RACINE / "Outils"


def trouver(nom):
    if (EPISODES / nom).is_dir():
        return EPISODES / nom
    c = [p for p in EPISODES.iterdir() if p.is_dir() and nom in p.name and not p.name.startswith("_")]
    if len(c) != 1:
        sys.exit(f"Projet introuvable ou ambigu : {nom} ({len(c)} résultat(s))")
    return c[0]


def outils(script, *a):
    subprocess.run([PYTHON_OUTILS, "-I", str(OUTILS / script), *map(str, a)], check=True, cwd=RACINE)


def voix_py(script, *a):
    subprocess.run([PYTHON_VOIX, str(OUTILS / script), *map(str, a)], check=True, cwd=RACINE)


def option(args, nom):
    if nom in args:
        i = args.index(nom)
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


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    etape, nom = args.pop(0), args.pop(0)
    if etape == "nouveau":
        dest = EPISODES / nom
        if dest.exists():
            sys.exit(f"Existe déjà : {dest}")
        shutil.copytree(RACINE / "Modeles" / "projet", dest)
        for d in ("images", "refs", "anim/clips", "voix/narration"):
            (dest / d).mkdir(parents=True, exist_ok=True)
        print("Créé :", dest)
        return
    ep = trouver(nom)
    narr = ep / "voix" / "narration"
    seul = option(args, "--seulement")
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
    elif etape == "montage":
        outils("montage.py", ep.relative_to(RACINE))
    elif etape == "verifier":
        outils("verifier.py", ep)
    elif etape == "finir":
        finir(ep)
    else:
        sys.exit(__doc__)


main()
