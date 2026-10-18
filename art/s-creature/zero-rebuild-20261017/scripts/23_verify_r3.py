"""Reopen R2 and a saved R3 file; verify changed scope, studio and real meshes.

Blender -b --python THIS -- relative/path/to/file.blend
No input file is saved. Verification output paths must be new.
"""
import bpy
import bmesh
import hashlib
import json
import struct
import sys
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / 'S_ZERO_CANDIDATE_REVISED_R2.blend'
TARGET = ROOT / sys.argv[sys.argv.index('--') + 1]
OUT = ROOT / 'evidence' / ('VERIFY_' + TARGET.stem + '_RELOAD.json')
assert bpy.app.version == (4, 3, 2)
assert not OUT.exists()


def mesh_data(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in ob.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
        h.update(struct.pack('<I?', p.material_index, p.use_smooth))
    for row in ob.matrix_world:
        h.update(struct.pack('<4f', *row))
    for attr in ob.data.color_attributes:
        h.update(attr.name.encode())
        for element in attr.data:
            h.update(struct.pack('<4f', *element.color))
    topology = hashlib.sha256(repr((sorted(tuple(sorted(p.vertices)) for p in ob.data.polygons),
                                   sorted(tuple(sorted(e.vertices)) for e in ob.data.edges))).encode()).hexdigest()
    return {'sha256': h.hexdigest(), 'topology_sha256': topology,
            'vertices': len(ob.data.vertices), 'faces': len(ob.data.polygons),
            'materials': [m.name for m in ob.data.materials]}


def nodes(tree):
    if not tree:
        return None
    result = {}
    for n in tree.nodes:
        inputs = {}
        for i in n.inputs:
            if not hasattr(i, 'default_value'):
                continue
            v = i.default_value
            if isinstance(v, (str, float, int, bool)) or v is None:
                inputs[i.identifier] = v
            elif hasattr(v, '__len__'):
                inputs[i.identifier] = list(v)
        result[n.name] = {'type': n.type, 'inputs': inputs}
    return {'nodes': result,
            'links': sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in tree.links)}


def studio():
    records = {}
    for ob in bpy.data.collections['STUDIO'].objects:
        row = {'type': ob.type, 'matrix': [list(r) for r in ob.matrix_world]}
        if ob.type == 'MESH':
            row['mesh'] = mesh_data(ob)
        if ob.type == 'CAMERA':
            row.update({'projection': ob.data.type, 'ortho_scale': ob.data.ortho_scale, 'lens': ob.data.lens})
        if ob.type == 'LIGHT':
            row.update({'color': list(ob.data.color), 'energy': ob.data.energy, 'shape': ob.data.shape, 'size': ob.data.size})
        records[ob.name] = row
    s = bpy.context.scene
    records['color_management'] = [s.view_settings.view_transform, s.view_settings.look, s.view_settings.exposure, s.view_settings.gamma]
    records['world'] = nodes(s.world.node_tree)
    used_materials = {slot.material.name for ob in bpy.data.objects for slot in ob.material_slots if slot.material}
    records['materials'] = {m.name: {'diffuse': list(m.diffuse_color), 'nodes': nodes(m.node_tree)}
                            for m in bpy.data.materials if m.name in used_materials}
    return records


def snapshot():
    return {'meshes': {o.name: mesh_data(o) for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type == 'MESH'},
            'studio': studio(),
            'unassigned_materials': {m.name: m.users for m in bpy.data.materials
                if m.name not in {slot.material.name for ob in bpy.data.objects for slot in ob.material_slots if slot.material}}}


hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [R2, TARGET]}
bpy.ops.wm.open_mainfile(filepath=str(R2), load_ui=False)
before = snapshot()
r2_soles = {o.name: min(v.co.z for v in o.data.vertices) for o in bpy.data.objects
            if o.name.startswith(('TOE_FORE_', 'TOE_HIND_'))}
bpy.ops.wm.open_mainfile(filepath=str(TARGET), load_ui=False)
after = snapshot()
assert set(before['meshes']) == set(after['meshes'])
changed = sorted(n for n in before['meshes'] if before['meshes'][n] != after['meshes'][n])
unchanged = sorted(set(before['meshes']) - set(changed))
assert len(changed) == 44, changed
assert all(n.startswith(('TOE_', 'HOOF_FACE_', 'HOOF_SIGNAL_', 'ANKLE_FIN_')) for n in changed)
for n in before['meshes']:
    assert before['meshes'][n]['topology_sha256'] == after['meshes'][n]['topology_sha256'], n
    assert before['meshes'][n]['materials'] == after['meshes'][n]['materials'], n
if before['studio'] != after['studio']:
    diagnostic = ROOT / 'evidence' / ('STUDIO_DIAGNOSTIC_' + TARGET.stem + '.json')
    if not diagnostic.exists():
        diagnostic.write_text(json.dumps({'before': before['studio'], 'after': after['studio']}, indent=2) + '\n')
    print('STUDIO_DIFFERENCE', [k for k in set(before['studio']) | set(after['studio']) if before['studio'].get(k) != after['studio'].get(k)], flush=True)
assert before['studio'] == after['studio']
assert 'S_ZERO_BODY_CONTINUOUS' in unchanged
assert all(n in unchanged for n in before['meshes'] if n.startswith('CROWN_'))

records = []
soles = {}
for ob in sorted(bpy.data.collections['S_ZERO_CREATURE'].objects, key=lambda o: o.name):
    if ob.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    unseen = set(bm.verts)
    components = []
    while unseen:
        stack = [unseen.pop()]
        count = 0
        while stack:
            v = stack.pop()
            count += 1
            for e in v.link_edges:
                other = e.other_vert(v)
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
        components.append(count)
    r = {'name': ob.name, 'vertices': len(bm.verts), 'faces': len(bm.faces),
         'boundary_edges': sum(e.is_boundary for e in bm.edges),
         'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
         'degenerate_faces': sum(f.calc_area() < 1e-12 for f in bm.faces),
         'loose_vertices': sum(not v.link_edges for v in bm.verts),
         'components': sorted(components, reverse=True)}
    assert all(r[k] == 0 for k in ['boundary_edges', 'nonmanifold_edges', 'degenerate_faces', 'loose_vertices']), r
    if ob.name in changed or ob.name == 'S_ZERO_BODY_CONTINUOUS':
        bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
        polygons = [set(p.vertices) for p in ob.data.polygons]
        pairs = set(tuple(sorted(pair)) for pair in bvh.overlap(bvh)
                    if pair[0] != pair[1] and not (polygons[pair[0]] & polygons[pair[1]]))
        r['nonadjacent_self_overlap_candidates'] = len(pairs)
    if ob.name.startswith(('TOE_FORE_', 'TOE_HIND_')):
        sole_faces = [f for f in bm.faces if all(abs(v.co.z + .016) < 1e-6 for v in f.verts)]
        soles[ob.name] = {'r2_min_z': r2_soles[ob.name],
                          'r3_min_z': min(v.co.z for v in bm.verts),
                          'sole_faces': len(sole_faces),
                          'sole_area_model_units2': sum(f.calc_area() for f in sole_faces),
                          'ground_clearance_model_units': min(v.co.z for v in bm.verts) + .018}
        assert sole_faces and soles[ob.name]['sole_area_model_units2'] > .001
    bm.free()
    records.append(r)

protected = {}
manifest = json.loads((ROOT / 'evidence/R3_RECOVERY_START.json').read_text())
for p, entry in manifest['protected_artifacts'].items():
    if p.endswith('/QUALITY_REVIEW.md'):
        continue
    f = ROOT.parents[2] / p
    assert hashlib.sha256(f.read_bytes()).hexdigest() == entry['sha256'], p
    protected[p] = entry['sha256']
for p in [R2, TARGET]:
    assert hashlib.sha256(p.read_bytes()).hexdigest() == hashes[p.name]
report = {'blender': bpy.app.version_string, 'reopened': str(TARGET.relative_to(ROOT)),
          'file_sha256': hashes, 'mesh_count': len(records),
          'vertices': sum(r['vertices'] for r in records), 'faces': sum(r['faces'] for r in records),
          'changed_meshes': changed, 'unchanged_meshes': unchanged,
          'all_object_names_vertices_faces_connectivity_material_slots_preserved': True,
          'body_including_r2_shoulder_coordinates_and_color_attributes_exactly_unchanged': True,
          'all_crown_meshes_exactly_unchanged': True,
          'studio_cameras_lights_world_materials_color_management_unchanged': True,
          'studio_snapshot': after['studio'], 'meshes': records, 'toe_soles': soles,
          'unassigned_materials_before': before['unassigned_materials'],
          'unassigned_materials_after': after['unassigned_materials'],
          'protected_file_sha256': protected,
          'armatures': [o.name for o in bpy.data.objects if o.type == 'ARMATURE'],
          'actions': list(bpy.data.actions.keys()),
          'limits': 'BVH candidates are not a complete proof. Separate detail shells remain; no retopology, rig, gait or PC/mobile runtime validation. No production promotion.'}
OUT.write_text(json.dumps(report, indent=2) + '\n')
print('R3_RELOAD_VERIFIED', len(changed), 'changed;', len(unchanged), 'unchanged;', len(protected), 'preserved files')
print('SELF_OVERLAP_CANDIDATES', [(r['name'], r['nonadjacent_self_overlap_candidates']) for r in records if r.get('nonadjacent_self_overlap_candidates')])
