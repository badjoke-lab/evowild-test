"""Crop authored v4 parts; no repaint, warp, or pose interpolation.

The v3 contact geometry and six foot bitmaps are copied byte for byte.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

source = Path('docs/evidence/p-rig-v4-20261014/parts-source.png')
old = Path('public/concept/p-layered-v3')
out = Path('public/concept/p-layered-v4')
out.mkdir(parents=True, exist_ok=True)
atlas = json.loads((old/'atlas.json').read_text())
rgba = np.array(Image.open(source).convert('RGBA'))
labels, _ = ndimage.label(rgba[:, :, 3] > 12, np.ones((3, 3)))
items = []
for label, bounds in enumerate(ndimage.find_objects(labels), 1):
    if bounds is None or np.count_nonzero(labels[bounds] == label) < 1000:
        continue
    yy, xx = bounds
    pixels = rgba[bounds].copy()
    pixels[labels[bounds] != label] = 0
    items.append(([xx.start, yy.start, xx.stop-xx.start, yy.stop-yy.start], pixels))
assert len(items) == 6
pivots = {
    'fore-upper': {'a': [120, 55], 'b': [270, 292]},
    'fore-lower': {'a': [65, 42], 'b': [200, 260]},
    'fore-joint': {'center': [127, 103], 'width': 26},
    'hind-upper': {'a': [135, 65], 'b': [286, 341]},
    'hind-lower': {'a': [75, 45], 'b': [245, 298]},
}
for name, part in atlas['parts'].items():
    if 'foot' in name or 'paw' in name:
        (out/part['image']).write_bytes((old/part['image']).read_bytes())
old_body = atlas['parts']['body']
for name, (crop, pixels) in zip(['body', 'fore-upper', 'fore-lower', 'fore-joint', 'hind-upper', 'hind-lower'], items):
    if name == 'fore-joint':
        continue  # Authored study remains in the source; no joint patch is rendered.
    part = dict(crop=crop, image=name+'.png', **pivots.get(name, {}))
    if name == 'body':
        # Separate v3 physical source calibration from the new paint crop.
        part['jointCalibration'] = {key: old_body[key] for key in ['shoulder', 'hip']}
        part['jointCalibration']['width'] = old_body['crop'][2]
    Image.fromarray(pixels).save(out/part['image'])
    atlas['parts'][name] = part
for name in ['fore-joint', 'hind-joint']:
    atlas['parts'].pop(name, None)
    (out/(name+'.png')).unlink(missing_ok=True)
atlas['footAssetDirectory'] = 'concept/p-layered-v3/'
atlas['sources'] = [str(source), str(old/'atlas.json')]
atlas['notes'] = 'v4 authored chest/scapula and four muscle segments. No flat runtime end tint. v3 physical pivots, fixed bones, feet and sole calibration retained.'
(out/'atlas.json').write_text(json.dumps(atlas, indent=2)+'\n')
