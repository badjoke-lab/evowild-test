"""Independent saved R5 reload and tail-only scope audit; never save sources."""
import bpy, bmesh, hashlib, json, struct, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'S_ZERO_CANDIDATE_REVISED_R4.blend'
TARGET=ROOT/sys.argv[sys.argv.index('--')+1]
OUT=ROOT/'evidence'/('VERIFY_'+TARGET.stem+'_RELOAD.json')
assert bpy.app.version==(4,3,2) and not OUT.exists()

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


hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE,TARGET]}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
before=snapshot()
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
old_body=[tuple(v.co) for v in body.data.vertices]
old_body_faces=[(tuple(p.vertices),p.material_index,p.use_smooth) for p in body.data.polygons]
old_objects=sorted(bpy.data.objects.keys())
old_tail_bounds={n: {'min':[min(v.co[i] for v in bpy.data.objects[n].data.vertices) for i in range(3)],
                    'max':[max(v.co[i] for v in bpy.data.objects[n].data.vertices) for i in range(3)]}
                 for n in before['meshes'] if n.startswith('TAIL_')}
bpy.ops.wm.open_mainfile(filepath=str(TARGET),load_ui=False)
after=snapshot()
assert old_objects==sorted(bpy.data.objects.keys())
changed=sorted(n for n in before['meshes'] if before['meshes'][n]!=after['meshes'][n])
assert changed==sorted([n for n in before['meshes'] if n.startswith('TAIL_')]+['S_ZERO_BODY_CONTINUOUS']),changed
unchanged=sorted(set(before['meshes'])-set(changed))
assert before['studio']==after['studio']
assert all(before['meshes'][n]['materials']==after['meshes'][n]['materials'] for n in before['meshes'])
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
assert old_body_faces==[(tuple(p.vertices),p.material_index,p.use_smooth) for p in body.data.polygons]
body_changes=[i for i,v in enumerate(body.data.vertices) if tuple(v.co)!=old_body[i]]
assert body_changes
assert all(old_body[i][0]>1.07 and old_body[i][2]>1.78-.75*(old_body[i][0]-1.12) for i in body_changes)
body_tree=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
records=[];roots={}
for ob in sorted(bpy.data.collections['S_ZERO_CREATURE'].objects,key=lambda o:o.name):
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    r={'name':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),
       'boundary_edges':sum(e.is_boundary for e in bm.edges),
       'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
       'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
       'loose_vertices':sum(not v.link_edges for v in bm.verts)}
    assert all(r[k]==0 for k in ['boundary_edges','nonmanifold_edges','degenerate_faces','loose_vertices']),r
    if ob.name.startswith('TAIL_'):
        bvh=BVHTree.FromObject(ob,bpy.context.evaluated_depsgraph_get())
        polys=[set(p.vertices) for p in ob.data.polygons]
        pairs=set(tuple(sorted(pair)) for pair in bvh.overlap(bvh) if pair[0]!=pair[1] and not polys[pair[0]]&polys[pair[1]])
        r['nonadjacent_self_overlap_candidates']=len(pairs)
        r['overlap_pairs']=sorted(pairs)[:30]
        r['absolute_volume']=abs(bm.calc_volume(signed=True))
        if ob.name.startswith('TAIL_BLADE_'):
            points=[v.co.copy() for v in ob.data.vertices[:8]]
            center=sum(points,Vector())/8
            p,n,index,distance=body_tree.find_nearest(center)
            signed=(center-p).dot(n)
            roots[ob.name]={'root_center':list(center),'distance_to_continuous_body':distance,
                            'signed_nearest_surface_distance':signed,
                            'root_center_inside_by_nearest_normal':signed<0,
                            'body_surface_overlap_candidates':len(bvh.overlap(body_tree))}
    bm.free();records.append(r)
protected={}
for name,entry in json.loads((ROOT/'evidence/R5_RECOVERY_START.json').read_text())['protected_artifacts'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['sha256'],name
    protected[name]=entry['sha256']
ref=ROOT.parent/'references/00_s_type_modeling_image_v1.png'
assert hashlib.sha256(ref.read_bytes()).hexdigest()==json.loads((ROOT/'evidence/R5_RECOVERY_START.json').read_text())['reference_sha256']
for p in [SOURCE,TARGET]:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name]
report={'blender':bpy.app.version_string,'reopened':str(TARGET.relative_to(ROOT)),
        'file_sha256':hashes,'mesh_count':len(records),'vertices':sum(r['vertices'] for r in records),
        'faces':sum(r['faces'] for r in records),'changed_meshes':changed,'unchanged_meshes':unchanged,
        'body_changed_vertex_indices':body_changes,'body_unchanged_vertices':len(old_body)-len(body_changes),
        'body_topology_material_assignments_shading_preserved':True,
        'all_objects_preserved':True,'nontail_meshes_unchanged':True,
        'studio_cameras_lights_materials_world_color_management_unchanged':True,
        'meshes':records,'tail_root_embedding':roots,'r4_tail_bounds':old_tail_bounds,
        'protected_file_sha256':protected,'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
        'armatures':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'actions':list(bpy.data.actions.keys()),
        'limits':'Roots use volumetric embedding, not welded topology. BVH and signed-nearest distances are diagnostic candidate tests only. No gait or PC/mobile runtime validation. REVISE.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R5_RELOAD',len(changed),'changed;',len(unchanged),'unchanged;',len(body_changes),'tail-body vertices;',len(protected),'old files preserved')
print('SELF_OVERLAP_CANDIDATES',[(r['name'],r['nonadjacent_self_overlap_candidates']) for r in records if r.get('nonadjacent_self_overlap_candidates')])
print('ROOT_CENTERS_OUTSIDE',[(n,r['signed_nearest_surface_distance']) for n,r in roots.items() if not r['root_center_inside_by_nearest_normal']])
