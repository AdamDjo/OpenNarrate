"""Met le logo et la bannière d'une chaîne aux formats YouTube.
Usage (Python de la config « python_voix ») :
  python Outils/identite.py logo <image.png> <dossier_sortie>                 → avatar.jpg (800x800) + watermark.png (150x150, rond, transparent)
  python Outils/identite.py banniere <image.png> <sortie.jpg> "NOM" "phrase" [x_centre_texte]
La bannière fait 2560x1440 ; le texte reste dans la zone visible sur tous les écrans (1546x423 au centre).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import POLICE_PHRASE, POLICE_TITRES as POLICE_NOM

sys.stdout.reconfigure(encoding="utf-8")
BLEU, BLANC = (112, 208, 245), (250, 250, 248)
W, H = 2560, 1440
ZONE_Y0, ZONE_Y1 = 508, 931


def logo(source, dossier):
    dossier = Path(dossier)
    img = ImageOps.fit(Image.open(source).convert("RGB"), (800, 800), Image.LANCZOS)
    img.save(dossier / "avatar.jpg", "JPEG", quality=92, optimize=True)
    petit = img.resize((150, 150), Image.LANCZOS).convert("RGBA")
    masque = Image.new("L", (600, 600), 0)
    ImageDraw.Draw(masque).ellipse((6, 6, 594, 594), fill=255)
    petit.putalpha(masque.resize((150, 150), Image.LANCZOS))
    petit.save(dossier / "watermark.png")
    print("avatar.jpg, watermark.png →", dossier)


def texte(fond, txt, f, cx, y, couleur, bord):
    ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).text((cx + 3, y + 6), txt, font=f, fill=(0, 0, 0, 220), anchor="ms", stroke_width=bord, stroke_fill=(0, 0, 0, 220))
    fond.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(fond).text((cx, y), txt, font=f, fill=couleur + (255,), anchor="ms", stroke_width=bord, stroke_fill=(0, 0, 0, 255))


def banniere(source, sortie, nom, phrase, cx):
    img = ImageOps.fit(Image.open(source).convert("RGB"), (W, H), Image.LANCZOS).convert("RGBA")
    f_nom = ImageFont.truetype(str(POLICE_NOM), 150)
    f_phrase = ImageFont.truetype(str(POLICE_PHRASE), 54)
    try:
        f_phrase.set_variation_by_name("Bold")
    except (OSError, ValueError):
        pass
    milieu = (ZONE_Y0 + ZONE_Y1) // 2
    texte(img, nom, f_nom, cx, milieu + 20, BLEU, 7)
    texte(img, phrase, f_phrase, cx, milieu + 105, BLANC, 4)
    img.convert("RGB").save(sortie, "JPEG", quality=92, optimize=True)
    print(sortie, round(Path(sortie).stat().st_size / 1e6, 2), "Mo")


def banniere_avec_titre(source, sortie, decalage, phrase, cx, y):
    """Le nom est déjà dessiné dans l'image : on la décale vers la droite pour le garder dans la zone visible, et on ajoute la phrase."""
    img = ImageOps.fit(Image.open(source).convert("RGB"), (W, H), Image.LANCZOS)
    bord_g = ImageOps.mirror(img.crop((0, 0, min(int(decalage * 0.85), 170), H))).resize((decalage, H), Image.LANCZOS)  # jamais assez large pour attraper le nom
    fond = Image.new("RGBA", (W, H))
    fond.paste(img, (decalage, 0))
    fond.paste(bord_g, (0, 0))
    f = ImageFont.truetype(str(POLICE_PHRASE), 50)
    try:
        f.set_variation_by_name("Bold")
    except (OSError, ValueError):
        pass
    texte(fond, phrase, f, cx, y, (244, 233, 210), 4)
    fond.convert("RGB").save(sortie, "JPEG", quality=92, optimize=True)
    print(sortie, round(Path(sortie).stat().st_size / 1e6, 2), "Mo")


if __name__ == "__main__":
    if sys.argv[1] == "logo":
        logo(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "banniere_titre":
        banniere_avec_titre(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], int(sys.argv[6]), int(sys.argv[7]))
    else:
        banniere(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6]) if len(sys.argv) > 6 else W // 2)
