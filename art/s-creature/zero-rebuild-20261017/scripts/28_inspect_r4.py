"""Read the byte-identical R3 protection copy through live Blender MCP."""
import bpy
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'S_ZERO_CANDIDATE_REVISED_R3.blend'
COPY = ROOT / 'verification/S_ZERO_R4_WORKING_COPY.blend'
assert bpy.app.version == (4, 3, 2)
assert SOURCE.read_bytes() == COPY.read_bytes()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'b3e1b1820c3019a7b466b81e06276d8585fdeb25ec425ac2a6219e55bd06a916'
assert not bpy.data.is_dirty, 'Protect unsaved session before opening the copy'
bpy.ops.wm.open_mainfile(filepath=str(COPY), load_ui=False)
report = {'blender': bpy.app.version_string, 'opened': bpy.data.filepath,
          'is_dirty_after_open': bpy.data.is_dirty, 'stage': bpy.context.scene.get('stage'),
          'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'crowns': {}}
for ob in bpy.data.objects:
    if ob.name.startswith('CROWN_'):
        report['crowns'][ob.name] = {'vertices': [list(v.co) for v in ob.data.vertices],
                                   'polygons': [list(p.vertices) for p in ob.data.polygons],
                                   'matrix': [list(r) for r in ob.matrix_world],
                                   'modifiers': [m.type for m in ob.modifiers]}
out = ROOT / 'evidence/R4_OPENED_R3.json'
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + '\n')
print('R3_OPENED', report['blender'], report['stage'], report['is_dirty_after_open'])
print(json.dumps({n: {'v': len(r['vertices']), 'f': len(r['polygons']), 'vertices': r['vertices']} for n, r in report['crowns'].items()}))
