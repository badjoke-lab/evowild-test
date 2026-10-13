"""Extract the authored nine-part P kit; no warping or repainting."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

source = Path('docs/evidence/p-rig-v2-20261013/parts-source.png')
out = Path('public/concept/p-layered')
rgba = np.array(Image.open(source).convert('RGBA'))
labels, count = ndimage.label(rgba[:, :, 3] > 12, np.ones((3, 3)))
items = []
for label, bounds in enumerate(ndimage.find_objects(labels), 1):
    if bounds is None or np.count_nonzero(labels[bounds] == label) < 1000:
        continue
    yy, xx = bounds
    crop = rgba[bounds].copy()
    crop[labels[bounds] != label] = 0
    items.append({'crop': [xx.start, yy.start, xx.stop-xx.start, yy.stop-yy.start], 'rgba': crop})
assert len(items) == 9
body = max(items, key=lambda p: np.count_nonzero(p['rgba'][:, :, 3]))
others = [p for p in items if p is not body]
fore = sorted([p for p in others if p['crop'][1] < 885], key=lambda p: p['crop'][0])
hind = sorted([p for p in others if p['crop'][1] >= 885], key=lambda p: p['crop'][0])
assert len(fore) == len(hind) == 4
parts = {'body': body}
for kind, row in [('fore', fore), ('hind', hind)]:
    parts.update({f'{kind}-{name}': p for name, p in zip(['upper', 'lower', 'foot', 'joint'], row)})
pivots = {
    'body': {'shoulder': [755, 340], 'hip': [418, 364]},
    'fore-upper': {'a': [120, 40], 'b': [175, 284]},
    'fore-lower': {'a': [85, 30], 'b': [125, 280]},
    'fore-foot': {'ankle': [67, 34], 'width': 46},
    'hind-upper': {'a': [125, 55], 'b': [228, 292]},
    'hind-lower': {'a': [83, 35], 'b': [122, 308]},
    'hind-foot': {'ankle': [68, 58], 'width': 46},
    'fore-joint': {'center': [88, 100], 'width': 32},
    'hind-joint': {'center': [79, 96], 'width': 31},
}
for name, part in parts.items():
    pixels = part.pop('rgba')
    if name.endswith('-foot'):
        opaque = pixels[:, :, 3] > 128
        bottom = int(np.nonzero(opaque)[0].max())
        ys, xs = np.nonzero(opaque[max(0, bottom-1):bottom+1])
        part['sole'] = [float(np.mean(xs + .5)), bottom+1]
    part.update(pivots[name]); part['image'] = name+'.png'
    Image.fromarray(pixels).save(out/part['image'])
manifest = {'sources': [str(source)], 'parts': parts,
            'body': {'x': 50, 'y': 60, 'width': 316},
            'bones': {'fore': [70, 68], 'hind': [70, 68]},
            'frame': {'width': 416, 'height': 320, 'ground': 296},
            'notes': 'Short stout authored P parts, organic joint covers, fixed calibrated bones. No raster warp or per-frame scaling.'}
(out/'atlas.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({name: p['crop'] for name, p in parts.items()}))
