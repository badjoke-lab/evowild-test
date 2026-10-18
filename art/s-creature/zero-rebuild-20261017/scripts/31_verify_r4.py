"""Independent R3/R4 reload audit. No source asset is saved or overwritten."""
import bpy, bmesh, hashlib, json, struct, sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'S_ZERO_CANDIDATE_REVISED_R3.blend'
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


def sections(ob):
    result={}
    me=ob.data
    for z in [2.20,2.28,2.42,2.60,2.82,3.02,3.08]:
        pts=[]
        for edge in me.edges:
            a,b=[me.vertices[i].co for i in edge.vertices]
            if min(a.z,b.z)<=z<=max(a.z,b.z) and abs(a.z-b.z)>1e-8:
                p=a.lerp(b,(z-a.z)/(b.z-a.z));pts.append(list(p))
        if pts:
            result[str(z)]={'x_span':max(p[0] for p in pts)-min(p[0] for p in pts),
                'y_span':max(p[1] for p in pts)-min(p[1] for p in pts),
                'y_min':min(p[1] for p in pts),'y_max':max(p[1] for p in pts)}
    return result

hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE,TARGET]}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
before=snapshot()
source_sections={o.name:sections(o) for o in bpy.data.objects if o.name.startswith('CROWN_MAIN_')}
source_outlines={o.name:[list(v.co) for v in o.data.vertices[:10] if v.co.z>=2.40]
                 for o in bpy.data.objects if o.name.startswith('CROWN_MAIN_')}
bpy.ops.wm.open_mainfile(filepath=str(TARGET),load_ui=False)
after=snapshot()
assert set(before['meshes'])==set(after['meshes'])
changed=sorted(n for n in before['meshes'] if before['meshes'][n]!=after['meshes'][n])
unchanged=sorted(set(before['meshes'])-set(changed))
assert changed==sorted('CROWN_'+part+'_'+side for part in ['MAIN','BLUE','IVORY_RIDGE'] for side in ['N','F']),changed
assert before['studio']==after['studio']
for n in before['meshes']:
    assert before['meshes'][n]['materials']==after['meshes'][n]['materials'],n
assert 'S_ZERO_BODY_CONTINUOUS' in unchanged
outline_checks={}
for name,points in source_outlines.items():
    verts=bpy.data.objects[name].data.vertices
    assert all(any(abs(v.co.x-p[0])<1e-6 and abs(v.co.z-p[2])<1e-6 for v in verts) for p in points),name
    outline_checks[name]={'preserved_xz_contour_vertices_above_root':len(points),'tolerance':1e-6}
records=[]
for ob in sorted(bpy.data.collections['S_ZERO_CREATURE'].objects,key=lambda o:o.name):
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    r={'name':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),
       'boundary_edges':sum(e.is_boundary for e in bm.edges),
       'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
       'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
       'loose_vertices':sum(not v.link_edges for v in bm.verts)}
    assert all(r[k]==0 for k in ['boundary_edges','nonmanifold_edges','degenerate_faces','loose_vertices']),r
    if ob.name in changed:
        bvh=BVHTree.FromObject(ob,bpy.context.evaluated_depsgraph_get())
        polys=[set(p.vertices) for p in ob.data.polygons]
        pairs=set(tuple(sorted(pair)) for pair in bvh.overlap(bvh) if pair[0]!=pair[1] and not polys[pair[0]]&polys[pair[1]])
        r['nonadjacent_self_overlap_candidates']=len(pairs)
        r['overlap_pairs']=sorted(pairs)[:30]
        r['absolute_volume']=abs(bm.calc_volume(signed=True))
    bm.free();records.append(r)
protected={}
for name,entry in json.loads((ROOT/'evidence/R4_RECOVERY_START.json').read_text())['protected_artifacts'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==entry['sha256'],name
    protected[name]=entry['sha256']
for p in [SOURCE,TARGET]:assert hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name]
report={'blender':bpy.app.version_string,'reopened':str(TARGET.relative_to(ROOT)),
        'file_sha256':hashes,'mesh_count':len(records),'vertices':sum(r['vertices'] for r in records),
        'faces':sum(r['faces'] for r in records),'changed_meshes':changed,'unchanged_meshes':unchanged,
        'noncrown_geometry_topology_material_slots_color_attributes_transforms_unchanged':True,
        'studio_cameras_lights_materials_world_color_management_unchanged':True,
        'source_sections':source_sections,'target_sections':{o.name:sections(o) for o in bpy.data.objects if o.name.startswith('CROWN_MAIN_')},
        'side_outline_checks':outline_checks,
        'meshes':records,'protected_file_sha256':protected,
        'armatures':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'actions':list(bpy.data.actions.keys()),
        'limits':'Separate detail shells and embedded roots are not welded topology or proof of rig suitability. BVH is a candidate test only. No gait or PC/mobile runtime validation. Overall REVISE.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R4_RELOAD',len(changed),'changed;',len(unchanged),'unchanged;',len(protected),'files preserved')
print('OVERLAP_CANDIDATES',[(r['name'],r['nonadjacent_self_overlap_candidates']) for r in records if r.get('nonadjacent_self_overlap_candidates')])
