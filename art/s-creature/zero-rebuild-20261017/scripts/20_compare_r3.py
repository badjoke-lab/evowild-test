"""Lay out real render pixels and canonical crops. No retouching or warping."""
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LABEL = sys.argv[1]
VIEWS = ['SIDE', 'FRONT', 'FRONT34', 'REAR34', 'BACK']
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 23)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
sources = {}
outputs = []


def read(path):
    sources[str(path.relative_to(ROOT.parent))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return Image.open(path).convert('RGB')


def render(stage, view):
    return read(ROOT / 'renders' / stage / (view + '.png'))


def panel(canvas, picture, x, y, w, h, label):
    ImageDraw.Draw(canvas).text((x + 12, y + 9), label, font=font, fill='#162435')
    im = ImageOps.contain(picture, (w - 16, h - 44))
    canvas.paste(im, (x + (w - im.width) // 2, y + 40 + (h - 44 - im.height) // 2))


def save(canvas, suffix):
    path = ROOT / 'comparisons' / (LABEL.upper() + '_' + suffix + '.png')
    assert not path.exists(), path
    canvas.save(path)
    outputs.append(str(path.relative_to(ROOT)))
    print(path)


ref = read(ROOT.parent / 'references/00_s_type_modeling_image_v1.png')
title = LABEL.upper().replace('_', ' ')
crops = {'SIDE': (30, 72, 755, 514), 'FRONT': (765, 86, 948, 513),
         'FRONT34': (1130, 83, 1434, 513)}
canvas = Image.new('RGB', (1800, 1530), '#edf1f5')
for row, (view, crop) in enumerate(crops.items()):
    panel(canvas, ref.crop(crop), 0, row * 500, 600, 500, 'REFERENCE / ' + view)
    panel(canvas, render('r2_recovery', view), 600, row * 500, 600, 500, 'R2 / ' + view)
    panel(canvas, render(LABEL, view), 1200, row * 500, 600, 500, title + ' / ' + view)
ImageDraw.Draw(canvas).text((12, 1507), 'Actual Blender renders; unchanged cameras and lighting. Reference illustration pose/projection differs.', font=small, fill='#162435')
save(canvas, 'REFERENCE_R2_COMPARISON')

regions = [('SIDE', (220, 670, 565, 805)), ('FRONT', (490, 740, 710, 875)),
           ('FRONT34', (260, 730, 700, 895))]
canvas = Image.new('RGB', (1800, 1130), '#edf1f5')
for i, (view, crop) in enumerate(regions):
    panel(canvas, render('r2_recovery', view).crop(crop), i * 600, 0, 600, 400, 'R2 / ' + view + ' FEET')
    panel(canvas, render(LABEL, view).crop(crop), i * 600, 400, 600, 400, title + ' / ' + view + ' FEET')
panel(canvas, ref.crop((748, 664, 1065, 869)), 0, 800, 900, 330, 'CANONICAL FOOT STRUCTURE')
panel(canvas, ref.crop((190, 418, 397, 509)), 900, 800, 900, 330, 'CANONICAL STANCE / CONTACT')
save(canvas, 'FOOT_DETAILS')

if all((ROOT / 'renders' / LABEL / (view + '.png')).exists() for view in VIEWS):
    canvas = Image.new('RGB', (1800, 1000), '#edf1f5')
    for i, view in enumerate(VIEWS):
        panel(canvas, render(LABEL, view), i % 3 * 600, i // 3 * 500, 600, 500, title + ' / ' + view)
    panel(canvas, ref, 1200, 500, 600, 500, 'CANONICAL MODELING REFERENCE')
    save(canvas, 'FIVE_VIEWS')
    canvas = Image.new('RGB', (1440, 2850), '#edf1f5')
    for i, view in enumerate(VIEWS):
        panel(canvas, render('r2_recovery', view), 0, i * 570, 720, 570, 'R2 / ' + view)
        panel(canvas, render(LABEL, view), 720, i * 570, 720, 570, title + ' / ' + view)
    save(canvas, 'R2_FIVE_VIEW_COMPARISON')
    canvas = Image.new('RGB', (900, 400), '#edf1f5')
    for row, stage in enumerate(['r2_recovery', LABEL]):
        for i, view in enumerate(VIEWS):
            picture = render(stage, view).resize((171, 128), Image.Resampling.LANCZOS)
            canvas.paste(picture, (i * 180, row * 190 + 48))
            ImageDraw.Draw(canvas).text((i * 180 + 4, row * 190 + 8), ('R2' if row == 0 else 'R3') + ' / ' + view, font=small, fill='#162435')
    save(canvas, 'STATIC_128PX')

path = ROOT / 'evidence' / ('COMPARISON_' + LABEL + '.json')
assert not path.exists()
path.write_text(json.dumps({'method': 'Unretouched real render pixels; crops, proportional resizing and labels only.',
                           'reference_crops': crops, 'detail_crops': regions,
                           'source_sha256': sources, 'outputs': outputs}, indent=2) + '\n')
