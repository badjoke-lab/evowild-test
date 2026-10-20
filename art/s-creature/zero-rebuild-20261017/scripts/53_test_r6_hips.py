"""Actual armature deformation on a separate verification copy, via Blender MCP.
This is a bounded articulation test, not a production rig or gait.
"""
import bpy, bmesh, hashlib, json, math
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'verification/S_ZERO_R6_TRIAL_B.blend'
TEST=globals().get('TEST','A')
suffix='' if TEST=='A' else '_'+TEST
OUT=ROOT/f'verification/S_ZERO_R6_HIP_DEFORMATION_TEST{suffix}.blend'
REPORT=ROOT/f'evidence/R6_HIP_DEFORMATION_TEST{suffix}.json'
assert not OUT.exists() and not REPORT.exists() and bpy.app.version==(4,3,2)
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
model=bpy.data.collections['S_ZERO_CREATURE']
collection=bpy.data.collections.new('R6_VALIDATION_ONLY');bpy.context.scene.collection.children.link(collection)
data=bpy.data.armatures.new('R6_HIP_TEST_ONLY')
rig=bpy.data.objects.new('R6_HIP_TEST_ONLY',data);collection.objects.link(rig)
rig.show_in_front=True;rig['purpose']='Validation only. No IK, knee articulation, foot contacts, muscle constraints or production weights.'
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.context.view_layer.update()
pivots={'HIP_NEAR':(.78,-.235,1.74),'HIP_FAR':(.67,.235,1.70)}
with bpy.context.temp_override(object=rig,active_object=rig,selected_objects=[rig],selected_editable_objects=[rig]):
    bpy.ops.object.mode_set(mode='EDIT')
    base=data.edit_bones.new('PELVIS_FIXED');base.head=(.68,0,1.76);base.tail=(.68,0,2.02)
    for name,p in pivots.items():
        bone=data.edit_bones.new(name);bone.head=p;bone.tail=Vector(p)+Vector((0,0,-.40));bone.parent=base
    bpy.ops.object.mode_set(mode='OBJECT')

def ease(t):
    t=max(0.,min(1.,t));return t*t*(3.-2.*t)

def weights(co):
    x,y,z=co
    if x<.20 or z>1.93:return 0.,0.
    wx=ease((x-.20)/.30)
    wz=ease((1.93-z)/.60)
    lateral=ease((abs(y)-.025)/.15)
    lateral=lateral+(1-lateral)*ease((1.55-z)/.20)
    tail=1.
    if x>1.07:
        line=1.78-.75*(x-1.12)
        tail=1-ease((z-(line-.06))/.06)
    if TEST=='B':
        line=1.78-.75*(x-1.12)
        tail=1-ease((x-.95)/.12)*ease((z-(line-.10))/.10)
    w=wx*wz*lateral*tail
    if TEST=='B':
        far=ease((y+.10)/.20)
        return w*(1-far),w*far
    return (w,0.) if y<0 else (0.,w)

deformed=[];base_coords={};weight_counts={}
for ob in model.objects:
    if ob.type!='MESH':continue
    side='HIP_NEAR' if 'HIND_NEAR' in ob.name else 'HIP_FAR' if 'HIND_FAR' in ob.name else None
    if ob!=body and not side:continue
    assert not ob.vertex_groups
    groups={name:ob.vertex_groups.new(name=name) for name in ['PELVIS_FIXED','HIP_NEAR','HIP_FAR']}
    counts={'near':0,'far':0,'blend':0}
    for v in ob.data.vertices:
        n,f=weights(v.co) if ob==body else ((1.,0.) if side=='HIP_NEAR' else (0.,1.))
        for name,w in [('PELVIS_FIXED',1-n-f),('HIP_NEAR',n),('HIP_FAR',f)]:
            if w>1e-9:groups[name].add([v.index],w,'REPLACE')
        counts['near']+=n>0;counts['far']+=f>0;counts['blend']+=0<n+f<.999999
    mod=ob.modifiers.new('R6 validation deformation only','ARMATURE');mod.object=rig
    mod.use_deform_preserve_volume=True
    base_coords[ob.name]=[v.co.copy() for v in ob.data.vertices];deformed.append(ob);weight_counts[ob.name]=counts

states=[('NEUTRAL',1,0.,0.),('NEAR_FORWARD',12,25.,-20.),('NEAR_BACK',24,-20.,25.)]
for label,frame,near,far in states:
    for name,deg in [('HIP_NEAR',near),('HIP_FAR',far)]:
        pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION'
        axis=data.bones[name].matrix_local.to_3x3().inverted() @ Vector((0,1,0))
        pb.rotation_quaternion=Quaternion(axis,math.radians(deg))
        pb.keyframe_insert(data_path='rotation_quaternion',frame=frame)
sc=bpy.context.scene;sc.frame_start=1;sc.frame_end=24
sc['stage']='R6_HIP_TEST_ONLY';sc['candidate_status']='VERIFICATION COPY ONLY; unfinished validation armature'
# Test cameras frame the hip explicitly; original cameras remain available.
for name,template,target,scale in [
    ('TEST_SIDE','CAM_SIDE',(-.05,0,1.34),5.70),
    ('TEST_SIDE_HIP','CAM_SIDE',(.87,0,1.48),2.15),
    ('TEST_REAR34_HIP','CAM_REAR34',(.80,0,1.48),2.05),
    ('TEST_BACK_HIP','CAM_BACK',(.78,0,1.48),1.85)]:
    original=bpy.data.objects[template];ob=original.copy();ob.data=original.data.copy();ob.name=name;collection.objects.link(ob)
    direction=original.matrix_world.to_quaternion() @ Vector((0,0,1))
    ob.location=Vector(target)+direction*8.;ob.data.ortho_scale=scale
floor=[]
for ob in bpy.data.collections['STUDIO'].objects:
    if ob.type=='MESH':ob.hide_render=True;floor.append(ob.name)

def summary(values):
    s=sorted(values)
    return {str(q):s[min(len(s)-1,int(q*(len(s)-1)))] for q in [0,.01,.05,.5,.95,.99,1]}

rest=base_coords[body.name]
edges=[tuple(e.vertices) for e in body.data.edges]
local=lambda p:.20<p.x<1.35 and 1.10<p.z<2.10 and not(p.x>1.07 and p.z>1.78-.75*(p.x-1.12))
local_edges=[e for e in edges if all(local(rest[i]) for i in e)]
body.data.calc_loop_triangles()
tris=[tuple(t.vertices) for t in body.data.loop_triangles]
local_tris=[tri for tri in tris if all(local(rest[i]) for i in tri)]
records=[]
for label,frame,near,far in states:
    sc.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    ev=body.evaluated_get(deps);mesh=ev.to_mesh();posed=[v.co.copy() for v in mesh.vertices]
    assert len(posed)==len(rest)
    edge_ratios=[(posed[a]-posed[b]).length/max((rest[a]-rest[b]).length,1e-12) for a,b in local_edges]
    area_ratios=[];inverted=[];invalid_rest=[]
    for ti,(a,b,c) in enumerate(local_tris):
        before=(rest[b]-rest[a]).cross(rest[c]-rest[a]);after=(posed[b]-posed[a]).cross(posed[c]-posed[a])
        if TEST=='B' and before.length<1e-9:
            invalid_rest.append(ti);continue
        area_ratios.append(after.length/max(before.length,1e-12))
        if before.dot(after)<0:inverted.append(ti)
    sets=[set(p.vertices) for p in mesh.polygons]
    tree=BVHTree.FromPolygons(posed,[tuple(p.vertices) for p in mesh.polygons])
    pairs=set(tuple(sorted(pair)) for pair in tree.overlap(tree) if pair[0]!=pair[1] and not sets[pair[0]]&sets[pair[1]])
    hip_pairs=[pair for pair in pairs if any(any(local(rest[i]) for i in mesh.polygons[fi].vertices) for fi in pair)]
    bm=bmesh.new();bm.from_mesh(mesh)
    fixed=[i for i,p in enumerate(rest) if sum(weights(p))==0]
    record={'state':label,'frame':frame,'degrees':{'HIP_NEAR':near,'HIP_FAR':far},
        'max_fixed_vertex_displacement':max((posed[i]-rest[i]).length for i in fixed),
        'hip_edge_ratio_quantiles':summary(edge_ratios),'hip_triangle_area_ratio_quantiles':summary(area_ratios),
        'rest_triangles_cross_length_below_1e_9_excluded':len(invalid_rest),
        'hip_edges_over_1_5':sum(v>1.5 for v in edge_ratios),'hip_triangles_below_0_35':sum(v<.35 for v in area_ratios),
        'hip_triangles_over_2':sum(v>2 for v in area_ratios),'rest_normal_dot_negative':len(inverted),
        'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'whole_body_nonadjacent_BVH_candidates':len(pairs),'hip_nonadjacent_BVH_candidates':len(hip_pairs),
        'hip_overlap_pairs':sorted(hip_pairs)[:80],'absolute_volume':abs(bm.calc_volume(signed=True))}
    bm.free();ev.to_mesh_clear();records.append(record)
sc.frame_set(1);sc.camera=bpy.data.objects['TEST_SIDE']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report={'source':str(SOURCE.relative_to(ROOT)),'source_sha256':source_hash,
    'output':str(OUT.relative_to(ROOT)),'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
    'pivot_positions':pivots,'rotation_axis_world':[0,1,0],
    'test_variant':TEST,
    'weights':'Analytic normalized weights; pelvis-to-thigh transition z=1.93 to 1.33; B blends the midline and tail boundary continuously; distal hind accessories rigid.',
    'preserve_volume':True,'weight_counts':weight_counts,'measurements':records,
    'hidden_ground_for_test':floor,'hip_edge_count':len(local_edges),'hip_triangle_count':len(local_tris),
    'limits':'Simplified thigh rotation only. No knee/hock articulation, ground contact, gait, IK or runtime proof. BVH candidates are not a formal intersection proof. Negative rest-normal dot flags require visual review.'}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print('R6 actual armature test saved',OUT.name)
for record in records:print(record)
