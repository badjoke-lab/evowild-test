"""Experimental Vibe Gate A1-v6: neck proportion + rigid head/crest placement only.
Source: S-vibe-a1-v5.blend.
Keep head shape and curved crest shape exactly; move them as one rigid unit.
Rebuild only neck rings 5-7. Thorax ring 8+ and all appendages are hard-locked.
"""
import bpy, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_curved_laminar_crest_v5']
mesh=core.data
assert len(mesh.vertices)==160

# Head rings 0-4 = 0..39, neck rings 5-7 = 40..63, ring 8+ fixed.
HEAD=set(range(0,40))
NECK=set(range(40,64))
BODY_FIXED=set(range(64,160))
DELTA=Vector((0.0,0.12,-0.06))

# snapshots
head_before={i:mesh.vertices[i].co.copy() for i in HEAD}
crest_before=[v.co.copy() for v in crest.data.vertices]
body_before={i:mesh.vertices[i].co.copy() for i in BODY_FIXED}
appendage_before={}
for o in cage.objects:
    if o.type=='MESH' and o not in (core,crest):
        appendage_before[o.name]=[v.co.copy() for v in o.data.vertices]

# Rigidly move head rings 0-4 and entire approved curved crest.
for i in HEAD:
    mesh.vertices[i].co=head_before[i]+DELTA
for i,v in enumerate(crest.data.vertices):
    v.co=crest_before[i]+DELTA

# Rebuild only neck stations 5-7. X widths kept from the v2/v5 neck.
stations={
  5:(-.34,1.290,1.070,.078),
  6:(-.22,1.200,.940,.093),
  7:(-.11,1.130,.830,.116),
}
for s,(y,top,bottom,width) in stations.items():
    for k in range(8):
        a=k*math.tau/8
        mesh.vertices[s*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))
mesh.update(); crest.data.update()

# Validation: head and crest are rigid transforms, body/appendages exactly fixed.
for i in HEAD:
    assert (mesh.vertices[i].co-(head_before[i]+DELTA)).length < 1e-8
for i,v in enumerate(crest.data.vertices):
    assert (v.co-(crest_before[i]+DELTA)).length < 1e-8
for i in BODY_FIXED:
    assert tuple(mesh.vertices[i].co)==tuple(body_before[i]), f'body changed {i}'
for name,coords in appendage_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'appendage changed {name}:{i}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(BODY_FIXED):
        h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for name in sorted(appendage_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v6-neck-proportion',
 'source':'S-vibe-a1-v5.blend',
 'decision':'REVIEW_PENDING',
 'editable':['neck rings 5-7','rigid head+crest placement'],
 'head_shape_unchanged':True,
 'crest_shape_unchanged':True,
 'head_crest_rigid_delta':[DELTA.x,DELTA.y,DELTA.z],
 'hard_fixed':['thorax ring 8+','waist','pelvis','limbs','feet','tail'],
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'neck_station_targets':{str(k):v for k,v in stations.items()},
 'topology_unchanged':True
}
with open(os.path.join(OUT,'S-vibe-a1-v6-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v6.blend'),compress=True)
print('VIBE_A1_V6_EDIT_COMPLETE',json.dumps(report))
