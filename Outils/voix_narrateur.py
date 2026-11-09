"""Étape 1/2 de la voix : génère plusieurs prises par morceau de texte (Chatterbox multilingue, licence MIT, local).
Étape 2/2 : Outils/voix_choisir.py (réécoute, choisit la meilleure prise, assemble avec pauses et ralenti).

Usage : fabriquer.py voix <projet> [--seulement b05,b09], ou pour un test :
  python Outils\\voix_narrateur.py <narrateur> <dossier_sortie> [--langue fr] [--prises 3] p01="Texte" [p02="Texte"]
Référence de la voix : Narrateurs/<narrateur>/reference.wav
Si le texte d'un bloc a changé, seules les prises des morceaux modifiés sont refaites.

À savoir :
- « il parle trop vite » → pauses entre les morceaux + ralenti (fait à l'étape 2) + cfg_weight bas (0.3) ;
- une phrase trop courte seule (« Tous les soirs. ») fait bégayer ou inventer des mots → on regroupe les phrases
  en morceaux d'au moins 8 mots ; « | » dans le texte = fin de paragraphe (longue pause).
Sortie : <dossier>/<nom>/plan.json + c01_p1.wav, c01_p2.wav… (24 kHz mono).
"""
import json
import re
import sys
from pathlib import Path

import torch
import torchaudio

RACINE = Path(__file__).resolve().parent.parent
PAUSES = {".": 0.6, "!": 0.6, "?": 0.7, "…": 1.0, ":": 0.45, "|": 1.2}
MIN_MOTS = 5
# Prononciation : "prononciation": {"Mot": "son écrit"} dans montage_images.json, utilisé seulement à la génération.
PRONONCIATION = {}


def prononcer(texte):
    for mot, son in PRONONCIATION.items():
        texte = texte.replace(mot, son)
    return texte


# Émotions : un repère {triste} dans le texte s'applique jusqu'au repère suivant.
# exag/cfg = réglages Chatterbox ; tempo = multiplie le ralenti global ; volume_db ; pause_plus = pause en plus.
EMOTIONS = {
    "neutre":         {"exag": 0.45, "cfg": 0.30, "tempo": 1.00, "volume_db": 0, "pause_plus": 0.0},
    "amuse":          {"exag": 0.70, "cfg": 0.35, "tempo": 1.04, "volume_db": 1, "pause_plus": 0.0},
    "joie":           {"exag": 0.75, "cfg": 0.35, "tempo": 1.05, "volume_db": 1, "pause_plus": 0.0},
    "triste":         {"exag": 0.35, "cfg": 0.25, "tempo": 0.90, "volume_db": -2, "pause_plus": 0.35},
    "confidence":     {"exag": 0.30, "cfg": 0.28, "tempo": 0.92, "volume_db": -4, "pause_plus": 0.25},
    "peur":           {"exag": 0.65, "cfg": 0.30, "tempo": 0.97, "volume_db": -1, "pause_plus": 0.15},
    "emerveillement": {"exag": 0.60, "cfg": 0.30, "tempo": 0.95, "volume_db": 0, "pause_plus": 0.2},
    "colere":         {"exag": 0.80, "cfg": 0.40, "tempo": 1.00, "volume_db": 2, "pause_plus": 0.0},
}


def option(args, nom, defaut):
    if nom in args:
        i = args.index(nom)
        val = args[i + 1]
        del args[i:i + 2]
        return val
    return defaut


def morceaux(texte):
    """Découpe en morceaux ; un repère {émotion} commence toujours un nouveau morceau.
    Renvoie [{texte, pause, emotion, tempo, volume_db}]."""
    out, emo = [], "neutre"
    for part in re.split(r"(\{[a-zé]+\})", texte):
        m = re.fullmatch(r"\{([a-zé]+)\}", part)
        if m:
            emo = m.group(1).replace("é", "e")
            if emo not in EMOTIONS:
                sys.exit(f"Émotion inconnue : {emo} (possibles : {', '.join(EMOTIONS)})")
            continue
        for c in morceaux_simples(part):
            e = EMOTIONS[emo]
            c.update({"emotion": emo, "tempo": e["tempo"], "volume_db": e["volume_db"]})
            c["pause"] = round(c["pause"] + e["pause_plus"], 2)
            out.append(c)
    return out


def morceaux_simples(texte):
    """Phrases regroupées en morceaux d'au moins MIN_MOTS mots ; renvoie [{texte, pause}]."""
    brut = re.findall(r"[^.!?…:|]+(?:\.\.\.|[.!?…:]+)?\s*\|?", texte)
    out, courant = [], ""
    for b in brut:
        b = b.strip()
        if not b:
            continue
        para = b.endswith("|")
        b = b.rstrip("|").strip()
        courant = (courant + " " + b).strip()
        if para and out and len(courant.split()) < 4:
            # un mot ou deux seuls en fin de paragraphe (« Fossoyeuse. ») : l'outil n'arrive pas à les dire seuls
            out[-1]["texte"] += " " + courant
            out[-1]["pause"] = PAUSES["|"]
            courant = ""
        elif len(courant.split()) >= MIN_MOTS or para:
            fin = courant[-1]
            out.append({"texte": courant, "pause": PAUSES["|"] if para else PAUSES.get(fin, 0.5)})
            courant = ""
    if courant:
        if out and len(courant.split()) < 4:  # un tout petit reste : on le colle au morceau précédent
            out[-1]["texte"] += " " + courant
        else:
            out.append({"texte": courant, "pause": 0.5})
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    langue = option(args, "--langue", "fr")
    prises = int(option(args, "--prises", "3"))
    MIN_MOTS = int(option(args, "--min-mots", str(MIN_MOTS)))
    blocs = option(args, "--blocs", None)  # blocs.json de Outils/script_blocs.py → un fichier par bloc (b02, b03…)
    # --refaire alertes.json (écrit par voix_choisir.py) : seulement ces morceaux, avec --prises prises en plus
    refaire = option(args, "--refaire", None)
    seulement = option(args, "--seulement", None)  # ex. b02,b03
    fichier_prononciation = option(args, "--prononciation", None)  # le montage_images.json du projet
    if fichier_prononciation:
        PRONONCIATION.update(json.loads(Path(fichier_prononciation).read_text(encoding="utf-8")).get("prononciation", {}))
    cibles = None
    if refaire:
        cibles = {(a["bloc"], a["morceau"]) for a in json.loads(Path(refaire).read_text(encoding="utf-8"))}
    narrateur, sortie, textes = args[0], Path(args[1]), args[2:]
    if blocs:
        textes = [f"b{b['n']:02d}={b['texte']}" for b in json.loads(Path(blocs).read_text(encoding="utf-8")) if b["mots"]]
    if seulement:  # ne touche pas aux autres blocs (leurs plan.json ont pu être retouchés à la main)
        textes = [x for x in textes if x.split("=", 1)[0] in seulement.split(",")]
    ref = RACINE / "Narrateurs" / narrateur / "reference.wav"
    if not ref.exists():
        sys.exit(f"Référence introuvable : {ref}")
    appareil = "cuda" if torch.cuda.is_available() else "cpu"
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    modele = ChatterboxMultilingualTTS.from_pretrained(device=appareil)

    for item in textes:
        nom, texte = item.split("=", 1)
        d = sortie / nom
        d.mkdir(parents=True, exist_ok=True)
        ancien = json.loads((d / "plan.json").read_text(encoding="utf-8")) if (d / "plan.json").exists() else None
        if ancien and (cibles is not None or ancien.get("source", texte) == texte):
            plan = ancien["morceaux"]  # texte inchangé : on garde le plan (il a pu être retouché), seules les prises manquantes sont faites
        else:
            plan = morceaux(texte)
            if ancien:  # texte modifié : on enlève les prises des morceaux qui ont changé
                for i, m in enumerate(ancien["morceaux"], 1):
                    if i > len(plan) or plan[i - 1]["texte"] != m["texte"]:
                        for f in d.glob(f"c{i:02d}_p*.wav"):
                            f.unlink()
            (d / "plan.json").write_text(json.dumps({"langue": langue, "source": texte, "morceaux": plan}, ensure_ascii=False, indent=1), encoding="utf-8")
        for i, m in enumerate(plan, 1):
            if cibles is not None and (nom, i) not in cibles:
                continue
            deja = len(list(d.glob(f"c{i:02d}_p*.wav"))) if cibles is not None else 0
            for p in range(1 + deja, prises + 1 + deja):
                f = d / f"c{i:02d}_p{p}.wav"
                if f.exists():
                    continue
                e = EMOTIONS[m.get("emotion", "neutre")]
                w = modele.generate(prononcer(m["texte"]), language_id=langue, audio_prompt_path=str(ref),
                                    exaggeration=e["exag"], cfg_weight=e["cfg"]).cpu()
                # écriture puis renommage : si le PC s'éteint en plein milieu, pas de prise à moitié écrite
                tmpf = f.with_name(f.stem + "_tmp.wav")
                torchaudio.save(str(tmpf), w, modele.sr)
                tmpf.replace(f)
                print(f, round(w.shape[-1] / modele.sr, 2), "s", flush=True)
