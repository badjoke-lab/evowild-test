"""Read R1 and final R2 in Blender. Inspect actual stored mesh data, never save inputs."""
import bpy
import bmesh
import hashlib
import json
import struct
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
R1=ROOT/'S_ZERO_CANDIDATE_REVISED_R1.blend'
R2=ROOT/'S_ZERO_CANDIDATE_REVISED_R2.blend'
OUT=ROOT/'evidence/VERIFY_R2_RELOAD.json'
assert not OUT.exists()


def sig(obj):
    h=hashlib.sha256()
    for v in obj.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in obj.data.polygons:
        h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        h.update(struct.pack('<I?',p.material_index,p.use_smooth))
    for row in obj.matrix_world:h.update(struct.pack('<4f',*row))
    return h.hexdigest()


def studio():
    records={}
    for o in bpy.data.collections['STUDIO'].objects:
        d={'type':o.type,'matrix':[list(row) for row in o.matrix_world]}
        if o.type=='MESH':d['mesh_sha256']=sig(o)
        if o.type=='CAMERA':d.update({'projection':o.data.type,'ortho_scale':o.data.ortho_scale,'lens':o.data.lens})
        if o.type=='LIGHT':d.update({'color':list(o.data.color),'energy':o.data.energy,'shape':o.data.shape,'size':o.data.size})
        records[o.name]=d
    s=bpy.context.scene
    records['color_management']={'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}
    records['world']=[{'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value')}} for n in s.world.node_tree.nodes]
    return records


def snapshot():
    coll=bpy.data.collections['S_ZERO_CREATURE']
    meshes={o.name:sig(o) for o in coll.objects if o.type=='MESH'}
    body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
    coords=[tuple(v.co) for v in body.data.vertices]
    crowns={o.name:[tuple(v.co) for v in o.data.vertices] for o in coll.objects if o.name.startswith('CROWN_')}
    sections={}
    for n in ['CROWN_MAIN_N','CROWN_MAIN_F']:
        ob=bpy.data.objects[n]
        sections[n]={}
        for z in [2.40,2.64,2.84]:
            ys=[]
            for e in ob.data.edges:
                a,b=(ob.data.vertices[i].co for i in e.vertices)
                if min(a.z,b.z)<=z<=max(a.z,b.z) and abs(b.z-a.z)>1e-6:
                    ys.append(a.y+(b.y-a.y)*(z-a.z)/(b.z-a.z))
            sections[n][str(z)]={'min_y':min(ys),'max_y':max(ys),'width':max(ys)-min(ys)}
    return {'mesh_signatures':meshes,'body_coordinates':coords,'crown_coordinates':crowns,'crown_sections':sections,'studio':studio()}


before_hash=hashlib.sha256(R1.read_bytes()).hexdigest()
after_hash=hashlib.sha256(R2.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R1),load_ui=False)
before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(R2),load_ui=False)
after=snapshot()
deleted=sorted(set(before['mesh_signatures'])-set(after['mesh_signatures']))
changed=sorted(n for n in after['mesh_signatures'] if before['mesh_signatures'].get(n)!=after['mesh_signatures'][n])
same=sorted(n for n in after['mesh_signatures'] if before['mesh_signatures'].get(n)==after['mesh_signatures'][n])
assert len(same)==137
assert deleted==sorted(['SCAPULA_N','SCAPULA_F','DELTOID_N','DELTOID_F','BRACHIAL_FORE_NEAR','BRACHIAL_FORE_FAR'])
assert set(changed)=={'S_ZERO_BODY_CONTINUOUS',*before['crown_coordinates']}
assert before['studio']==after['studio']
for name,coords in before['crown_coordinates'].items():
    assert all(p[0]==q[0] and p[2]==q[2] for p,q in zip(coords,after['crown_coordinates'][name]))
after_positions=set(after['body_coordinates'])
protected_coords=[p for p in before['body_coordinates'] if not(-1.23<p[0]<-.36 and 1.00<p[2]<2.10 and abs(p[1])>.095)]
assert all(p in after_positions for p in protected_coords)
records=[]
for ob in sorted(bpy.data.collections['S_ZERO_CREATURE'].objects,key=lambda o:o.name):
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    unseen=set(bm.verts);components=[]
    while unseen:
        stack=[unseen.pop()];count=0
        while stack:
            v=stack.pop();count+=1
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in unseen:unseen.remove(other);stack.append(other)
        components.append(count)
    rec={'name':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),
         'boundary_edges':sum(e.is_boundary for e in bm.edges),
         'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
         'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
         'loose_vertices':sum(not v.link_edges for v in bm.verts),'components':sorted(components,reverse=True)}
    bm.free()
    assert all(rec[k]==0 for k in ['boundary_edges','nonmanifold_edges','degenerate_faces','loose_vertices']),rec
    records.append(rec)
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
polys=[set(p.vertices) for p in body.data.polygons]
pairs=set(tuple(sorted(p)) for p in bvh.overlap(bvh) if p[0]!=p[1] and not(polys[p[0]]&polys[p[1]]))
assert not pairs
assert next(r for r in records if r['name']==body.name)['components']==[len(body.data.vertices)]
base=json.loads((ROOT/'evidence/R2_START_STATE.json').read_text())
protected_files={}
for p,d in base['protected_artifacts'].items():
    if p.endswith('QUALITY_REVIEW.md'):continue
    f=ROOT.parents[2]/p
    assert hashlib.sha256(f.read_bytes()).hexdigest()==d['sha256'],p
    protected_files[p]=d['sha256']
assert hashlib.sha256(R1.read_bytes()).hexdigest()==before_hash
assert hashlib.sha256(R2.read_bytes()).hexdigest()==after_hash
report={'blender':bpy.app.version_string,'reopened':R2.name,'r1_sha256':before_hash,'r2_sha256':after_hash,
        'mesh_count':len(records),'vertices':sum(r['vertices'] for r in records),'faces':sum(r['faces'] for r in records),
        'unchanged_meshes':same,'changed_meshes':changed,'merged_into_body':deleted,
        'untouched_body_vertex_count':len(protected_coords),'crown_xz_coordinates_exactly_unchanged':True,
        'crown_frontal_sections_r1':before['crown_sections'],'crown_frontal_sections_r2':after['crown_sections'],
        'studio_lights_cameras_world_color_management_unchanged':True,'studio_snapshot':after['studio'],
        'body_nonadjacent_self_overlap_candidates':len(pairs),'protected_file_sha256':protected_files,
        'meshes':records,'armatures':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],
        'actions':list(bpy.data.actions.keys()),'decision':'REVISE overall; retain local improvement as working R2; no production promotion',
        'limits':'Closed manifold is not rig-ready. Boolean seam/ngon topology requires retopology. BVH is not a complete intersection proof. Gait and runtime untested.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R2_RELOAD_VERIFIED',len(same),'unchanged meshes;',len(records),'closed meshes;',len(protected_files),'protected files')
