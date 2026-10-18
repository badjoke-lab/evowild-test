"""Render closer views of the near forefoot without changing or saving a model.

Blender -b FILE --python THIS -- LABEL [SIDE FRONT FRONT34 REAR34]
Only a temporary camera is added. Original studio/light/material settings stay.
"""
import bpy
import hashlib
import json
import sys
import time
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
args = sys.argv[sys.argv.index('--') + 1:]
label = args[0]
views = args[1:] or ['SIDE', 'FRONT', 'FRONT34', 'REAR34']
source = Path(bpy.data.filepath)
source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
out = ROOT / 'renders' / label
out.mkdir(parents=True, exist_ok=True)
report_path = ROOT / 'evidence' / ('RENDER_' + label + '.json')
assert not report_path.exists()
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.seed = 17
scene.cycles.use_denoising = True
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
report = {'source': str(source.relative_to(ROOT)), 'source_sha256': source_hash,
          'blender': bpy.app.version_string, 'engine': 'CYCLES', 'samples': 32,
          'seed': 17, 'resolution': [900, 900],
          'method': 'Same studio and camera orientations; temporary camera translated/zoomed onto near forefoot; model not saved.',
          'views': {}}
for view in views:
    original = bpy.data.objects['CAM_' + view]
    camera = original.copy()
    camera.data = original.data.copy()
    scene.collection.objects.link(camera)
    camera.location += Vector((-.51, -.29, .205)) - Vector((.03, 0, 1.56))
    camera.data.ortho_scale = .67
    scene.camera = camera
    path = out / (view + '.png')
    assert not path.exists()
    scene.render.filepath = str(path)
    start = time.time()
    bpy.ops.render.render(write_still=True)
    report['views'][view] = {'file': str(path.relative_to(ROOT)),
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'camera_matrix': [list(row) for row in camera.matrix_world],
        'ortho_scale': camera.data.ortho_scale, 'seconds': time.time() - start}
    bpy.data.objects.remove(camera, do_unlink=True)
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('FOOT_RENDER', label, view, flush=True)
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
print('FOOT_RENDER_COMPLETE', label, flush=True)
