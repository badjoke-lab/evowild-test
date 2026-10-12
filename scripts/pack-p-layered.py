"""Extract authored cutouts by alpha component; no painting or pose warping.

Requires Pillow, NumPy and SciPy. Every output pixel comes from imagegen art.
Pivots describe rigid bones, never frame-dependent image scaling.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

out = Path('public/concept/p-layered')
evidence = Path('docs/evidence/p-layered-20261012')
out.mkdir(parents=True, exist_ok=True)

def components(path):
    rgba = np.array(Image.open(path).convert('RGBA'))
    labels, count = ndimage.label(rgba[:, :, 3] > 12, np.ones((3, 3)))
    items = []
    for label, bounds in enumerate(ndimage.find_objects(labels), 1):
        if bounds is None or np.count_nonzero(labels[bounds] == label) < 1000:
            continue
        yy, xx = bounds
        crop = rgba[bounds].copy()
        crop[labels[bounds] != label] = 0
        items.append({'crop': [xx.start, yy.start, xx.stop-xx.start, yy.stop-yy.start], 'rgba': crop})
    return items

core = sorted(components(evidence/'parts-source.png'), key=lambda p: p['crop'][1])
lowers = sorted(components(evidence/'lower-parts-source.png'), key=lambda p: p['crop'][0])
assert len(core) == 7 and len(lowers) == 2
names = ['body', 'fore-upper', 'fore-lower', 'fore-foot', 'hind-upper', 'hind-lower', 'hind-foot']
parts = dict(zip(names, core))
parts['fore-lower'], parts['hind-lower'] = lowers
pivots = {
    'body': {'shoulder': [806, 277], 'hip': [423, 283]},
    'fore-upper': {'a': [55, 24], 'b': [154, 216]},
    'fore-lower': {'a': [125, 90], 'b': [155, 1045]},
    'fore-foot': {'ankle': [39, 25], 'width': 48},
    'hind-upper': {'a': [82, 38], 'b': [184, 269]},
    'hind-lower': {'a': [110, 90], 'b': [180, 1045]},
    'hind-foot': {'ankle': [47, 33], 'width': 48}
}
for name, part in parts.items():
    rgba = part.pop('rgba')
    if name.endswith('-foot'):
        opaque = rgba[:, :, 3] > 128
        bottom = int(np.nonzero(opaque)[0].max())
        ys, xs = np.nonzero(opaque[max(0, bottom-1):bottom+1])
        part['sole'] = [float(np.mean(xs + .5)), bottom+1]
    part.update(pivots[name])
    part['image'] = name+'.png'
    Image.fromarray(rgba).save(out/part['image'])

manifest = {'sources': ['parts-source.png', 'lower-parts-source.png'], 'parts': parts,
            'body': {'x': 34, 'y': 27, 'width': 350},
            'frame': {'width': 416, 'height': 320, 'ground': 296},
            'notes': 'Immutable torso plus six rigid cutouts; alpha-component extraction removes unrelated overlapping bounding-box pixels. No frame interpolation or per-frame art scaling.'}
(out/'atlas.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({name: part['crop'] for name, part in parts.items()}))
