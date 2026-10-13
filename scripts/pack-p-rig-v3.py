"""Extract the v3 authored joint/limb kit. v2 assets and contact calibration stay intact."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

source = Path('docs/evidence/p-rig-v3-20261013/parts-source.png')
original = Path('public/concept/p-layered')
out = Path('public/concept/p-layered-v3')
out.mkdir(parents=True, exist_ok=True)
manifest = json.loads((original/'atlas.json').read_text())
rgba = np.array(Image.open(source).convert('RGBA'))
labels, _ = ndimage.label(rgba[:, :, 3] > 12, np.ones((3, 3)))
items = []
for label, bounds in enumerate(ndimage.find_objects(labels), 1):
    if bounds is None or np.count_nonzero(labels[bounds] == label) < 1000:
        continue
    yy, xx = bounds
    pixels = rgba[bounds].copy()
    pixels[labels[bounds] != label] = 0
    items.append({'crop': [xx.start, yy.start, xx.stop-xx.start, yy.stop-yy.start], 'pixels': pixels})
assert len(items) == 8
pivots = {
    'fore-upper': {'a': [155, 50], 'b': [240, 353]},
    'fore-lower': {'a': [120, 40], 'b': [186, 346]},
    'hind-upper': {'a': [165, 68], 'b': [305, 380]},
    'hind-lower': {'a': [107, 42], 'b': [169, 377]},
    'fore-joint': {'center': [119, 104], 'width': 24},
    'hind-joint': {'center': [120, 111], 'width': 24},
}
for name in ['body', 'fore-foot', 'hind-foot']:
    # The torso and the two physics/contact definitions are byte-identical v2.
    (out/manifest['parts'][name]['image']).write_bytes((original/manifest['parts'][name]['image']).read_bytes())
for kind, row in [('fore', [p for p in items if p['crop'][1] < 500]),
                  ('hind', [p for p in items if p['crop'][1] >= 500])]:
    assert len(row) == 4
    for suffix, item in zip(['upper', 'lower', 'joint', 'far-paw'], sorted(row, key=lambda p: p['crop'][0])):
        name = f'{kind}-{suffix}'
        pixels = item.pop('pixels')
        part = dict(item, image=name+'.png', **pivots.get(name, {}))
        if suffix == 'far-paw':
            opaque = pixels[:, :, 3] > 128
            bottom = int(np.nonzero(opaque)[0].max())
            _, xs = np.nonzero(opaque[bottom-1:bottom+1])
            part.update(sole=[float(np.mean(xs+.5)), bottom+1], width=46)
            # A single rigid visual calibration, not a new contact/IK offset.
            physical = manifest['parts'][kind+'-foot']
            ratio = physical['width']/physical['crop'][2] / (part['width']/part['crop'][2])
            part['ankle'] = [part['sole'][i]+(physical['ankle'][i]-physical['sole'][i])*ratio for i in range(2)]
        Image.fromarray(pixels).save(out/part['image'])
        manifest['parts'][name] = part
# Near paws retain the three visible toes of the first authored pass.
near_source = Path('docs/evidence/p-rig-v3-20261013/near-paw-source.png')
for kind, crop in [('fore', [1177,146,359,243]), ('hind',[1183,647,357,252])]:
    x,y,w,h = crop
    pixels = np.array(Image.open(near_source).convert('RGBA').crop((x,y,x+w,y+h)))
    bottom = int(np.nonzero(pixels[:,:,3]>128)[0].max())
    _, xs = np.nonzero(pixels[bottom-1:bottom+1,:,3]>128)
    part = {'crop':crop,'image':kind+'-paw.png','sole':[float(np.mean(xs+.5)),bottom+1],'width':46}
    physical = manifest['parts'][kind+'-foot']
    ratio = physical['width']/physical['crop'][2] / (part['width']/w)
    part['ankle'] = [part['sole'][i]+(physical['ankle'][i]-physical['sole'][i])*ratio for i in range(2)]
    Image.fromarray(pixels).save(out/part['image'])
    manifest['parts'][kind+'-paw'] = part
manifest['sources'] = [str(source), str(near_source), 'public/concept/p-layered/atlas.json']
manifest['notes'] = 'v3 materials only. v2 body, foot-contact calibration, bones and frame retained. Authored slate joint skins and separate near/far paws; fixed runtime end-material blend. No per-frame warp or bone scaling.'
(out/'atlas.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({name: part for name, part in manifest['parts'].items() if name.endswith('paw')}))
