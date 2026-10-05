"""S rig v2: one static deformation stress pose, no Action/keyframes."""
import bpy,os,json,hashlib,math
from mathutils import Vector,Quaternion

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-rig-v1.blend'))

cage=bpy.data.collections['S_REBUILD_GATE_A']
arm=bpy.data.objects['S_RIG']
assert arm.type=='ARMATURE'
assert len(bpy.data.actions)==0

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices)).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}

def rotate_world_axis(name,axis_world,degrees):
    pb=arm.pose.bones[name]
    axis_local=pb.bone.matrix_local.to_3x3().inverted() @ Vector(axis_world)
    axis_local.normalize()
    pb.rotation_mode='QUATERNION'
    pb.rotation_quaternion=Quaternion(axis_local,math.radians(degrees))

# Asymmetric running-like stress pose, deliberately moderate.
pose_spec={
 'fore_upper.L':('X',12),'fore_lower.L':('X',-28),'fore_foot.L':('X',10),
 'fore_upper.R':('X',-10),'fore_lower.R':('X',22),'fore_foot.R':('X',-8),
 'hind_upper.L':('X',-12),'hind_lower.L':('X',24),'hind_foot.L':('X',-10),
 'hind_upper.R':('X',10),'hind_lower.R':('X',-20),'hind_foot.R':('X',8),
 'neck':('Z',6),'head':('Z',-8),
 'tail.01':('Z',6),'tail.02':('Z',8),'tail.03':('Z',10)
}
for name,(axis,deg) in pose_spec.items():
    rotate_world_axis(name,(1,0,0) if axis=='X' else (0,0,1),deg)

bpy.context.view_layer.update()

# No base mesh edits and no actions/keyframes.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' base coords changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rig-v2-pose.blend'),compress=True)

# Evaluated bounds as a sanity check.
deps=bpy.context.evaluated_depsgraph_get()
bounds={}
for name in ['S_rebuild_core_head_crest_neck_torso_tail','S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R']:
    o=bpy.data.objects[name].evaluated_get(deps)
    pts=[o.matrix_world @ Vector(c) for c in o.bound_box]
    bounds[name]={
      'min':[min(p[i] for p in pts) for i in range(3)],
      'max':[max(p[i] for p in pts) for i in range(3)]
    }

report={
 'stage':'rig','pass':'v2-pose','status':'REVIEW_PENDING','source':'S-rig-v1.blend',
 'scope':'single static armature pose only',
 'base_geometry_sha256':source_hash,'base_coordinates_unchanged':True,
 'action_count':len(bpy.data.actions),'keyframes_created':False,
 'pose_spec_degrees':{k:v[1] for k,v in pose_spec.items()},
 'evaluated_bounds':bounds,
 'limitations':['Single stress pose only; animation timing/gait not tested','Weights remain first-pass until deformation review']
}
json.dump(report,open(os.path.join(OUT,'S-rig-v2-pose.json'),'w'),indent=2)
print('S_RIG_V2_POSE_SAVED',json.dumps({'pose_bones':len(pose_spec),'actions':len(bpy.data.actions)}))
