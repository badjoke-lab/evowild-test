"""Authority reset R0-A2 v1: shoulder/thorax + waist tuck + pelvis mass only.

Source: output/S-authority-r0-v2.blend (accepted R0-A1)
Authority: references/00_s_type_modeling_image_v1.png

Hard lock:
- accepted R0-A1 head/neck coordinates
- accepted crest mesh
- body topology / vertex count
- distal limbs outside A2 envelope
- feet / toes
- tail beyond pelvis envelope
- review cameras

Stop after five-view render. R0-A3 remains blocked.
"""
import bpy, bmesh, os, json, math, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
os.makedirs(OUT,exist_ok=True)

AUTH_PATH=os.path.join(ROOT,'references','00_s_type_modeling_image_v1.png')
AUTH_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

assert os.path.getsize(AUTH_PATH)==1982782
assert sha256_file(AUTH_PATH)==AUTH_SHA

cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']
crest=bpy.data.objects['S_authority_r0_a1_v2_crest']

body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# Exact accepted A1 hard-lock region from the accepted v2 gate.
def in_a1_lock(p):
    return p.y <= -0.18 and p.z >= 0.84

# R0-A2 mass envelope. Front is negative Y.
def in_a2_envelope(p):
    return (-0.16 <= p.y <= 1.14) and p.z >= 0.66 and not in_a1_lock(p)

editable=[i for i,p in enumerate(body_before) if in_a2_envelope(p)]
fixed=[i for i,p in enumerate(body_before) if i not in set(editable)]
assert 400 <= len(editable) <= 5000, len(editable)

# Snapshot all non-body meshes: accepted crest and all toes must remain exact.
mesh_fixed={}
mesh_topology={}
for o in cage.objects:
    if o.type=='MESH' and o != body:
        mesh_fixed[o.name]=[v.co.copy() for v in o.data.vertices]
        mesh_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

# Snapshot review camera transforms.
camera_before={}
for stem in ('SIDE','FRONT','FRONT34','REAR34','BACK'):
    o=bpy.data.objects['S_REBUILD_CAM_'+stem]
    camera_before[o.name]=tuple(tuple(row) for row in o.matrix_world)

def clamp(v,a=0.0,b=1.0):
    return max(a,min(b,v))

def smooth01(t):
    t=clamp(t)
    return t*t*(3.0-2.0*t)

def bump(y,a,c,b):
    if y<=a or y>=b:
        return 0.0
    if y<c:
        return smooth01((y-a)/(c-a))
    return smooth01((b-y)/(b-c))

def band_stats(coords,y0,y1,zmin=0.66):
    pts=[p for p in coords if y0<=p.y<=y1 and p.z>=zmin]
    assert pts
    return {
      'max_abs_x':max(abs(p.x) for p in pts),
      'min_z':min(p.z for p in pts),
      'max_z':max(p.z for p in pts),
      'count':len(pts),
    }

before_stats={
  'shoulder':band_stats(body_before,-0.10,0.24,0.72),
  'waist':band_stats(body_before,0.40,0.66,0.66),
  'pelvis':band_stats(body_before,0.76,1.04,0.72),
}

moved=[]
weights_meta={'shoulder_nonzero':0,'waist_nonzero':0,'pelvis_nonzero':0}

for i in editable:
    v=body.data.vertices[i]
    p0=body_before[i]
    p=p0.copy()

    sw=bump(p0.y,-0.16,0.05,0.36)
    ww=bump(p0.y,0.26,0.52,0.78)
    pw=bump(p0.y,0.62,0.88,1.14)

    if sw>0: weights_meta['shoulder_nonzero']+=1
    if ww>0: weights_meta['waist_nonzero']+=1
    if pw>0: weights_meta['pelvis_nonzero']+=1

    # Lateral athletic mass rhythm:
    # broad shoulder -> narrow racing waist -> substantial pelvis.
    x_scale=1.0 + 0.42*sw - 0.26*ww + 0.34*pw
    p.x *= x_scale

    # Shoulder/chest: deeper ventral mass plus modest dorsal/scapular lift.
    sh_vent=clamp((0.98-p0.z)/0.30)
    sh_dors=clamp((p0.z-0.98)/0.24)
    p.z += (-0.105*sw*sh_vent) + (0.035*sw*sh_dors)

    # Waist: authority requires a deep abdominal tuck. Raise ventral abdomen,
    # leave the dorsal line essentially unchanged.
    waist_vent=clamp((0.98-p0.z)/0.32)
    p.z += 0.145*ww*waist_vent

    # Pelvis/upper hindquarter: restore usable sprint mass and depth.
    pel_vent=clamp((0.98-p0.z)/0.30)
    pel_dors=clamp((p0.z-0.98)/0.24)
    p.z += (-0.055*pw*pel_vent) + (0.045*pw*pel_dors)

    d=(p-p0).length
    if d>1e-12:
        moved.append((i,d))
        v.co=p

assert moved
max_disp=max(d for _,d in moved)
mean_disp=sum(d for _,d in moved)/len(moved)
assert max_disp <= 0.19 + 1e-9, max_disp

# Body topology is immutable.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology

# Every vertex outside A2 envelope remains exact.
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

# Explicit accepted R0-A1 lock.
a1_locked=[i for i,p in enumerate(body_before) if in_a1_lock(p)]
assert a1_locked
for i in a1_locked:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'R0-A1 changed {i}'

# All non-body meshes remain exact, including accepted crest and every toe.
for name,coords in mesh_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords), name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==mesh_topology[name], name

# Review cameras remain exact.
for name,m in camera_before.items():
    o=bpy.data.objects[name]
    assert tuple(tuple(row) for row in o.matrix_world)==m, name

bm=bmesh.new()
bm.from_mesh(body.data)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, len(nonmanifold)

after_coords=[v.co.copy() for v in body.data.vertices]
after_stats={
  'shoulder':band_stats(after_coords,-0.10,0.24,0.72),
  'waist':band_stats(after_coords,0.40,0.66,0.66),
  'pelvis':band_stats(after_coords,0.76,1.04,0.72),
}

shoulder_width_ratio=after_stats['shoulder']['max_abs_x']/before_stats['shoulder']['max_abs_x']
waist_width_ratio=after_stats['waist']['max_abs_x']/before_stats['waist']['max_abs_x']
pelvis_width_ratio=after_stats['pelvis']['max_abs_x']/before_stats['pelvis']['max_abs_x']
waist_floor_raise=after_stats['waist']['min_z']-before_stats['waist']['min_z']

assert shoulder_width_ratio >= 1.10, shoulder_width_ratio
assert waist_width_ratio <= 0.94, waist_width_ratio
assert pelvis_width_ratio >= 1.08, pelvis_width_ratio
assert waist_floor_raise >= 0.025, waist_floor_raise

report={
  'lane':'exp/s-creature-vibe-modeling',
  'gate':'R0-A2-v1-authority-body-mass',
  'status':'REVIEW_PENDING',
  'decision':'REVIEW_PENDING',
  'authority_image':'references/00_s_type_modeling_image_v1.png',
  'authority_sha256':AUTH_SHA,
  'source':'S-authority-r0-v2.blend',
  'accepted_prior_gate':'R0-A1 v2',
  'output':'S-authority-r0-a2-v1.blend',
  'scope':'shoulder/anterior thorax + waist tuck + pelvis/upper hindquarter only',
  'a2_envelope':{'y':[-0.16,1.14],'z_min':0.66},
  'mass_fields':{
    'shoulder':{'support_y':[-0.16,0.36],'center_y':0.05,'max_lateral_gain':0.42,'max_ventral_deepen':0.105,'max_dorsal_lift':0.035},
    'waist':{'support_y':[0.26,0.78],'center_y':0.52,'max_lateral_reduction':0.26,'max_ventral_tuck':0.145},
    'pelvis':{'support_y':[0.62,1.14],'center_y':0.88,'max_lateral_gain':0.34,'max_ventral_deepen':0.055,'max_dorsal_lift':0.045},
  },
  'hard_fixed':['accepted R0-A1 head/neck','accepted crest mesh','body topology','outside A2 envelope','distal limbs outside envelope','all toe meshes','tail beyond envelope','review cameras'],
  'body_vertex_count':body_count,
  'editable_vertex_count':len(editable),
  'moved_vertex_count':len(moved),
  'max_displacement':max_disp,
  'mean_displacement':mean_disp,
  'a1_locked_vertex_count':len(a1_locked),
  'a1_geometry_unchanged':True,
  'crest_geometry_unchanged':True,
  'other_meshes_unchanged':True,
  'body_topology_unchanged':True,
  'body_nonmanifold_edge_count':0,
  'camera_transforms_unchanged':True,
  'weights_meta':weights_meta,
  'before_stats':before_stats,
  'after_stats':after_stats,
  'shoulder_width_ratio':shoulder_width_ratio,
  'waist_width_ratio':waist_width_ratio,
  'pelvis_width_ratio':pelvis_width_ratio,
  'waist_floor_raise':waist_floor_raise,
  'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A3 blocked pending actual-image review'
}

with open(os.path.join(OUT,'S-authority-r0-a2-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a2-v1.blend'),compress=True)
print('S_AUTHORITY_R0_A2_V1_EDIT_COMPLETE',json.dumps(report))
