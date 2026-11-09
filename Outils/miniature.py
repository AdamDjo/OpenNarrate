"""Pose le texte d'une miniature YouTube sur une image (1280x720, JPEG de moins de 2 Mo).
Usage (Python de la config « python_voix ») : python Outils/miniature.py <image> <sortie.jpg> "LIGNE 1" ["LIGNE 2"]
Trois mots maximum si possible : texte énorme, à gauche, contour noir épais, lisible en tout petit.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import POLICE_TITRES as POLICE

W, H, MARGE = 1280, 720, 44
LARGEUR_MAX = 620
BLANC, BLEU = (255, 255, 255), (112, 208, 245)


def taille_pour(txt):
    t = 170
    while t > 40 and ImageFont.truetype(str(POLICE), t).getlength(txt) > LARGEUR_MAX:
        t -= 2
    return t


def main():
    source, sortie, *lignes = sys.argv[1:]
    img = ImageOps.fit(Image.open(source).convert("RGB"), (W, H), Image.LANCZOS).convert("RGBA")
    # voile sombre à gauche pour détacher le texte, quelle que soit l'image
    voile = Image.new("L", (W, 1))
    voile.putdata([int(175 * max(0, 1 - x / (W * 0.62))) for x in range(W)])
    img.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (0, 0), voile.resize((W, H)))
    y = MARGE
    for i, ligne in enumerate(lignes):
        ligne = ligne.upper()
        t = taille_pour(ligne)
        f = ImageFont.truetype(str(POLICE), t)
        bord = max(5, round(t * 0.075))
        ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).text((MARGE + 6, y + 8), ligne, font=f, fill=(0, 0, 0, 230), stroke_width=bord, stroke_fill=(0, 0, 0, 230))
        img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(7)))
        ImageDraw.Draw(img).text((MARGE, y), ligne, font=f, fill=(BLANC if i == 0 else BLEU) + (255,), stroke_width=bord, stroke_fill=(0, 0, 0, 255))
        y += int(t * 1.12)
    img.convert("RGB").save(sortie, "JPEG", quality=90, optimize=True)
    print(sortie, round(Path(sortie).stat().st_size / 1e6, 2), "Mo")


main()
