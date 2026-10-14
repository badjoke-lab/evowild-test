"""Unretouched crops of the locked canonical sheet for Blender alignment."""
from pathlib import Path
from PIL import Image
import hashlib, json

ROOT = Path(__file__).resolve().parents[3]
STATION = ROOT / 'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
OUT = STATION / 'review-v4'
REF = ROOT / 'art/s-creature/references/00_s_type_modeling_image_v1.png'
assert hashlib.sha256(REF.read_bytes()).hexdigest() == '93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
OUT.mkdir(exist_ok=True)
im = Image.open(REF)
boxes = {'SIDE': (60, 73, 750, 507), 'FRONT': (796, 102, 926, 507), 'BACK': (977, 102, 1108, 507), 'FRONT34': (1143, 89, 1426, 506)}
for tag, box in boxes.items():
    im.crop(box).save(OUT / ('CANONICAL_CROP_' + tag + '.png'))
(OUT / 'REFERENCE_CROPS.json').write_text(json.dumps({'source':str(REF.relative_to(ROOT)), 'source_size':im.size,'boxes':boxes,'method':'pixel crop only; no repainting or resampling'},indent=2)+'\n')
