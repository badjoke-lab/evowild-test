"""Experimental Vibe Modeling Gate A1.
Open S-rebuild-v1.blend first. Edit only head / crest / neck vertex coordinates.
Thorax/waist/pelvis/limbs/feet/tail and topology are hard-locked by hashes.
"""
import bpy, os, json, hashlib, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
assert len(mesh.vertices)==232, f'unexpected core vertex count {len(mesh.vertices)}'
cage=bpy.data.collections['S_REBUILD_GATE_A']

TARGET_CORE=set(range(0,64)) | set(range(160,232))
FIXED_CORE=set(range(64,160))

def hash_coords(items):
    h=hashlib.sha256()
    for name,idx,co in items:
        h.update(name.encode()); h.update(str(idx).encode()); h.update(repr(tuple(co)).encode())
    return h.hexdigest()

def fixed_items():
    items=[]
    for i in sorted(FIXED_CORE):
        items.append((core.name,i,mesh.vertices[i].co.copy()))
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core: continue
        for i,v in enumerate(o.data.vertices):
            items.append((o.name,i,v.co.copy()))
    return items

before_fixed=fixed_items()
before_fixed_hash=hash_coords(before_fixed)
before_counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
before_poly_counts={o.name:len(o.data.polygons) for o in cage.objects if o.type=='MESH'}

# Reference-driven A1 station targets.
# Front is -Y. Station 8 (anterior thorax) and everything behind it remain untouched.
stations=[
 (-.92,1.355,1.295,.018),
 (-.86,1.395,1.295,.042),
 (-.76,1.455,1.315,.074),
 (-.67,1.465,1.320,.082),
 (-.59,1.420,1.255,.086),
 (-.46,1.335,1.120,.090),
 (-.30,1.225,.995,.112),
 (-.16,1.135,.865,.130),
]
for s,(y,top,bottom,width) in enumerate(stations):
    for k in range(8):
        a=k*math.tau/8
        mesh.vertices[s*8+k].co=(width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))

# Six skull-rooted plates remain, but tips are lowered, broadened, and swept rearward.
# This specifically removes the front/back paired-horn reading of rebuild-v1.
crest={
  0:[(.055,-.50,1.495,.022,.050),(.064,-.26,1.525,.020,.043),(.070,-.04,1.535,.012,.022)],
  1:[(.085,-.48,1.435,.022,.046),(.094,-.23,1.465,.018,.038),(.100,-.01,1.475,.011,.020)],
  2:[(.092,-.43,1.385,.020,.040),(.102,-.18,1.410,.017,.034),(.108,.02,1.420,.010,.018)],
}
cursor=160
crest_landmarks=[]
for sign in (1,-1):
    for level in range(3):
        for x,y,z,thickness,depth in crest[level]:
            pts=[
                (sign*(x-thickness),y,z+depth),
                (sign*(x+thickness),y,z+depth),
                (sign*(x+thickness),y,z-depth),
                (sign*(x-thickness),y,z-depth),
            ]
            for p in pts:
                mesh.vertices[cursor].co=p; cursor+=1
        tip=crest[level][-1]
        crest_landmarks.append({'side':sign,'layer':level,'tip':[sign*tip[0],tip[1],tip[2]]})
assert cursor==232
mesh.update()

after_fixed=fixed_items()
after_fixed_hash=hash_coords(after_fixed)
assert before_fixed_hash==after_fixed_hash, 'A1 changed hard-locked non-target geometry'
assert before_counts=={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
assert before_poly_counts=={o.name:len(o.data.polygons) for o in cage.objects if o.type=='MESH'}

report={
  'lane':'exp/s-creature-vibe-modeling',
  'gate':'A1',
  'status':'MODEL_EDIT_COMPLETE_RENDER_PENDING',
  'input':'S-rebuild-v1.blend',
  'output':'S-vibe-a1.blend',
  'method':'reference -> landmarks -> constrained geometry',
  'editable':['head','crest','neck'],
  'hard_fixed':['thorax','waist','pelvis','forelimbs','hindlimbs','feet','tail'],
  'target_core_vertex_count':len(TARGET_CORE),
  'fixed_core_vertex_count':len(FIXED_CORE),
  'fixed_geometry_hash_before':before_fixed_hash,
  'fixed_geometry_hash_after':after_fixed_hash,
  'fixed_geometry_unchanged':True,
  'topology_unchanged':True,
  'landmarks':{
    'nose_tip_station_y':stations[0][0],
    'skull_rear_station_y':stations[4][0],
    'neck_base_station_y':stations[7][0],
    'thorax_lock_station_y':-.04,
    'crest_tips':crest_landmarks,
  },
  'intended_effects':[
    'shorter head-to-thorax span than rebuild-v1',
    'wider/deeper neck taper without tube read',
    'low rear-swept layered crest instead of tall paired prongs',
  ],
  'decision':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-a1-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1.blend'),compress=True)
print('VIBE_A1_EDIT_COMPLETE',json.dumps(report))
