r"""Rendu de la vidéo : zooms doux, transitions, textes à l'écran, voix et musique. Ne rien déplacer dans le projet pendant son exécution.
Usage : fabriquer.py montage <projet>
"format": "16:9" (par défaut) ou "9:16" (Short), "nom" = nom du fichier de sortie.
Lit la section "magique" de <projet>\episode.json (écrit par plan_montage.py) :
  morceaux : [{clip, de, a, vitesse?, gel?, image?: "plan.png" (image fixe au lieu d'un clip, avec duree),
               zoom?: [z0, z1], centre?: [x, y] (0-1, point visé par le zoom), secousse?: force (px),
               aberration?: true, flash?: true, desat?: 0-1,
               transition?: nom xfade (entrée dans ce morceau), tduree?: s}]
  titres   : [{texte, sous?, style, morceau, dt, duree, couleur?}]
  sons     : [{fichier, morceau, dt, debut?, duree?, volume?, fondu_in?, fondu_out?, grave?, echo?}]
  bloom    : 0-1 (halo lumineux, défaut 0.25)
Clips pris dans clips/hd/ (agrandis par RealESRGAN, fait automatiquement). Résultat : A_publier\<dossier>.mp4
"""
import json, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import COMFY_ENTREE, COMFY_URL, FFMPEG, POLICE_TITRES as POLICE, PYTHON_VOIX as VENV, RACINE

DOSSIER = (RACINE / sys.argv[1]).resolve()
CONF = json.loads((DOSSIER / "episode.json").read_text(encoding="utf8"))["magique"]
THEME = CONF.get("theme_titres") or {}  # chaque vidéo a son thème de titres : police, couleurs, placement (montage_images.json)
if THEME.get("police"):
    POLICE = RACINE / THEME["police"]
SORTIE = RACINE / "A_publier" / f"{CONF.get('nom', DOSSIER.name)}.mp4"
W, H = (1080, 1920) if CONF.get("format") == "9:16" else (1920, 1080)
FPS = 30


def run(*args, cwd=None):
    subprocess.run([FFMPEG, "-v", "error", "-y", *args], check=True, cwd=cwd)


def agrandir(clip, dest):
    COMFY, ENTREE = COMFY_URL, Path(COMFY_ENTREE)
    dest.parent.mkdir(exist_ok=True)
    nom = f"magique_{DOSSIER.name}_{clip.stem}.mp4"
    shutil.copy(clip, ENTREE / nom)
    wf = {"1": {"class_type": "LoadVideo", "inputs": {"file": nom}},
          "2": {"class_type": "GetVideoComponents", "inputs": {"video": ["1", 0]}},
          "3": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x2plus.pth"}},
          "4": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["3", 0], "image": ["2", 0]}},
          "5": {"class_type": "CreateVideo", "inputs": {"images": ["4", 0], "fps": ["2", 2]}},
          "6": {"class_type": "SaveVideo", "inputs": {"video": ["5", 0], "filename_prefix": f"magique/{clip.stem}",
                                                     "format": "auto", "codec": "auto"}}}
    req = urllib.request.Request(f"{COMFY}/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})
    pid = json.load(urllib.request.urlopen(req))["prompt_id"]
    while True:
        time.sleep(3)
        h = json.load(urllib.request.urlopen(f"{COMFY}/history/{pid}"))
        if pid in h:
            break
    o = h[pid]["outputs"]["6"]["images"][0]
    q = urllib.parse.urlencode({"filename": o["filename"], "subfolder": o["subfolder"], "type": "output"})
    dest.write_bytes(urllib.request.urlopen(f"{COMFY}/view?{q}").read())


def boucle_sans_saut(src, t=0.5):
    """Fond la fin du clip dans son début : la 1re et la dernière image Wan diffèrent (le feu…), sinon petit saut à chaque tour."""
    dest = src.with_name(src.stem + "_boucle.mp4")
    if dest.exists():
        return dest
    sonde = str(Path(FFMPEG).with_name("ffprobe.exe"))
    l = float(subprocess.run([sonde, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
                             capture_output=True, text=True, check=True).stdout)
    f = (f"[0:v]split[a][b];[a]trim=start={t},setpts=PTS-STARTPTS[x];[b]trim=end={t},setpts=PTS-STARTPTS[y];"
         f"[x][y]xfade=transition=fade:duration={t}:offset={l - 2 * t:.3f},format=yuv420p[v]")
    run("-i", str(src), "-filter_complex", f, "-map", "[v]", "-c:v", "libx264", "-crf", "14", str(dest))
    return dest


def camera(m, d):
    """Zoom doux (ease in-out) vers un point + secousse d'impact qui s'amortit."""
    z0, z1 = m.get("zoom", [1.0, 1.0])
    cx, cy = m.get("centre", [0.5, 0.5])
    f = ""
    if (z0, z1) != (1.0, 1.0):
        n = max(1, int(d * FPS))
        e = f"(1-cos(PI*min(on/{n}\\,1)))/2"
        z = f"({z0}+({z1}-{z0})*{e})"
        f += (f",scale={W*2}:{H*2}:flags=lanczos,zoompan=z='{z}':"
              f"x='max(0\\,min(iw-iw/zoom\\,{cx}*iw-iw/zoom/2))':y='max(0\\,min(ih-ih/zoom\\,{cy}*ih-ih/zoom/2))':"
              f"d=1:s={W}x{H}:fps={FPS}")
    s = m.get("secousse", 0)
    if s:
        f += (f",scale={W+2*s}:{H+2*s},crop={W}:{H}:"
              f"x='{s}+{s}*exp(-t*7)*sin(t*73)':y='{s}+{s}*exp(-t*7)*cos(t*61)'")
    return f


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    shutil.copy(POLICE, tmp / "police.ttf")
    durees = []
    for i, m in enumerate(CONF["morceaux"]):
        sortie = str(tmp / f"m{i}.mp4")
        if m.get("image"):
            # durée arrondie à une image près : sinon les arrondis s'additionnent sur 40+ plans et la première
            # coupe nette (transition d'une image) arrive après la fin de la vidéo précédente → image figée/arrêtée
            d = max(1, round(m["duree"] * FPS)) / FPS
            z0, z1 = m.get("zoom", [1.0, 1.0])
            cx, cy = m.get("centre", [0.5, 0.5])
            kb = tmp / f"k{i}.mp4"
            # zoom lent fluide calculé sur la carte graphique (zoompan de FFmpeg = image qui « vibre »)
            subprocess.run([str(VENV), str(RACINE / "Outils" / "kenburns.py"), str(DOSSIER / m["image"]), str(kb),
                            f"{d:.4f}", str(z0), str(z1), str(cx), str(cy), str(W), str(H), str(FPS)],
                           check=True, capture_output=True)
            entree = ["-i", str(kb)]
            f = f"[0:v]setsar=1,fps={FPS}"
            m = {**m, "zoom": [1.0, 1.0]}  # le zoom est déjà fait
        else:
            clips = DOSSIER / CONF.get("dossier_clips", "clips")
            src = clips / "hd" / f"{m['clip']}.mp4"
            if not src.exists():
                agrandir(clips / f"{m['clip']}.mp4", src)
            v = m.get("vitesse", 1.0)
            if m.get("boucle"):
                # boucle Wan (1re image = dernière image) répétée aussi longtemps que le plan dure
                d = max(1, round(m["duree"] * FPS)) / FPS
                src = boucle_sans_saut(src)
                entree = ["-stream_loop", "-1", "-i", str(src)]
                f = (f"[0:v]trim=duration={d:.4f},setpts=PTS-STARTPTS,"
                     f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1")
            else:
                d = max(1, round((m["a"] - m["de"]) / v * FPS)) / FPS
                entree = ["-i", str(src)]
                f = (f"[0:v]trim={m['de']}:{m['a']},setpts=(PTS-STARTPTS)/{v},"
                     f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1")
            if v < 0.9:
                f += f",minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
            f += f",fps={FPS}"
        gel = round(m.get("gel", 0) * FPS) / FPS
        if gel:
            f += f",tpad=stop_mode=clone:stop_duration={gel}"
            d += gel
        f += camera(m, d)
        if m.get("desat"):
            f += f",hue=s={1 - m['desat']}"
        if m.get("flash"):
            f += ",eq=brightness='if(lt(t\\,0.15)\\,0.7*(1-t/0.15)\\,0)':eval=frame"
        if m.get("aberration"):
            f += ",split[a][b];[b]rgbashift=rh=-14:bh=14:gv=4[c];[a][c]overlay=enable='lt(t\\,0.18)'"
        # sécurité : un morceau trop court (ralenti/zoompan) arrêtait toute la vidéo au xfade suivant
        f += f",tpad=stop_mode=clone:stop_duration=3,trim=duration={d:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]"
        run(*entree, "-filter_complex", f, "-map", "[v]", "-c:v", "libx264", "-crf", "14", sortie)
        durees.append(d)

    # Enchaînement avec transitions (xfade) ; coupe franche si pas de transition
    entrees, debuts = [], []
    for i in range(len(durees)):
        entrees += ["-i", str(tmp / f"m{i}.mp4")]
    # même base de temps pour tous (sinon xfade peut arrêter la vidéo en route)
    f = "".join(f"[{i}:v]fps={FPS},settb=1/{FPS},setpts=N[n{i}];" for i in range(len(durees)))
    prec, t = "n0", durees[0]
    debuts.append(0.0)
    for i in range(1, len(durees)):
        m = CONF["morceaux"][i]
        tr, td = m.get("transition", "fade"), m.get("tduree", 0.0) if m.get("transition") else 1 / FPS
        td = max(1, round(td * FPS)) / FPS  # transitions aussi en nombre entier d'images
        t -= td
        debuts.append(t)
        f += f"[{prec}][n{i}]xfade=transition={tr}:duration={td}:offset={t:.3f}[x{i}];"
        prec = f"x{i}"
        t += durees[i]
    total = t

    b = CONF.get("bloom", 0.25)
    f += (f"[{prec}]eq=contrast=1.08:saturation=1.12:gamma=0.97,"
          f"colorbalance=rs=0.03:bs=-0.02:rh=0.03:bh=-0.04,split[n][h];[h]gblur=sigma=22[hb];"
          f"[n][hb]blend=all_mode=screen:all_opacity={b},vignette=PI/4.5,unsharp=5:5:0.35")  # plus de grain animé (il « fourmillait »)
    # textes à l'écran : PNG dessinés par Outils/titres_png.py (voile doux, doré dégradé, ornement), posés en fondu
    (tmp / "titres.json").write_text(json.dumps(CONF.get("titres", []), ensure_ascii=False), encoding="utf8")
    (tmp / "theme.json").write_text(json.dumps(THEME, ensure_ascii=False), encoding="utf8")
    subprocess.run([str(VENV), str(RACINE / "Outils" / "titres_png.py"), str(tmp), str(POLICE)], check=True)
    f += "[base0]"
    for j, tx in enumerate(CONF.get("titres", [])):
        a = debuts[tx["morceau"]] + tx.get("dt", 0)
        d = tx["duree"]
        f += (f";movie=t{j}.png,format=rgba,loop=loop={round(d * FPS)}:size=1:start=0,setpts=N/{FPS}/TB+{a:.3f}/TB,"
              f"fade=t=in:st={a:.3f}:d=0.5:alpha=1,fade=t=out:st={a + d - 0.6:.3f}:d=0.6:alpha=1[tt{j}];"
              f"[base{j}][tt{j}]overlay=0:0:eof_action=pass:repeatlast=0[base{j + 1}]")
    f += f";[base{len(CONF.get('titres', []))}]fade=in:st=0:d=0.25,fade=out:st={total-CONF.get('fin_image', 0.6):.3f}:d={CONF.get('fin_image', 0.6)}[vid]"

    pistes, voix, na = [], [], len(durees)
    for s in CONF.get("sons", []):
        ms = max(0, int((debuts[s["morceau"]] + s.get("dt", 0)) * 1000))
        entrees += (["-stream_loop", "-1"] if s.get("boucle") else []) + ["-ss", str(s.get("debut", 0)), "-i", str(DOSSIER / s["fichier"])]
        filtre = f"[{na}:a]aresample=48000,aformat=channel_layouts=stereo"
        if s.get("duree"):
            dd, fo = s["duree"], s.get("fondu_out", 0.05)
            filtre += f",atrim=0:{dd},afade=out:st={max(0, dd - fo):.3f}:d={fo}"
        if s.get("fondu_in"):
            filtre += f",afade=in:d={s['fondu_in']}"
        if s.get("grave"):
            filtre += f",asetrate=48000*{s['grave'] if isinstance(s['grave'], float) else 0.7},aresample=48000"
        if s.get("echo"):
            filtre += ",apad=pad_dur=1.5,aecho=0.8:0.7:120|260:0.45|0.3"
        f += f";{filtre},volume={s.get('volume', 1)},adelay={ms}|{ms}[s{na}]"
        (voix if s.get("voix") else pistes).append(f"[s{na}]")
        na += 1
    if pistes:
        f += f";{''.join(pistes)}amix=inputs={len(pistes)}:normalize=0:duration=longest"
        if voix:  # "voix": true -> la musique et les bruitages baissent automatiquement sous la voix
            f += (f"[fond];{''.join(voix)}amix=inputs={len(voix)}:normalize=0:duration=longest,apad=whole_dur={total:.3f},asplit[v1][v2];"  # apad : sinon le son s'arrête à la dernière voix
                  f"[fond][v1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[fc];"
                  f"[fc][v2]amix=inputs=2:normalize=0:duration=longest")
    else:  # vidéo sans musique ni bruitage : seulement la voix
        f += f";{''.join(voix)}amix=inputs={len(voix)}:normalize=0:duration=longest,apad=whole_dur={total:.3f}"
    f += (f",atrim=0:{total:.3f},"
          f"afade=out:st={total-CONF.get('fin_son', 0.8):.3f}:d={CONF.get('fin_son', 0.8)},loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89[aud]")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    run(*entrees, "-filter_complex", f, "-map", "[vid]", "-map", "[aud]", "-c:v", "libx264", "-crf", "17",
        "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(SORTIE), cwd=tmp)
    for i, d in enumerate(debuts):
        print(f"  morceau {i:2d} : {d:5.2f} s  {CONF['morceaux'][i].get('clip') or CONF['morceaux'][i].get('image')}")
print("Terminé :", SORTIE, f"({total:.1f} s)")
