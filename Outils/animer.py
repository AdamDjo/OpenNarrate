# Anime les plans d'un episode avec Wan 2.2 14B I2V + LoRA Lightning via l'API ComfyUI.
# Usage : fabriquer.py animer <projet> [nom_du_plan]. Les plans sont décrits dans <projet>/anim/episode.json.
import json
import shutil
import subprocess
import sys
import time
import uuid
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import COMFY_URL as COMFY, FFMPEG

NEGATIF = ("blurry, distorted face, deformed hands, extra fingers, extra limbs, text, watermark, "
           "subtitles, low quality, static frame, camera shake, morphing")


def workflow(image, texte, prefixe, seed, image_fin=None):
    wf = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
        "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "strength_model": 1}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["2", 0], "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "strength_model": 1}},
        "5": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["3", 0], "shift": 5}},
        "6": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["4", 0], "shift": 5}},
        "7": {"class_type": "CLIPLoader", "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": texte}},
        "10": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["7", 0], "text": NEGATIF}},
        "11": {"class_type": "LoadImage", "inputs": {"image": image}},
        "12": {"class_type": "WanImageToVideo", "inputs": {"positive": ["9", 0], "negative": ["10", 0], "vae": ["8", 0], "start_image": ["11", 0],
                                                         "width": 480, "height": 832, "length": 81, "batch_size": 1}},
        "13": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["5", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["12", 2],
                                                          "add_noise": "enable", "noise_seed": seed, "steps": 4, "cfg": 1, "sampler_name": "euler",
                                                          "scheduler": "simple", "start_at_step": 0, "end_at_step": 2, "return_with_leftover_noise": "enable"}},
        "14": {"class_type": "KSamplerAdvanced", "inputs": {"model": ["6", 0], "positive": ["12", 0], "negative": ["12", 1], "latent_image": ["13", 0],
                                                          "add_noise": "disable", "noise_seed": seed, "steps": 4, "cfg": 1, "sampler_name": "euler",
                                                          "scheduler": "simple", "start_at_step": 2, "end_at_step": 10000, "return_with_leftover_noise": "disable"}},
        "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["8", 0]}},
        # RIFE double le nombre d'images (16 -> 32 i/s) : mouvements plus fluides, moins "IA"
        "19": {"class_type": "RIFE VFI", "inputs": {"ckpt_name": "rife49.pth", "frames": ["15", 0], "clear_cache_after_n_frames": 10,
                                                   "multiplier": 2, "fast_mode": False, "ensemble": True, "scale_factor": 1.0,
                                                   "dtype": "float32", "torch_compile": False, "batch_size": 1}},
        "16": {"class_type": "CreateVideo", "inputs": {"images": ["19", 0], "fps": 32}},
        "17": {"class_type": "SaveVideo", "inputs": {"video": ["16", 0], "filename_prefix": prefixe, "format": "auto", "codec": "auto"}},
    }
    if image_fin:
        # Transition : Wan invente le mouvement entre l'image de depart et l'image d'arrivee
        wf["18"] = {"class_type": "LoadImage", "inputs": {"image": image_fin}}
        wf["12"] = {"class_type": "WanFirstLastFrameToVideo", "inputs": {"positive": ["9", 0], "negative": ["10", 0], "vae": ["8", 0],
                                                                       "start_image": ["11", 0], "end_image": ["18", 0],
                                                                       "width": 480, "height": 832, "length": 81, "batch_size": 1}}
    return wf


def requete(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req) as r:
        return r.read()


def envoyer_image(fichier):
    limite = uuid.uuid4().hex
    corps = (f"--{limite}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n"
             f"--{limite}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{fichier.name}\"\r\n"
             f"Content-Type: image/png\r\n\r\n").encode() + fichier.read_bytes() + f"\r\n--{limite}--\r\n".encode()
    rep = requete(f"{COMFY}/upload/image", corps, {"Content-Type": f"multipart/form-data; boundary={limite}"})
    return json.loads(rep)["name"]


def attendre(prompt_id):
    while True:
        time.sleep(5)
        h = json.loads(requete(f"{COMFY}/history/{prompt_id}")).get(prompt_id)
        if not h:
            continue
        statut = h.get("status", {})
        if statut.get("status_str") == "error":
            raise RuntimeError(json.dumps(statut.get("messages"))[:1500])
        if statut.get("completed"):
            return next(img for sortie in h["outputs"].values() for img in sortie.get("images", []))


def mode_qualite(wf):
    # Sans LoRA Lightning : 20 etapes, cfg 3.5 -> mouvements plus naturels, ~5x plus lent
    for n in ("3", "4"):
        del wf[n]
    wf["5"]["inputs"]["model"] = ["1", 0]
    wf["6"]["inputs"]["model"] = ["2", 0]
    for n, (debut, fin) in (("13", (0, 10)), ("14", (10, 10000))):
        wf[n]["inputs"].update({"steps": 20, "cfg": 3.5, "start_at_step": debut, "end_at_step": fin})
    return wf


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    qualite = "--qualite" in sys.argv
    dossier = Path(args[0] if args else "Episode1")
    seul = args[1] if len(args) > 1 else None
    episode = json.loads((dossier / "episode.json").read_text(encoding="utf-8"))
    (dossier / "clips").mkdir(exist_ok=True)

    for n, plan in enumerate(episode["plans"], start=1):
        nom_clip = plan.get("nom", f"plan{n}")
        if seul and seul != nom_clip:
            continue
        debut = time.time()
        if "images" in plan:
            # Scene a 3 images (debut, milieu, fin) : un segment par paire, puis collage sans coupure
            segments = []
            for i, (a, b) in enumerate(zip(plan["images"], plan["images"][1:]), start=1):
                seg = f"{nom_clip}_seg{i}"
                generer_clip(dossier, seg, a, b, plan["animations"][i - 1], 1000 + 10 * n + i, qualite)
                segments.append(dossier / "clips" / f"{seg}.mp4")
            coller(segments, dossier / "clips" / f"{nom_clip}.mp4")
        else:
            generer_clip(dossier, nom_clip, plan["image"], plan.get("image_fin"), plan["animation"], plan.get("seed", 1000 + n), qualite,
                         plan.get("images_video", 81), plan.get("largeur", 480), plan.get("hauteur", 832))
        print(f"Clip {nom_clip} : OK -> {dossier / 'clips' / (nom_clip + '.mp4')} ({round(time.time() - debut)} s)", flush=True)


def generer_clip(dossier, nom_clip, image, image_fin, animation, seed, qualite, longueur=81, largeur=480, hauteur=832):
    # largeur/hauteur : 480x832 = vertical (Shorts) ; 832x480 = horizontal 16:9 (vidéos longues de lore)
    print(f"  {nom_clip} : {image} -> {image_fin or '(libre)'}, {longueur} images, {largeur}x{hauteur}"
          f"{' (mode qualite)' if qualite else ''}...", flush=True)
    nom = envoyer_image(dossier / image)
    nom_fin = envoyer_image(dossier / image_fin) if image_fin else None
    wf = workflow(nom, animation, f"{dossier.name}/{nom_clip}", seed, nom_fin)
    wf["12"]["inputs"]["length"] = longueur  # 16 images = 1 seconde ; doit valoir 4k+1 (81, 97, 113...)
    wf["12"]["inputs"]["width"], wf["12"]["inputs"]["height"] = largeur, hauteur
    if qualite:
        wf = mode_qualite(wf)
    rep = json.loads(requete(f"{COMFY}/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"}))
    sortie = attendre(rep["prompt_id"])
    params = urllib.parse.urlencode({"filename": sortie["filename"], "subfolder": sortie["subfolder"], "type": "output"})
    (dossier / "clips" / f"{nom_clip}.mp4").write_bytes(requete(f"{COMFY}/view?{params}"))


def coller(segments, dest):
    # Chaque segment commence par la derniere image du precedent : on la retire pour eviter un arret sur image
    entrees, filtres = [], []
    for i, seg in enumerate(segments):
        entrees += ["-i", str(seg)]
        filtres.append(f"[{i}:v]{'trim=start_frame=1,' if i else ''}setpts=PTS-STARTPTS[v{i}]")
    filtres.append(f"{''.join(f'[v{i}]' for i in range(len(segments)))}concat=n={len(segments)}:v=1:a=0[out]")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *entrees, "-filter_complex", ";".join(filtres), "-map", "[out]",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(dest)], check=True)


if __name__ == "__main__":
    main()
