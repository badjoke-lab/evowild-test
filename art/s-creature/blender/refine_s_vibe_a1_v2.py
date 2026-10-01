"""Experimental Vibe Gate A1-v2.
Restart from S-rebuild-v1.blend. Apply only image-derived head/crest/neck changes.
"""
import bpy, os, json, hashlib, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
cage=bpy.data.collections['S_REBUILD_GATE_A']
assert len(mesh.vertices)==232
TARGET_CORE=set(range(0,64)) | set(range(160,232))
FIXED_CORE=set(range(64,160))

def hash_fixed():
    h=hashlib.sha256()
    for i in sorted(FIXED_CORE):
        h.update(core.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core: continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

before_hash=hash_fixed()
counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
polys={o.name:len(o.data.polygons) for o in cage.objects if o.type=='MESH'}

# Head/neck stations derived from repository reference proportions.
# Thorax starts at station 8 and is hard-fixed.
stations=[
 (-.84,1.350,1.300,.018),
 (-.79,1.390,1.300,.042),
 (-.71,1.450,1.310,.072),
 (-.64,1.460,1.320,.080),
 (-.57,1.420,1.250,.084),
 (-.45,1.330,1.100,.078),
 (-.29,1.210,.960,.093),
 (-.14,1.130,.840,.116),
]
for s,(y,top,bottom,width) in enumerate(stations):
    for k in range(8):
        a=k*math.tau/8
        mesh.vertices[s*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))

# C5/H6-inspired layered blade hypothesis:
# long in rearward Y, modest vertical rise, tapered distal ends,
# and distal centers converge toward the sagittal plane.
crest={
  0:[(.060,-.52,1.470,.016,.030),(.038,-.30,1.520,.010,.020),(.022,-.10,1.550,.002,.004)],
  1:[(.078,-.50,1.430,.016,.028),(.052,-.27,1.470,.009,.018),(.034,-.06,1.500,.002,.004)],
  2:[(.083,-.47,1.390,.015,.026),(.058,-.23,1.420,.008,.016),(.042,-.02,1.450,.002,.004)],
}
cursor=160
tips=[]
for sign in (1,-1):
    for level in range(3):
        for x,y,z,thickness,depth in crest[level]:
            for p in [
                (sign*(x-thickness),y,z+depth),
                (sign*(x+thickness),y,z+depth),
                (sign*(x+thickness),y,z-depth),
                (sign*(x-thickness),y,z-depth),
            ]:
                mesh.vertices[cursor].co=p; cursor+=1
        t=crest[level][-1]
        tips.append({'side':sign,'layer':level,'tip':[sign*t[0],t[1],t[2]]})
assert cursor==232
mesh.update()

after_hash=hash_fixed()
assert before_hash==after_hash, 'non-A1 geometry changed'
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert polys=={o.name:len(o.data.polygons) for o in cage.objects if o.type=='MESH'}

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v2',
 'source':'S-rebuild-v1.blend',
 'reference_lock':'S_VIBE_A1_REFERENCE_ANALYSIS.md',
 'status':'MODEL_EDIT_COMPLETE_RENDER_PENDING',
 'editable':['head','crest','neck'],
 'hard_fixed':['thorax','waist','pelvis','forelimbs','hindlimbs','feet','tail'],
 'fixed_geometry_hash_before':before_hash,
 'fixed_geometry_hash_after':after_hash,
 'fixed_geometry_unchanged':True,
 'topology_unchanged':True,
 'station_targets':stations,
 'crest_tips':tips,
 'hypothesis':[
   'shorter skull-to-thorax Y span',
   'moderate lateral neck width with increased sagittal depth',
   'tapered rear-swept blades',
   'distal crest convergence toward sagittal plane',
   'limited crest vertical rise'
 ],
 'decision':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-a1-v2-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v2.blend'),compress=True)
print('VIBE_A1_V2_EDIT_COMPLETE',json.dumps(report))
