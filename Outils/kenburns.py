"""Zoom lent « Ken Burns » parfaitement fluide (sans vibration) calculé sur la carte graphique.
Pourquoi : le filtre zoompan de FFmpeg déplace l'image pixel par pixel → sur un zoom lent, l'image « tremble ». Ici chaque image est rééchantillonnée au sous-pixel (bicubique, PyTorch).

Usage (Python de la config « python_voix », qui a PyTorch + CUDA) :
  python Outils\\kenburns.py <image> <sortie.mp4> <duree_s> <z0> <z1> <cx> <cy> [largeur hauteur fps]
z = facteur de zoom (1.0 = image entière), cx/cy = point visé (0-1). Mouvement doux (ease in-out).
"""
import math
import subprocess
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from commun import FFMPEG
src, out, duree, z0, z1, cx, cy = sys.argv[1], sys.argv[2], *map(float, sys.argv[3:8])
W, H, FPS = (int(sys.argv[8]), int(sys.argv[9]), int(sys.argv[10])) if len(sys.argv) > 10 else (1920, 1080, 30)
dev = "cuda" if torch.cuda.is_available() else "cpu"

img = Image.open(src).convert("RGB")
# recadrage « cover » au format de sortie (comme force_original_aspect_ratio=increase + crop)
iw, ih = img.size
cible = W / H
if iw / ih > cible:
    nw = int(ih * cible); img = img.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
else:
    nh = int(iw / cible); img = img.crop((0, (ih - nh) // 2, iw, (ih - nh) // 2 + nh))
t = torch.from_numpy(np.asarray(img)).to(dev).permute(2, 0, 1).unsqueeze(0).float() / 255.0
# si l'image est plus petite que la sortie, on l'agrandit une fois (bicubique) pour garder du détail
if t.shape[-1] < W * 1.25:
    t = F.interpolate(t, size=(int(H * 1.25), int(W * 1.25)), mode="bicubic", align_corners=False).clamp(0, 1)

n = max(1, round(duree * FPS))
ys = torch.linspace(-1 + 1 / H, 1 - 1 / H, H, device=dev)
xs = torch.linspace(-1 + 1 / W, 1 - 1 / W, W, device=dev)
gy, gx = torch.meshgrid(ys, xs, indexing="ij")

enc = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "fast",
                        "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
with torch.no_grad():
    for i in range(n):
        e = (1 - math.cos(math.pi * min(i / max(n - 1, 1), 1))) / 2
        z = z0 + (z1 - z0) * e
        demi = 1 / (2 * z)                       # demi-largeur de la fenêtre visible (en 0-1)
        u = min(max(cx, demi), 1 - demi)         # le centre reste dans l'image
        v = min(max(cy, demi), 1 - demi)
        grille = torch.stack(((u * 2 - 1) + gx / z, (v * 2 - 1) + gy / z), dim=-1).unsqueeze(0)
        f = F.grid_sample(t, grille, mode="bicubic", padding_mode="border", align_corners=False)
        f = (f.clamp(0, 1)[0].permute(1, 2, 0) * 255).round().byte().cpu().numpy()
        enc.stdin.write(f.tobytes())
enc.stdin.close()
enc.wait()
print(out, n, "images")
