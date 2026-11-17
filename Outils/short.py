"""Fabrique les Shorts verticaux (1080x1920) d'une vidéo validée, avec sa voix et ses images déjà validées : rien de nouveau à générer.
Usage (Python « python_outils », qui a faster-whisper) : python Outils/short.py <projet> [nom_du_short ...]
Lit Episodes/<projet>/shorts.json :
  {"police_sous_titres": "Polices/X.ttf" (facultatif, sinon police_phrase de config.json),
   "shorts": [{"nom": "short1", "accroche": "Texte en haut au début", "fin": "Texte de fin",
               "musique": "theme.mp3",
               "plans": [{"bloc": 26, "images": [["M26", 0.5]]}, ...]}]}
  images : [alias de montage_images.json, position horizontale du recadrage 0-1 (0 = bord gauche, 0.5 = centre)].
Pour chaque Short : recadre les images en 9:16, écrit shorts/<nom>/episode.json, fait le rendu avec montage.py,
puis incruste l'accroche, les sous-titres (mots du script, calés sur la voix par la transcription) et le texte de fin.
Polices et couleurs : "theme_titres" de montage_images.json ; langue : "langue" (fr par défaut).
Résultat : A_publier/<projet>_<nom>.mp4. Règles : Docs/shorts.md.
"""
import difflib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import FFMPEG, FFPROBE, POLICE_PHRASE, POLICE_TITRES, PYTHON_OUTILS, RACINE, media_fingerprint
import musique
import struct

FPS = 30
CIBLE_MUSIQUE = -36.0  # même règle que plan_montage.py : la musique ne dépasse jamais la voix
TRANS = 0.5            # fondu entre deux images
AVANT, ECART = 0.3, 0.8  # silence avant chaque passage de voix, silence entre deux passages
FIN = 3.0              # durée du texte de fin, sur la dernière image
MOTS_MAX, CAR_MAX = 3, 17  # taille d'un sous-titre (gros texte lisible sur téléphone, retour du 12 nov.)

ep = RACINE / "Episodes" / sys.argv[1]
choix = set(sys.argv[2:])
conf = json.loads((ep / "montage_images.json").read_text(encoding="utf-8"))
blocs = {b["n"]: b for b in json.loads((ep / "blocs.json").read_text(encoding="utf-8"))}
reglages = json.loads((ep / "shorts.json").read_text(encoding="utf-8"))
shorts = reglages["shorts"]
LANGUE = conf.get("langue", "fr")
theme = conf.get("theme_titres", {})


def duree(f):
    return float(subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True, check=True).stdout)


def niveau(f, d):
    err = subprocess.run([FFMPEG, "-hide_banner", "-nostats", "-t", str(d), "-i", str(f), "-af", "ebur128=framelog=quiet",
                          "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def ass_couleur(rgb):
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}"


def norm(m):
    m = unicodedata.normalize("NFD", m.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in m if unicodedata.category(c) != "Mn"))


def famille(ttf):
    """Nom de famille d'une police (table « name » du fichier), pour les sous-titres incrustés."""
    data = Path(ttf).read_bytes()
    for i in range(struct.unpack(">H", data[4:6])[0]):
        tag, _, off, _ = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
        if tag == b"name":
            _, nb, so = struct.unpack(">HHH", data[off:off + 6])
            for k in range(nb):
                pid, _, _, nid, ln, o = struct.unpack(">HHHHHH", data[off + 6 + 12 * k:off + 18 + 12 * k])
                if nid == 1:
                    brut = data[off + so + o:off + so + o + ln]
                    return brut.decode("utf-16-be") if pid in (0, 3) else brut.decode("latin-1")
    return Path(ttf).stem


def ass_temps(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def mots_cales(wav, texte, modele):
    """Mots du script avec leur heure dans le fichier voix : la transcription donne les heures, le script donne l'orthographe."""
    script = texte.split()
    import numpy as np  # le son est décodé par ffmpeg : la lecture directe d'un fichier par faster-whisper plante (version de « av »)
    brut = subprocess.run([FFMPEG, "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                          capture_output=True, check=True).stdout
    segs, _ = modele.transcribe(np.frombuffer(brut, dtype=np.float32).copy(), language=LANGUE, word_timestamps=True,
                                condition_on_previous_text=False)
    entendus = [w for s in segs for w in s.words]
    a, b = [norm(m) for m in script], [norm(w.word) for w in entendus]
    heures = [None] * len(script)
    for bloc in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bloc.size):
            heures[bloc.a + k] = (entendus[bloc.b + k].start, entendus[bloc.b + k].end)
    # mots non reconnus (noms propres…) : heure interpolée entre les voisins
    connus = [i for i, h in enumerate(heures) if h]
    for i in range(len(script)):
        if heures[i] is None:
            av = max([j for j in connus if j < i], default=None)
            ap = min([j for j in connus if j > i], default=None)
            t0 = heures[av][1] if av is not None else 0.0
            t1 = heures[ap][0] if ap is not None else t0 + 0.4 * (i - (av if av is not None else -1))
            n0, n1 = (av if av is not None else -1), (ap if ap is not None else len(script))
            t = t0 + (t1 - t0) * (i - n0) / max(1, n1 - n0)
            heures[i] = (t, t + 0.3)
    return list(zip(script, heures))


def morceler(mots):
    """Groupes de 2 à 4 mots, coupés après la ponctuation."""
    groupes, g = [], []
    for m, h in mots:
        if g and (len(g) >= MOTS_MAX or len(" ".join(x for x, _ in g + [(m, h)])) > CAR_MAX):
            groupes.append(g); g = []
        g.append((m, h))
        if re.search(r"[.,;:!?»]$", m) and len(g) >= 2:
            groupes.append(g); g = []
    if g:
        groupes.append(g)
    return groupes


def recadrer(cle, x, dest):
    src = ep / conf["alias"][cle]
    f = f"crop=trunc(ih*9/16/2)*2:ih:(iw-ih*9/16)*{x}:0"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(src), "-vf", f, str(dest)], check=True)


def departs(morceaux):
    t, d = [0.0], [max(1, round(m["duree"] * FPS)) / FPS for m in morceaux]
    for i in range(1, len(morceaux)):
        td = max(1, round(morceaux[i].get("tduree", 1 / FPS) * FPS)) / FPS if morceaux[i].get("transition") else 1 / FPS
        t.append(t[-1] + d[i - 1] - td)
    return t, t[-1] + d[-1]


modele = None
for s in shorts:
    if choix and s["nom"] not in choix:
        continue
    d = ep / "shorts" / s["nom"]
    (d / "img").mkdir(parents=True, exist_ok=True)
    morceaux, sons, voix, sources = [], [], [], []
    for p, plan in enumerate(s["plans"]):
        wav = ep / "voix" / "narration" / f"b{plan['bloc']:02d}.wav"
        sources.append(wav)
        dv = duree(wav)
        total = AVANT + dv + ECART + TRANS + (FIN if p == len(s["plans"]) - 1 else 0)
        part = total / len(plan["images"])
        voix.append((len(morceaux), wav, plan["bloc"]))
        sons.append({"fichier": f"../../voix/narration/{wav.name}", "morceau": len(morceaux), "dt": AVANT, "voix": True, "volume": 1.0})
        for j, (cle, x) in enumerate(plan["images"]):
            sources.append(ep / conf["alias"][cle])
            nom_img = f"img/{cle}_{round(x * 100)}.png"
            recadrer(cle, x, d / nom_img)
            m = {"image": nom_img, "duree": round(part, 2), "zoom": [1.0, 1.07] if len(morceaux) % 2 == 0 else [1.07, 1.0],
                 "centre": [0.5, 0.45]}
            if morceaux:
                m.update({"transition": "dissolve", "tduree": TRANS})
            morceaux.append(m)
    t, total = departs(morceaux)
    try:
        mu = musique.verifier(s["musique"])  # jamais une musique réclamée (Musique/INTERDITES.txt)
    except musique.MusiqueRefusee as e:
        sys.exit(f"ARRÊT : {e}")
    vol = round(10 ** ((CIBLE_MUSIQUE - niveau(mu, total)) / 20), 4)
    sons.append({"fichier": f"../../../../Musique/themes/{s['musique']}", "morceau": 0, "dt": 0.0, "volume": vol,
                 "duree": round(total, 2), "fondu_in": 1.5, "fondu_out": 2.5, "creux_voix": True, **({"boucle": True} if duree(mu) < total else {})})
    tmp_nom = f"_tmp_{ep.name}_{s['nom']}"
    render_plan = {"magique": {
        "format": "9:16", "nom": tmp_nom, "bloom": 0.18, "fin_son": 2.0, "fin_image": 0.8, "theme_titres": {},
        "morceaux": morceaux, "titres": [], "sons": sons}}
    (d / "episode.json").write_text(json.dumps(render_plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"== {s['nom']} : {len(morceaux)} images, {total:.1f} s, musique à {vol}")
    base = d / "rendu_sans_textes.mp4"  # gardé : on peut refaire les textes sans refaire le rendu
    stamp = base.with_suffix(".sha256")
    engine = RACINE / "Outils"
    fingerprint = media_fingerprint(render_plan, [*sources, mu, Path(__file__),
                                                    engine / "montage.py", engine / "kenburns.py"])
    if base.is_file() and stamp.is_file() and stamp.read_text(encoding="ascii") == fingerprint:
        print("   rendu déjà fait, textes seulement")
    else:
        subprocess.run([PYTHON_OUTILS, "-I", str(RACINE / "Outils" / "montage.py"), str(d.relative_to(RACINE))], check=True, cwd=RACINE)
        (RACINE / "A_publier" / f"{tmp_nom}.mp4").replace(base)
        stamp.write_text(fingerprint, encoding="ascii")

    # textes incrustés : accroche, sous-titres, fin
    if modele is None:
        from faster_whisper import WhisperModel
        modele = WhisperModel("small", device="cpu", compute_type="int8")
    os_, vert = theme.get("couleur", [255, 255, 255]), theme.get("couleur_sous", [255, 214, 120])
    contour = theme.get("contour", [0, 0, 0])
    p_titre = RACINE / theme["police"] if theme.get("police") else Path(POLICE_TITRES)
    p_sous = RACINE / reglages["police_sous_titres"] if reglages.get("police_sous_titres") else Path(POLICE_PHRASE)
    if not p_sous.exists():
        p_sous = p_titre
    lignes = []
    for k, (i, wav, n) in enumerate(voix):
        texte = re.sub(r"\[#\d+\]|\{[^}]*\}", "", blocs[n]["texte"])
        texte = re.sub(r"«\s*", "«", re.sub(r"\s*»", "»", re.sub(r"\s+", " ", texte))).strip()  # guillemets collés au mot
        groupes = morceler(mots_cales(wav, texte, modele))
        debut = t[i] + AVANT
        for gi, g in enumerate(groupes):
            a = debut + g[0][1][0]
            fin_mots = debut + g[-1][1][1] + 0.6  # pas de sous-titre qui reste affiché pendant un silence
            b = min(debut + groupes[gi + 1][0][1][0], fin_mots) if gi + 1 < len(groupes) else fin_mots - 0.35
            lignes.append(f"Dialogue: 0,{ass_temps(a)},{ass_temps(b)},Sous,,0,0,0,,{' '.join(m for m, _ in g)}")
    lignes.append(f"Dialogue: 1,{ass_temps(0.2)},{ass_temps(3.6)},Accroche,,0,0,0,,{{\\fad(250,400)}}{s['accroche']}")
    lignes.append(f"Dialogue: 1,{ass_temps(total - FIN + 0.2)},{ass_temps(total - 0.3)},Fin,,0,0,0,,{{\\fad(400,300)}}{s['fin']}")
    entete = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sous,{famille(p_sous)},96,{ass_couleur(os_)},&H00FFFFFF,{ass_couleur(contour)},&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,70,70,600,1\n"
        f"Style: Accroche,{famille(p_titre)},104,{ass_couleur(vert)},&H00FFFFFF,{ass_couleur(contour)},&H96000000,-1,0,0,0,100,100,0,0,1,7,3,8,80,80,250,1\n"
        f"Style: Fin,{famille(p_titre)},96,{ass_couleur(vert)},&H00FFFFFF,{ass_couleur(contour)},&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,80,80,0,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    (d / "textes.ass").write_text(entete + "\n".join(lignes) + "\n", encoding="utf-8")
    (d / "polices").mkdir(exist_ok=True)
    for p in {p_sous, p_titre}:
        shutil.copy(p, d / "polices" / p.name)
    final = RACINE / "A_publier" / f"{ep.name}_{s['nom']}.mp4"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(base), "-vf", "ass=textes.ass:fontsdir=polices",
                    "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy",
                    "-movflags", "+faststart", str(final)], check=True, cwd=d)
    print(f"Terminé : {final} ({duree(final):.1f} s, {final.stat().st_size / 1e6:.1f} Mo)")
