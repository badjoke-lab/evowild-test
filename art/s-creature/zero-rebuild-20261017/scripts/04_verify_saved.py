"""Read-only Blender 4.3.2 verification. Never saves or mutates an input .blend."""
import bpy
import bmesh
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
assert bpy.app.version == (4, 3, 2), bpy.app.version_string


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path):
    before = sha(path)
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
    model = bpy.data.collections['S_ZERO_CREATURE']
    records = []
    for obj in sorted(model.all_objects, key=lambda x: x.name):
        if obj.type != 'MESH':
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        unseen = set(bm.verts)
        sizes = []
        while unseen:
            seed = unseen.pop()
            stack = [seed]
            size = 0
            while stack:
                v = stack.pop()
                size += 1
                for e in v.link_edges:
                    other = e.other_vert(v)
                    if other in unseen:
                        unseen.remove(other)
                        stack.append(other)
            sizes.append(size)
        records.append({
            'name': obj.name, 'vertices': len(bm.verts), 'faces': len(bm.faces),
            'boundary_edges': sum(e.is_boundary for e in bm.edges),
            'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
            'loose_vertices': sum(not v.link_edges for v in bm.verts),
            'degenerate_faces': sum(f.calc_area() < 1e-12 for f in bm.faces),
            'components': sorted(sizes, reverse=True),
            'vertex_groups': [g.name for g in obj.vertex_groups],
            'modifiers': [{'name': m.name, 'type': m.type} for m in obj.modifiers],
            'scale': list(obj.scale),
        })
        bm.free()
    after = sha(path)
    assert before == after, 'Input changed'
    return {
        'file': path.name, 'bytes': path.stat().st_size,
        'sha256': before, 'sha256_after': after, 'opened': True,
        'blender': bpy.app.version_string, 'stage': bpy.context.scene.get('stage'),
        'collection_objects': len(model.all_objects), 'mesh_objects': len(records),
        'vertices': sum(r['vertices'] for r in records),
        'faces': sum(r['faces'] for r in records),
        'armatures': [o.name for o in bpy.data.objects if o.type == 'ARMATURE'],
        'actions': [a.name for a in bpy.data.actions],
        'cameras': [o.name for o in bpy.data.objects if o.type == 'CAMERA'],
        'external_images': [{'name': im.name, 'path': im.filepath, 'packed': bool(im.packed_file)}
                            for im in bpy.data.images if im.source == 'FILE'],
        'meshes': records,
    }


args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
paths = [Path(p).resolve() for p in args] if args else [ROOT / ('S_ZERO_' + s + '.blend') for s in ['BLOCKOUT', 'REFINED', 'CANDIDATE']]
report = {'utc': datetime.now(timezone.utc).isoformat(), 'read_only': True, 'files': []}
for path in paths:
    result = inspect(path)
    report['files'].append(result)
    print('VERIFIED', path.name, result['bytes'], result['sha256'], 'meshes', result['mesh_objects'], flush=True)
out = ROOT / 'evidence' / ('VERIFY_SAVED_ORIGINALS.json' if not args else 'VERIFY_' + paths[-1].stem + '.json')
assert not out.exists(), 'Do not overwrite verification evidence'
out.write_text(json.dumps(report, indent=2) + '\n')
print('VERIFICATION_COMPLETE', out, flush=True)
