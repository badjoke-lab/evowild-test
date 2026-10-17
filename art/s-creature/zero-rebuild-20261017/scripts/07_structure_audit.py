"""Assembly contact diagnostics; overlap counts are not automatic defect counts."""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
label = sys.argv[sys.argv.index('--') + 1]
out = ROOT / 'evidence' / ('STRUCTURE_' + label + '.json')
assert not out.exists()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
body_bvh = BVHTree.FromObject(body, depsgraph)
records = []
names = ['DELTOID_N', 'DELTOID_F', 'BRACHIAL_FORE_NEAR', 'BRACHIAL_FORE_FAR',
         'PELVIS_N', 'PELVIS_F', 'SCAPULA_N', 'SCAPULA_F', 'RIB_SHELL_N',
         'RIB_SHELL_F', 'LOWER_RIB_N', 'LOWER_RIB_F', 'DORSAL_MANTLE', 'SACRAL_MANTLE']
for name in names:
    obj = bpy.data.objects.get(name)
    if not obj:
        continue
    bvh = BVHTree.FromObject(obj, depsgraph)
    polygons = [set(p.vertices) for p in obj.data.polygons]
    candidates = set(tuple(sorted(pair)) for pair in bvh.overlap(bvh)
                     if pair[0] != pair[1] and not (polygons[pair[0]] & polygons[pair[1]]))
    pairs = bvh.overlap(body_bvh)
    distance = min(body_bvh.find_nearest(v.co)[3] for v in obj.data.vertices)
    records.append({'name': name, 'body_intersecting_face_pairs': len(pairs),
                    'min_vertex_to_body_distance': distance,
                    'nonadjacent_self_overlap_pairs': len(candidates)})
report = {'source': bpy.data.filepath, 'label': label, 'records': records,
          'interpretation': 'BVH triangle overlap is a diagnostic, not a complete robust self-intersection proof. Separate overlapping shell meshes remain separate during skin deformation. Zero boundary edges alone does not certify assembly.'}
out.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
