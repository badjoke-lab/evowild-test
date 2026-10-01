"""Experimental Vibe Gate A1-v3: crest-only correction.
Open S-vibe-a1-v2.blend. Preserve every vertex except crest vertices 160..231.
"""
import bpy, os, json, hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
cage=bpy.data.collections['S_REBUILD_GATE_A']
assert len(mesh.vertices)==232
CREST=set(range(160,232))
FIXED_CORE=set(range(0,160))

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

# Crest-only C5/H6 correction.
# Side: clear rear-upward arc. Front: tips converge near sagittal plane.
crest={
  0:[(.058,-.52,1.470,.015,.024),(.035,-.34,1.555,.009,.014),(.014,-.14,1.640,.002,.003)],
  1:[(.076,-.50,1.430,.015,.023),(.045,-.31,1.500,.008,.013),(.026,-.10,1.570,.002,.003)],
  2:[(.082,-.47,1.390,.014,.022),(.055,-.27,1.450,.007,.012),(.040,-.06,1.510,.002,.003)],
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
assert before_hash==after_hash, 'A1-v3 changed head/neck or non-A1 geometry'
assert counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert polys=={o.name:len(o.data.polygons) for o in cage.objects if o.type=='MESH'}

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v3-crest-only',
 'source':'S-vibe-a1-v2.blend',
 'editable':['crest'],
 'hard_fixed':['head','neck','thorax','waist','pelvis','forelimbs','hindlimbs','feet','tail'],
 'fixed_geometry_hash_before':before_hash,
 'fixed_geometry_hash_after':after_hash,
 'fixed_geometry_unchanged':True,
 'topology_unchanged':True,
 'crest_tips':tips,
 'hypothesis':'rear-upward tapered layered blades with sagittally clustered tips',
 'decision':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-a1-v3-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v3.blend'),compress=True)
print('VIBE_A1_V3_EDIT_COMPLETE',json.dumps(report))
