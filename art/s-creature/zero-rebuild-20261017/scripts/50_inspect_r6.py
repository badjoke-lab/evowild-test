"""Capture R5's actual loaded structure before the R6 edit, via Blender MCP."""
import bpy, bmesh, json, hashlib, struct
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/R6_OPENED_R5.json'
assert bpy.app.version == (4, 3, 2) and not OUT.exists()
assert Path(bpy.data.filepath).name == 'S_ZERO_R6_WORKING_COPY.blend'
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest() == '87fd6732a682ece45733e1c9ad78861a6b2543259c5feae38ba506fe6a509923'
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
report = {'file': bpy.data.filepath, 'blender': bpy.app.version_string,
          'stage': bpy.context.scene.get('stage'), 'armatures': sum(o.type == 'ARMATURE' for o in bpy.data.objects),
          'actions': len(bpy.data.actions), 'objects': {},
          'assessment': 'Core is continuous, but both white pelvic volumes and sacral mantle are separate overlapping objects. Closed meshes are not evidence of articulation.'}
for name in ['S_ZERO_BODY_CONTINUOUS', 'PELVIS_N', 'PELVIS_F', 'SACRAL_MANTLE']:
    ob = bpy.data.objects[name]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    seen = set(); components = []
    for v in bm.verts:
        if v in seen: continue
        todo = [v]; seen.add(v); count = 0
        while todo:
            q = todo.pop(); count += 1
            for e in q.link_edges:
                w = e.other_vert(q)
                if w not in seen: seen.add(w); todo.append(w)
        components.append(count)
    report['objects'][name] = {'vertices': len(bm.verts), 'faces': len(bm.faces),
        'components': components, 'boundary_edges': sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
        'modifiers': [m.type for m in ob.modifiers],
        'coordinates': [list(v.co) for v in ob.data.vertices],
        'polygons': [list(p.vertices) for p in ob.data.polygons]}
    if ob != body:
        distances = []
        for v in ob.data.vertices:
            hit, normal, face, distance = tree.find_nearest(v.co)
            distances.append((v.co-hit).dot(normal))
        report['objects'][name]['signed_distance_to_core'] = {'min': min(distances), 'max': max(distances),
            'outside_vertices': sum(d > 0 for d in distances), 'inside_vertices': sum(d < 0 for d in distances)}
    bm.free()
OUT.write_text(json.dumps(report, indent=2)+'\n')
print('R5 structure captured:', {n:{k:v for k,v in r.items() if k not in ['coordinates','polygons']} for n,r in report['objects'].items()})
