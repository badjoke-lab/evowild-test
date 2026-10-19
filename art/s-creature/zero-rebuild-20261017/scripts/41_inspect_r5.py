"""Open protected R4 copy through Blender MCP and record tail geometry."""
import bpy, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'S_ZERO_CANDIDATE_REVISED_R4.blend'
copy = ROOT / 'verification/S_ZERO_R5_WORKING_COPY.blend'
assert bpy.app.version == (4, 3, 2)
assert not bpy.data.is_dirty
assert source.read_bytes() == copy.read_bytes()
bpy.ops.wm.open_mainfile(filepath=str(copy), load_ui=False)
report = {'blender': bpy.app.version_string, 'opened': bpy.data.filepath,
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'stage': bpy.context.scene.get('stage'), 'meshes': {}}
for ob in bpy.data.collections['S_ZERO_CREATURE'].objects:
    if ob.name.startswith('TAIL_') or ob.name == 'S_ZERO_BODY_CONTINUOUS':
        report['meshes'][ob.name] = {
            'vertices': [list(v.co) for v in ob.data.vertices],
            'polygons': [list(p.vertices) for p in ob.data.polygons],
            'materials': [m.name for m in ob.data.materials],
            'matrix': [list(row) for row in ob.matrix_world],
            'modifiers': [m.type for m in ob.modifiers]}
out = ROOT / 'evidence/R5_OPENED_R4.json'
assert not out.exists()
out.write_text(json.dumps(report, indent=2) + '\n')
print('R4_OPENED', report['blender'], report['stage'])
for n, m in report['meshes'].items():
    print(n, len(m['vertices']), len(m['polygons']), m['materials'])
