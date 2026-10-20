"""Continue immutable trial B in Blender 4.3.2. New outputs only.

Retessellate the existing pelvic patch; preserve all source coordinates,
materials and protected surfaces. Solve continuous skin weights on its graph,
then compare actual evaluated armature deformations at the original angles.
"""
import bpy, bmesh, hashlib, json, math, shutil
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT.parent
SOURCE = PRIOR / 'verification/S_ZERO_R6_TRIAL_B.blend'
COPY = ROOT / 'verification/S_ZERO_R6_PROTECTED_B.blend'
STATIC = ROOT / 'verification/S_ZERO_R6_RECOVERED_C.blend'
RIG = ROOT / 'verification/S_ZERO_R6_HIP_DEFORMATION_RECOVERED_C.blend'
REPORT = ROOT / 'evidence/R6_REPAIR_AND_DEFORMATION_C.json'
assert bpy.app.version == (4, 3, 2)
assert not any(p.exists() for p in [COPY, STATIC, RIG, REPORT])
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash == '8748d32c0b842c15c5a3c5da910637b4dcc06bf8af112882c2447afdb47e4949'
shutil.copy2(SOURCE, COPY)
bpy.ops.wm.open_mainfile(filepath=str(COPY), load_ui=False)
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']

def region(p):
    x,y,z = p
    return .18 < x < 1.34 and 1.10 < z < 2.10 and not (x > 1.07 and z > 1.78-.75*(x-1.12))

def mesh_signature(ob):
    m=ob.data
    return hashlib.sha256(repr((
        [tuple(v.co) for v in m.vertices],
        [(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
        [[tuple(d.color) for d in a.data] for a in m.color_attributes],
        [list(r) for r in ob.matrix_world],
    )).encode()).hexdigest()

def protected_faces(m):
    return sorted((
        tuple(tuple(m.vertices[i].co) for i in p.vertices),p.material_index,p.use_smooth,
        tuple((a.name,tuple(tuple(a.data[i].color) for i in p.loop_indices)) for a in m.color_attributes)
    ) for p in m.polygons if not all(region(m.vertices[i].co) for i in p.vertices))

model=bpy.data.collections['S_ZERO_CREATURE']
protected={o.name:mesh_signature(o) for o in model.objects if o.type=='MESH' and o!=body}
before_faces=protected_faces(body.data)
before_coords=[tuple(v.co) for v in body.data.vertices]
body.data.calc_loop_triangles()
tiny_before=sum(t.area<1e-9 for t in body.data.loop_triangles)
bm=bmesh.new();bm.from_mesh(body.data)
local_faces=[f for f in bm.faces if all(region(v.co) for v in f.verts)]
count=len(local_faces)
# BMesh's geometry-aware diagonal choice avoids the collinear fan triangles
# produced by implicit tessellation of the Boolean cut quads and n-gons.
bmesh.ops.triangulate(bm,faces=local_faces)
assert all(e.is_manifold for e in bm.edges)
assert all(f.calc_area()>1e-9 for f in bm.faces)
bm.to_mesh(body.data);bm.free();body.data.update()
assert [tuple(v.co) for v in body.data.vertices]==before_coords
assert protected_faces(body.data)==before_faces
assert all(mesh_signature(bpy.data.objects[n])==v for n,v in protected.items())
body.data.calc_loop_triangles()
tiny_after=sum(t.area<1e-9 for t in body.data.loop_triangles)
assert tiny_after==0
sc=bpy.context.scene
sc['stage']='R6_RECOVERED_C_STATIC'
sc['candidate_status']='REVISE; trial B topology repair; validation rig stored separately'
body['r6_recovery']='Local pelvic retessellation of 8388 polygons; source vertex positions and palette preserved.'
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(STATIC),compress=True)
static_hash=hashlib.sha256(STATIC.read_bytes()).hexdigest()

# Work on a reloaded saved static result; the formal source stays unrigged.
bpy.ops.wm.open_mainfile(filepath=str(STATIC),load_ui=False)
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];sc=bpy.context.scene
model=bpy.data.collections['S_ZERO_CREATURE']
rest=np.array([v.co[:] for v in body.data.vertices],dtype=np.float64)
edges=np.array([e.vertices[:] for e in body.data.edges],dtype=np.int64)
body.data.calc_loop_triangles()
tris=np.array([t.vertices[:] for t in body.data.loop_triangles],dtype=np.int64)
local=np.array([.20<x<1.35 and 1.10<z<2.10 and not(x>1.07 and z>1.78-.75*(x-1.12)) for x,y,z in rest])
local_edges=edges[np.all(local[edges],axis=1)]
local_tris=tris[np.all(local[tris],axis=1)]
rest_edge=np.linalg.norm(rest[local_edges[:,0]]-rest[local_edges[:,1]],axis=1)
rest_cross=np.cross(rest[local_tris[:,1]]-rest[local_tris[:,0]],rest[local_tris[:,2]]-rest[local_tris[:,0]])
rest_area=np.linalg.norm(rest_cross,axis=1)
assert min(rest_area)>1e-9
collection=bpy.data.collections.new('R6_RECOVERY_VALIDATION_ONLY')
sc.collection.children.link(collection)
data=bpy.data.armatures.new('R6_RECOVERY_HIP_TEST')
rig=bpy.data.objects.new('R6_RECOVERY_HIP_TEST',data);collection.objects.link(rig)
rig.show_in_front=True
rig['purpose']='Verification only; no knee/hock/IK/contact/gait or runtime validation.'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.context.view_layer.objects.active=rig

def set_pivots(pivots,create=False):
    sc.frame_set(1)
    with bpy.context.temp_override(object=rig,active_object=rig,selected_objects=[rig],selected_editable_objects=[rig]):
        bpy.ops.object.mode_set(mode='EDIT')
        base=data.edit_bones.new('PELVIS_FIXED') if create else data.edit_bones['PELVIS_FIXED']
        base.head=(.68,0,1.76);base.tail=(.68,0,2.02)
        for name,p in pivots.items():
            bone=data.edit_bones.new(name) if create else data.edit_bones[name]
            bone.head=p;bone.tail=Vector(p)+Vector((0,0,-.40));bone.parent=base
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()

old_pivots={'HIP_NEAR':(.78,-.235,1.74),'HIP_FAR':(.67,.235,1.70)}
new_pivots={'HIP_NEAR':(.80,-.29,1.62),'HIP_FAR':(.70,.29,1.62)}
set_pivots(old_pivots,True)

def harmonic_weights(seed_z,top_z):
    """Positive graph Laplacian Dirichlet solve. Fixed torso/tail, rigid distal legs."""
    x,y,z=rest.T
    fixed=(x<=.25)|(z>=top_z)|((x>1.07)&(z>1.78-.75*(x-1.12)))
    distal=(x>.25)&(z<seed_z)&~fixed
    boundary=fixed|distal;unknown=np.where(~boundary)[0]
    prescribed=np.zeros((len(rest),2))
    prescribed[distal&(y<0),0]=1.
    prescribed[distal&(y>=0),1]=1.
    a,b=edges.T
    conductance=1/np.maximum(np.linalg.norm(rest[a]-rest[b],axis=1),.003)
    degree=np.bincount(a,weights=conductance,minlength=len(rest))+np.bincount(b,weights=conductance,minlength=len(rest))
    def lap(v):
        return degree*v-np.bincount(a,weights=conductance*v[b],minlength=len(rest))-np.bincount(b,weights=conductance*v[a],minlength=len(rest))
    def mat(v):
        full=np.zeros(len(rest));full[unknown]=v
        return lap(full)[unknown]
    solution=prescribed.copy();iterations=[]
    for channel in range(2):
        rhs=-lap(prescribed[:,channel])[unknown]
        v=np.zeros(len(unknown));r=rhs.copy();zpre=r/degree[unknown];p=zpre.copy()
        rz=np.dot(r,zpre)
        for it in range(2000):
            ap=mat(p);alpha=rz/np.dot(p,ap);v+=alpha*p;r-=alpha*ap
            if np.max(np.abs(r))<1e-8:break
            zpre=r/degree[unknown];nrz=np.dot(r,zpre);p=zpre+(nrz/rz)*p;rz=nrz
        solution[unknown,channel]=v;iterations.append(it+1)
    solution=np.maximum(solution,0)
    assert np.max(solution.sum(axis=1))<1.0000001
    solution/=np.maximum(solution.sum(axis=1),1)[:,None]
    return solution,{'seed_z':seed_z,'top_z':top_z,'unknown_vertices':len(unknown),'iterations':iterations,'fixed_vertices':int(fixed.sum())}

groups={}
for ob in model.objects:
    if ob.type!='MESH':continue
    side='HIP_NEAR' if 'HIND_NEAR' in ob.name else 'HIP_FAR' if 'HIND_FAR' in ob.name else None
    if ob!=body and not side:continue
    assert not ob.vertex_groups
    groups[ob.name]={n:ob.vertex_groups.new(name=n) for n in ['PELVIS_FIXED','HIP_NEAR','HIP_FAR']}
    if ob!=body:
        groups[ob.name][side].add(list(range(len(ob.data.vertices))),1.,'REPLACE')
    mod=ob.modifiers.new('Recovery verification armature','ARMATURE');mod.object=rig
    mod.use_deform_preserve_volume=True

def apply_weights(weights):
    gs=groups[body.name]
    for g in gs.values():g.remove(list(range(len(rest))))
    for i,(near,far) in enumerate(weights):
        for name,w in [('PELVIS_FIXED',max(0.,1-near-far)),('HIP_NEAR',near),('HIP_FAR',far)]:
            if w>1e-10:gs[name].add([i],float(w),'REPLACE')
    body.data.update()

states=[('NEUTRAL',1,0.,0.),('NEAR_FORWARD',12,25.,-20.),('NEAR_BACK',24,-20.,25.)]
def pose(near,far):
    for name,deg in [('HIP_NEAR',near),('HIP_FAR',far)]:
        pb=rig.pose.bones[name]
        assert 'QUATERNION' in [i.identifier for i in pb.bl_rna.properties['rotation_mode'].enum_items]
        pb.rotation_mode='QUATERNION'
        axis=data.bones[name].matrix_local.to_3x3().inverted()@Vector((0,1,0))
        pb.rotation_quaternion=Quaternion(axis,math.radians(deg))
    bpy.context.view_layer.update()

def measure(weights,full=False):
    records=[]
    for label,frame,near,far in states:
        pose(near,far)
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        posed=np.array([v.co[:] for v in mesh.vertices])
        er=np.linalg.norm(posed[local_edges[:,0]]-posed[local_edges[:,1]],axis=1)/rest_edge
        cross=np.cross(posed[local_tris[:,1]]-posed[local_tris[:,0]],posed[local_tris[:,2]]-posed[local_tris[:,0]])
        ar=np.linalg.norm(cross,axis=1)/rest_area
        record={'state':label,'frame':frame,'degrees':{'HIP_NEAR':near,'HIP_FAR':far},
            'edge_min':float(er.min()),'edge_max':float(er.max()),'edge_p99':float(np.quantile(er,.99)),
            'edges_above_1_5':int((er>1.5).sum()),'area_min':float(ar.min()),'area_max':float(ar.max()),
            'triangles_below_0_35':int((ar<.35).sum()),'triangles_above_2':int((ar>2).sum()),
            'rest_normal_dot_negative':int((np.sum(rest_cross*cross,axis=1)<0).sum()),
            'max_fixed_displacement':float(np.max(np.linalg.norm(posed[weights.sum(axis=1)==0]-rest[weights.sum(axis=1)==0],axis=1)))}
        if full:
            bm=bmesh.new();bm.from_mesh(mesh)
            record.update(boundary_edges=sum(e.is_boundary for e in bm.edges),
                nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),
                zero_area_faces=sum(f.calc_area()<1e-12 for f in bm.faces),volume=abs(bm.calc_volume(signed=True)))
            bm.free()
            sets=[set(p.vertices) for p in mesh.polygons]
            tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],[p.vertices[:] for p in mesh.polygons])
            pairs=set(tuple(sorted(pair)) for pair in tree.overlap(tree) if pair[0]!=pair[1] and not sets[pair[0]]&sets[pair[1]])
            hip_pairs=[p for p in pairs if any(any(local[i] for i in mesh.polygons[fi].vertices) for fi in p)]
            record.update(whole_body_nonadjacent_BVH_candidates=len(pairs),hip_nonadjacent_BVH_candidates=len(hip_pairs),hip_pairs=sorted(hip_pairs)[:30])
            order=np.argsort(er)[-10:][::-1]
            record['largest_edges']=[{'indices':local_edges[i].tolist(),'ratio':float(er[i]),
                'rest_center':rest[local_edges[i]].mean(axis=0).tolist()} for i in order]
        ev.to_mesh_clear();records.append(record)
    pose(0,0)
    return records

trials=[];best=None
for seed_z,top_z in [(1.24,1.96),(1.12,2.02),(1.18,2.02)]:
    weights,solve=harmonic_weights(seed_z,top_z)
    apply_weights(weights)
    for pivot_name,pivots in [('original',old_pivots),('centered',new_pivots)]:
        set_pivots(pivots)
        records=measure(weights)
        score=max(r['edge_max'] for r in records)+max(0,.5-min(r['area_min'] for r in records))*4
        trials.append({'solve':solve,'pivot_variant':pivot_name,'pivots':pivots,'measurements':records,'selection_score':score})
        print('R6_RECOVERY_TRIAL',seed_z,top_z,pivot_name,score,[(r['edge_max'],r['area_min'],r['rest_normal_dot_negative']) for r in records],flush=True)
        if best is None or score<best[0]:best=(score,weights.copy(),pivots,solve,pivot_name)
_,weights,pivots,solve,pivot_name=best
apply_weights(weights);set_pivots(pivots)
measurements=measure(weights,True)
for label,frame,near,far in states:
    pose(near,far)
    for name in ['HIP_NEAR','HIP_FAR']:
        rig.pose.bones[name].keyframe_insert(data_path='rotation_quaternion',frame=frame)
sc.frame_start=1;sc.frame_end=24;sc.frame_set(1)
for name,template,target,scale in [
    ('TEST_SIDE','CAM_SIDE',(-.05,0,1.34),5.70),
    ('TEST_SIDE_HIP','CAM_SIDE',(.87,0,1.48),2.15),
    ('TEST_REAR34_HIP','CAM_REAR34',(.80,0,1.48),2.05),
    ('TEST_BACK_HIP','CAM_BACK',(.78,0,1.48),1.85)]:
    original=bpy.data.objects[template];ob=original.copy();ob.data=original.data.copy();ob.name=name;collection.objects.link(ob)
    direction=original.matrix_world.to_quaternion()@Vector((0,0,1))
    ob.location=Vector(target)+direction*8.;ob.data.ortho_scale=scale
for ob in bpy.data.collections['STUDIO'].objects:
    if ob.type=='MESH':ob.hide_render=True
sc.camera=bpy.data.objects['TEST_SIDE']
sc['stage']='R6_RECOVERED_C_HIP_TEST_ONLY'
sc['candidate_status']='VERIFICATION ONLY; see separate measurements and quality review'
bpy.ops.wm.save_as_mainfile(filepath=str(RIG),compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
assert hashlib.sha256(STATIC.read_bytes()).hexdigest()==static_hash
report={'source':str(SOURCE.relative_to(PRIOR)),'source_sha256':source_hash,
    'static':str(STATIC.relative_to(ROOT)),'static_sha256':static_hash,
    'rig':str(RIG.relative_to(ROOT)),'rig_sha256':hashlib.sha256(RIG.read_bytes()).hexdigest(),
    'blender':bpy.app.version_string,'local_polygons_retessellated':count,
    'all_original_vertices_exact':len(before_coords),'protected_objects_exact':len(protected),
    'protected_body_faces_exact':len(before_faces),'tiny_rest_triangles_before':tiny_before,'tiny_rest_triangles_after':tiny_after,
    'weight_method':'Positive inverse-edge-length graph Laplacian with fixed torso/tail and rigid distal-leg Dirichlet conditions; normalized 3-bone dual-quaternion skinning',
    'trials':trials,'selected_pivots':pivots,'selected_pivot_variant':pivot_name,'selected_solve':solve,
    'hip_edge_count':len(local_edges),'hip_triangle_count':len(local_tris),'measurements':measurements,
    'limits':'Only three hip poses; no knee/hock/IK/contact/gait or PC/mobile runtime proof. BVH candidates are conservative. Rest-normal sign is not a rigorous inversion proof.'}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print('R6_RECOVERY_COMPLETE',json.dumps({k:v for k,v in report.items() if k in ['selected_pivots','selected_solve','measurements']}),flush=True)
