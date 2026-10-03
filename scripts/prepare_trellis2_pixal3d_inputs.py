#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "art/s-creature/experiments/trellis2-pixal3d/prepared"
OUT.mkdir(parents=True, exist_ok=True)

def padded_crop(src, box, name):
    im = Image.open(src).convert("RGB")
    crop = im.crop(box)
    # Normalize to a square without changing morphology.
    side = max(crop.size)
    canvas = Image.new("RGB", (side, side), "white")
    canvas.paste(crop, ((side-crop.width)//2, (side-crop.height)//2))
    canvas = canvas.resize((1024,1024), Image.Resampling.LANCZOS)
    path = OUT / name
    canvas.save(path, optimize=True)
    return path

primary = ROOT / "art/s-creature/references/01_s_body_primary.png"
silhouette = ROOT / "art/s-creature/references/02_s_silhouette.png"

# Pure crop/pad candidates. No repainting, inpainting or shape edits.
candidates = [
    (primary, (0, 25, 210, 245), "primary_crop_a.png"),
    (primary, (8, 32, 205, 238), "primary_crop_b.png"),
    (primary, (12, 38, 210, 242), "primary_crop_c.png"),
    (silhouette, (28, 42, 225, 275), "silhouette_crop_a.png"),
]

paths = [padded_crop(*c) for c in candidates]

# Contact sheet for review only.
thumbs=[]
for p in paths:
    im=Image.open(p).convert("RGB").resize((420,420), Image.Resampling.LANCZOS)
    canvas=Image.new("RGB",(420,455),"white")
    canvas.paste(im,(0,35))
    ImageDraw.Draw(canvas).text((8,8),p.name,fill="black")
    thumbs.append(canvas)
sheet=Image.new("RGB",(840,910),(235,235,235))
for i,im in enumerate(thumbs):
    sheet.paste(im,((i%2)*420,(i//2)*455))
sheet.save(OUT/"prepared_contact.png", optimize=True)

print("Prepared:")
for p in paths:
    print(p.relative_to(ROOT))
