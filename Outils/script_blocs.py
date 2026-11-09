"""Découpe un script de veillée (script.md) en blocs : une couche/image + le texte dit pendant ce plan.
Usage : python -I Outils\\script_blocs.py Episodes\\<dossier>   → écrit <dossier>/blocs.json et affiche la liste.
Règles du script.md :
- une ligne qui commence par 🔥 / 🌫️ / 🌍 / 📜 ouvre un nouveau bloc (sa description sert à choisir l'image) ;
- les lignes « > » sont dites par le narrateur ; une ligne « > » vide = fin de paragraphe (pause longue « | ») ;
- une ligne *(silence …)* ajoute un silence après le bloc précédent ;
- les [#n] (renvois aux sources) et les *(…)* dans le texte sont retirés.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

COUCHES = {"🔥": "FEU", "🌫": "VISION", "🌍": "MONDE", "📜": "CARNET"}
dossier = Path(sys.argv[1])
lignes = (dossier / "script.md").read_text(encoding="utf-8").splitlines()
blocs, courant, chapitre = [], None, ""
for l in lignes:
    s = l.strip()
    if s.startswith("## "):
        parts = [p.strip() for p in s[3:].split("—")]
        chapitre = parts[1] if len(parts) > 2 else parts[0]
        if s.startswith("## À préparer") or s.startswith("## Mots expliqués"):
            break
        continue
    couche = next((v for k, v in COUCHES.items() if s.startswith(k)), None)
    if couche:
        courant = {"n": len(blocs) + 1, "chapitre": chapitre, "couche": couche, "desc": s.split("—", 1)[-1].strip(),
                   "texte": "", "silence_apres": 0.0}
        blocs.append(courant)
        continue
    if s.startswith("*(") and "silence" in s and blocs:
        m = re.search(r"(\d+(?:,\d+)?)\s*s", s)
        blocs[-1]["silence_apres"] = float(m.group(1).replace(",", ".")) if m else 1.0
        continue
    if s.startswith(">") and courant is not None:
        t = s[1:].strip()
        t = re.sub(r"\[#\d+\]", "", t)
        t = re.sub(r"\*\([^)]*\)\*", "", t).strip()
        if not t:
            if courant["texte"] and not courant["texte"].endswith("|"):
                courant["texte"] += " |"
            continue
        courant["texte"] = (courant["texte"] + " " + t).strip()

for b in blocs:
    b["texte"] = re.sub(r"\s+", " ", b["texte"]).strip().rstrip("|").strip()
    b["mots"] = len(b["texte"].replace("|", "").split())
(dossier / "blocs.json").write_text(json.dumps(blocs, ensure_ascii=False, indent=1), encoding="utf-8")
for b in blocs:
    print(f"{b['n']:3d} {b['couche']:6s} {b['mots']:3d} mots | {b['desc'][:55]}")
print("total mots :", sum(b["mots"] for b in blocs), "| blocs :", len(blocs))
