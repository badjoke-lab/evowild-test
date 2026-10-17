"""Lay out real render PNGs and reference crops; no generated/retouched geometry.
Requires Pillow in system Python. Only uniform resize, crop and labels are used.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'comparisons'
OUT.mkdir(exist_ok=True)
REF = ROOT.parent / 'references/00_s_type_modeling_image_v1.png'
VIEWS = ['SIDE', 'FRONT', 'FRONT34', 'REAR34', 'BACK']
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
    SMALL = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
except OSError:
    FONT = SMALL = ImageFont.load_default()
BG = '#edf1f5'
INK = '#152338'
sources = {}


def load(path):
    path = Path(path)
    sources[str(path.relative_to(ROOT.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')


def render(stage, view):
    return load(ROOT / 'renders' / stage / (view + '.png'))


def panel(canvas, picture, box, label):
    x, y, w, h = box
    ImageDraw.Draw(canvas).text((x + 10, y + 7), label, font=FONT, fill=INK)
    picture = ImageOps.contain(picture, (w - 12, h - 40))
    canvas.paste(picture, (x + (w - picture.width) // 2, y + 36 + (h - 40 - picture.height) // 2))


def save(im, name):
    path = OUT / name
    assert not path.exists(), path
    im.save(path)
    print(path, im.size)


for stage, title in [('candidate_review', 'CANDIDATE'), ('revised_r1', 'REVISED R1')]:
    canvas = Image.new('RGB', (1800, 1000), BG)
    for i, view in enumerate(VIEWS):
        panel(canvas, render(stage, view), (i % 3 * 600, i // 3 * 500, 600, 500), title + ' / ' + view)
    panel(canvas, load(REF), (1200, 500, 600, 500), 'MODELING REFERENCE / original PNG')
    save(canvas, title.replace(' ', '_') + '_FIVE_VIEWS.png')

canvas = Image.new('RGB', (1440, 2850), BG)
for i, view in enumerate(VIEWS):
    panel(canvas, render('candidate_review', view), (0, i * 570, 720, 570), 'BEFORE / ' + view)
    panel(canvas, render('revised_r1', view), (720, i * 570, 720, 570), 'AFTER R1 / ' + view)
save(canvas, 'BEFORE_AFTER_FIVE_VIEWS.png')

# Coordinates are explicit crops of the original 1448 x 1086 reference sheet.
reference = load(REF)
assert reference.size == (1448, 1086), reference.size
crops = {'SIDE': (30, 72, 755, 514), 'FRONT': (765, 86, 948, 513),
         'FRONT34': (1130, 83, 1434, 513), 'BACK': (950, 86, 1125, 513)}
canvas = Image.new('RGB', (1800, 2100), BG)
for i, (view, crop) in enumerate(crops.items()):
    panel(canvas, reference.crop(crop), (0, i * 520, 600, 520), 'REFERENCE / ' + view)
    panel(canvas, render('candidate_review', view), (600, i * 520, 600, 520), 'CANDIDATE / ' + view)
    panel(canvas, render('revised_r1', view), (1200, i * 520, 600, 520), 'REVISED R1 / ' + view)
ImageDraw.Draw(canvas).text((12, 2080), 'Reference crops and real renders; uniform fit per panel. Reference pose/camera are not an exact registration.', font=SMALL, fill=INK)
save(canvas, 'REFERENCE_COMPARISON.png')

canvas = Image.new('RGB', (1800, 1410), BG)
regions = [('SIDE', (325, 315, 640, 570), 'SHOULDER / UPPER ARM'),
           ('FRONT34', (350, 300, 700, 610), 'SHOULDER / 3D CONNECTION'),
           ('SIDE', (670, 315, 900, 600), 'PELVIS / THIGH')]
for row, (view, crop, title) in enumerate(regions):
    for col, (stage, label) in enumerate([('refined', 'REFINED'), ('candidate_review', 'CANDIDATE'), ('revised_r1', 'REVISED R1')]):
        panel(canvas, render(stage, view).crop(crop), (col * 600, row * 470, 600, 470), label + ' / ' + title)
save(canvas, 'SHOULDER_HIP_PROGRESS.png')

canvas = Image.new('RGB', (1200, 220), BG)
d = ImageDraw.Draw(canvas)
d.text((12, 8), 'Static previews: rendered frame height 128 px. Gait / PC / mobile runtime untested.', font=FONT, fill=INK)
for i, (stage, view) in enumerate([('candidate_review', 'SIDE'), ('revised_r1', 'SIDE'), ('candidate_review', 'FRONT'), ('revised_r1', 'FRONT')]):
    im = render(stage, view)
    im = im.resize((171, 128), Image.Resampling.LANCZOS)
    canvas.paste(im, (i * 300 + 60, 45))
    d.text((i * 300 + 12, 184), ('BEFORE' if stage == 'candidate_review' else 'R1') + ' / ' + view, font=FONT, fill=INK)
save(canvas, 'STATIC_128PX_PREVIEW.png')

(ROOT / 'evidence/COMPARISON_SOURCES.json').write_text(json.dumps({
    'method': 'Real Blender renders and unaltered reference crops. Uniform image resize and labels only.',
    'reference_crops': crops, 'detail_crops': regions, 'source_sha256': sources}, indent=2) + '\n')
