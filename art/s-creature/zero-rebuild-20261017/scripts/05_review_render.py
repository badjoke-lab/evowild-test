"""Render an explicitly saved verification/revision file, never an original input.
Blender -b FILE --python-exit-code 1 --python THIS -- LABEL [VIEW ...]
Output paths must be new. Lighting and camera matrices remain unchanged.
"""
import bpy
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assert bpy.app.version == (4, 3, 2)
source = Path(bpy.data.filepath)
assert source.name not in ['S_ZERO_BLOCKOUT.blend', 'S_ZERO_REFINED.blend', 'S_ZERO_CANDIDATE.blend']
args = sys.argv[sys.argv.index('--') + 1:]
label = args[0]
views = args[1:] or ['SIDE', 'FRONT', 'FRONT34', 'REAR34', 'BACK']
out = ROOT / 'renders' / label
out.mkdir(parents=True, exist_ok=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 32
sc.cycles.seed = 17
sc.cycles.use_denoising = True
sc.render.resolution_x = 1200
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
meta = {'source': str(source.relative_to(ROOT)), 'source_sha256': source_hash,
        'blender': bpy.app.version_string, 'engine': sc.render.engine,
        'samples': sc.cycles.samples, 'seed': sc.cycles.seed,
        'resolution': [1200, 900], 'view_transform': sc.view_settings.view_transform,
        'look': sc.view_settings.look, 'views': {}}
for view in views:
    target = out / (view + '.png')
    assert not target.exists(), f'Refusing to overwrite {target}'
    sc.camera = bpy.data.objects['CAM_' + view]
    sc.render.filepath = str(target)
    start = time.time()
    bpy.ops.render.render(write_still=True)
    meta['views'][view] = {
        'file': str(target.relative_to(ROOT)),
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'camera_matrix': [list(row) for row in sc.camera.matrix_world],
        'ortho_scale': sc.camera.data.ortho_scale,
        'seconds': time.time() - start,
    }
    (ROOT / 'evidence' / ('RENDER_' + label + '.json')).write_text(json.dumps(meta, indent=2) + '\n')
    print('REVIEW_RENDER', label, view, flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
print('REVIEW_RENDER_COMPLETE', label, flush=True)
