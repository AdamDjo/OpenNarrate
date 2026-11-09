"""Dessine les textes à l'écran d'une vidéo en PNG transparents 1920x1080 : grand nom net, contour franc, rien autour.
Usage (Python de la config « python_voix », qui a Pillow) : python Outils\\titres_png.py <dossier> <police.ttf>
Lit <dossier>/titres.json : [{"texte", "style": "ouverture"|"chapitre"|"fin", "sous"?, "couleur"?: [r, g, b]}] → écrit <dossier>/t0.png, t1.png…
Lit aussi <dossier>/theme.json s'il existe : le "theme_titres" de la vidéo.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
BLEU_ZONE = (112, 208, 245)   # couleur par défaut, à changer avec "theme_titres" dans montage_images.json
BLANC = (250, 250, 248)


def police(chemin, taille):
    f = ImageFont.truetype(chemin, taille)
    try:
        f.set_variation_by_name("Bold")
    except (OSError, ValueError):
        pass
    return f


def ecrire(fond, txt, chemin, taille, y, couleur, contour=(0, 0, 0), casse="majuscules"):
    """Texte centré, contour franc et petite ombre. Rétrécit tout seul s'il dépasse de l'écran."""
    if casse == "majuscules":
        txt = txt.upper()
    f = police(chemin, taille)
    while f.getlength(txt) > W - 160 and taille > 24:
        taille -= 2
        f = police(chemin, taille)
    bord = max(2, round(taille * 0.04))
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).text((W / 2 + 2, y + 4), txt, font=f, fill=contour + (200,), anchor="ms", stroke_width=bord, stroke_fill=contour + (200,))
    fond.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(fond).text((W / 2, y), txt, font=f, fill=couleur + (255,), anchor="ms", stroke_width=bord, stroke_fill=contour + (255,))


DEFAUT = {"ouverture": {"taille": 150, "y": 400, "taille_sous": 48, "y_sous": 485},
          "fin": {"taille": 150, "y": 400, "taille_sous": 48, "y_sous": 485},
          "chapitre": {"taille": 70, "y": 270}}


def dessiner(t, chemin, theme=None):
    """theme = "theme_titres" de montage_images.json : police (lue par le montage), couleur, couleur_sous, contour, casse,
    et pour chaque style ("ouverture", "chapitre", "fin") : taille, y, taille_sous, y_sous, couleur, couleur_sous."""
    theme = theme or {}
    style = t.get("style") if t.get("style") in DEFAUT else "chapitre"
    r = {**DEFAUT[style], **theme.get(style, {})}
    couleur = tuple(t.get("couleur") or r.get("couleur") or theme.get("couleur") or BLEU_ZONE)
    sous = tuple(r.get("couleur_sous") or theme.get("couleur_sous") or BLANC)
    contour = tuple(r.get("contour") or theme.get("contour") or (0, 0, 0))
    casse = r.get("casse") or theme.get("casse") or "majuscules"
    fond = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ecrire(fond, t["texte"], chemin, r["taille"], r["y"], couleur, contour, casse)
    if t.get("sous") and "taille_sous" in r:
        ecrire(fond, t["sous"], chemin, r["taille_sous"], r["y_sous"], sous, contour, casse)
    return fond


if __name__ == "__main__":
    dossier, chemin = Path(sys.argv[1]), sys.argv[2]
    fichier_theme = dossier / "theme.json"
    theme = json.loads(fichier_theme.read_text(encoding="utf-8")) if fichier_theme.exists() else {}
    for j, t in enumerate(json.loads((dossier / "titres.json").read_text(encoding="utf-8"))):
        dessiner(t, chemin, theme).save(dossier / f"t{j}.png")
