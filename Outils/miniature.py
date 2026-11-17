"""Pose le texte d'une miniature YouTube sur une image (1280x720, JPEG de moins de 2 Mo).
Usage (Python de la config « python_voix ») : python Outils/miniature.py <image> <sortie.jpg> "LIGNE 1" ["LIGNE 2"]
Options, pour reprendre le thème des titres de la vidéo :
  --police=Polices/X.ttf   --couleur=255,255,255 (ligne 1)   --couleur2=112,208,245 (ligne 2)
  --petit="RUINES DE LORDAERON" : ligne en petit sous le grand texte, qui dit de quoi parle la vidéo (nom du lieu, du donjon…).
  Règle de l'utilisateur (12 nov. 2026) : toujours un texte significatif sur le sujet, pas seulement une accroche.
  --graisse=Black : épaisseur d'une police variable (ex. Cinzel : Regular, Bold, Black). Black est bien plus accrocheur ;
    garder --largeur=480 pour que le texte reste gros sans manger l'image (une police Black à 640 était « trop grande »).
  --lueur=255,120,30 : halo coloré autour du grand texte (le fait ressortir sur un fond chargé).
  --largeur=760 : largeur max du grand texte (620 par défaut) ; un mot court (« RAID ») devient énorme.
Trois mots maximum si possible : texte énorme, à gauche, contour noir épais, lisible en tout petit.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import POLICE_TITRES, RACINE

W, H, MARGE = 1280, 720, 44
LARGEUR_MAX = 620
BLANC, BLEU = (255, 255, 255), (112, 208, 245)
POLICE = POLICE_TITRES


GRAISSE, LUEUR = None, None


def police(t):
    f = ImageFont.truetype(str(POLICE), t)
    if GRAISSE:
        f.set_variation_by_name(GRAISSE)
    return f


def taille_pour(txt, tmax=170):
    t = tmax
    while t > 40 and police(t).getlength(txt) > LARGEUR_MAX:
        t -= 2
    return t


def couleur(txt):
    return tuple(int(v) for v in txt.split(","))


def main():
    global POLICE, BLANC, BLEU, GRAISSE, LUEUR, LARGEUR_MAX
    petits = []
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for o in (a for a in sys.argv[1:] if a.startswith("--")):
        cle, _, val = o[2:].partition("=")
        if cle == "police":
            POLICE = RACINE / val
        elif cle == "couleur":
            BLANC = couleur(val)
        elif cle == "couleur2":
            BLEU = couleur(val)
        elif cle == "graisse":
            GRAISSE = val.encode()
        elif cle == "lueur":
            LUEUR = couleur(val)
        elif cle == "largeur":
            LARGEUR_MAX = int(val)
        elif cle == "petit":
            petits.append(val)
    source, sortie, *lignes = args
    img = ImageOps.fit(Image.open(source).convert("RGB"), (W, H), Image.LANCZOS).convert("RGBA")
    # voile sombre à gauche pour détacher le texte, quelle que soit l'image
    voile = Image.new("L", (W, 1))
    voile.putdata([int(175 * max(0, 1 - x / (W * 0.62))) for x in range(W)])
    img.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (0, 0), voile.resize((W, H)))
    y = MARGE
    for i, ligne in enumerate(lignes):
        ligne = ligne.upper()
        t = taille_pour(ligne, 230 if GRAISSE else 170)
        f = police(t)
        bord = max(5, round(t * 0.075))
        if LUEUR:  # halo coloré derrière le texte
            halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(halo).text((MARGE, y), ligne, font=f, fill=LUEUR + (255,), stroke_width=bord * 3, stroke_fill=LUEUR + (255,))
            img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(18)))
        ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).text((MARGE + 6, y + 8), ligne, font=f, fill=(0, 0, 0, 230), stroke_width=bord, stroke_fill=(0, 0, 0, 230))
        img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(7)))
        ImageDraw.Draw(img).text((MARGE, y), ligne, font=f, fill=(BLANC if i == 0 else BLEU) + (255,), stroke_width=bord, stroke_fill=(0, 0, 0, 255))
        y += int(t * 1.12)
    for ligne in petits:   # en petit, sous le grand texte : le sujet de la vidéo
        ligne = ligne.upper()
        t = min(60, taille_pour(ligne))
        f = police(t)
        bord = max(3, round(t * 0.09))
        y += 6
        ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).text((MARGE + 4, y + 5), ligne, font=f, fill=(0, 0, 0, 230), stroke_width=bord, stroke_fill=(0, 0, 0, 230))
        img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(5)))
        ImageDraw.Draw(img).text((MARGE, y), ligne, font=f, fill=BLANC + (255,), stroke_width=bord, stroke_fill=(0, 0, 0, 255))
        y += int(t * 1.2)
    img.convert("RGB").save(sortie, "JPEG", quality=90, optimize=True)
    print(sortie, round(Path(sortie).stat().st_size / 1e6, 2), "Mo")


main()
