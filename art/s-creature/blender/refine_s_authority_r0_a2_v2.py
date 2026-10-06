"""Authority reset R0-A2 v2: central-body-weighted shoulder/tuck/pelvis correction.

Source: output/S-authority-r0-v2.blend (accepted R0-A1; v1 A2 is NOT input)
Authority: references/00_s_type_modeling_image_v1.png

R0-A3 remains blocked.
"""
import bpy, bmesh, os, json, hashlib

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

def centralness(p):
    ax=abs(p.x)
    if ax<=0.11:
        return 1.0
    if ax>=0.21:
        return 0.0
    return 1.0-smooth01((ax-0.11)/0.10)

def in_a1_lock(p):
    return p.y <= -0.18 and p.z >= 0.84

def in_a2_envelope(p):
    return (-0.16 <= p.y <= 1.14) and p.z >= 0.66 and not in_a1_lock(p)

editable=[i for i,p in enumerate(body_before) if in_a2_envelope(p)]
editable_set=set(editable)
fixed=[i for i in range(body_count) if i not in editable_set]
assert 400 <= len(editable) <= 5000, len(editable)

# Lock all non-body geometry.
mesh_fixed={}
mesh_topology={}
for o in cage.objects:
    if o.type=='MESH' and o != body:
        mesh_fixed[o.name]=[v.co.copy() for v in o.data.vertices]
        mesh_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

camera_before={}
for stem in ('SIDE','FRONT','FRONT34','REAR34','BACK'):
    o=bpy.data.objects['S_REBUILD_CAM_'+stem]
    camera_before[o.name]=tuple(tuple(row) for row in o.matrix_world)

# Metric sets are selected from source coordinates and reused after deformation.
def select_metric(y0,y1,zmin=0.66,xmax=0.16):
    ids=[i for i,p in enumerate(body_before)
         if y0<=p.y<=y1 and p.z>=zmin and abs(p.x)<=xmax]
    assert ids
    return ids

def stats(coords,ids):
    pts=[coords[i] for i in ids]
    return {
      'max_abs_x':max(abs(p.x) for p in pts),
      'min_z':min(p.z for p in pts),
      'max_z':max(p.z for p in pts),
      'count':len(pts),
    }

metric_ids={
  'shoulder':select_metric(-0.10,0.24,0.72,0.16),
  'waist':select_metric(0.40,0.66,0.66,0.16),
  'pelvis':select_metric(0.76,1.04,0.72,0.16),
}
before_stats={k:stats(body_before,ids) for k,ids in metric_ids.items()}

moved=[]
outer_root_moved=[]
weight_counts={'shoulder_nonzero':0,'waist_nonzero':0,'pelvis_nonzero':0}

for i in editable:
    v=body.data.vertices[i]
    p0=body_before[i]
    p=p0.copy()

    sw=bump(p0.y,-0.16,0.05,0.36)
    ww=bump(p0.y,0.26,0.52,0.78)
    pw=bump(p0.y,0.62,0.88,1.14)
    cn=centralness(p0)

    if sw>0: weight_counts['shoulder_nonzero']+=1
    if ww>0: weight_counts['waist_nonzero']+=1
    if pw>0: weight_counts['pelvis_nonzero']+=1

    # Strong axial-torso effect, very small residual on outer proximal roots.
    lateral_strength=0.12+0.88*cn
    vertical_mass_strength=0.18+0.82*cn
    waist_vertical_strength=0.25+0.75*cn

    x_scale=(
      1.0
      + 0.30*sw*lateral_strength
      - 0.20*ww*lateral_strength
      + 0.28*pw*lateral_strength
    )
    p.x *= x_scale

    sh_vent=clamp((0.98-p0.z)/0.30)
    sh_dors=clamp((p0.z-0.98)/0.24)
    p.z += (
      -0.085*sw*sh_vent*vertical_mass_strength
      +0.030*sw*sh_dors*vertical_mass_strength
    )

    waist_vent=clamp((0.98-p0.z)/0.32)
    p.z += 0.125*ww*waist_vent*waist_vertical_strength

    pel_vent=clamp((0.98-p0.z)/0.30)
    pel_dors=clamp((p0.z-0.98)/0.24)
    p.z += (
      -0.045*pw*pel_vent*vertical_mass_strength
      +0.050*pw*pel_dors*vertical_mass_strength
    )

    d=(p-p0).length
    if d>1e-12:
        moved.append((i,d))
        if abs(p0.x)>=0.18:
            outer_root_moved.append((i,d))
        v.co=p

assert moved
max_disp=max(d for _,d in moved)
mean_disp=sum(d for _,d in moved)/len(moved)
outer_root_max=max((d for _,d in outer_root_moved),default=0.0)
assert max_disp <= 0.16 + 1e-9, max_disp
assert outer_root_max <= 0.065 + 1e-9, outer_root_max

# Exact hard locks.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

a1_locked=[i for i,p in enumerate(body_before) if in_a1_lock(p)]
assert a1_locked
for i in a1_locked:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'R0-A1 changed {i}'

for name,coords in mesh_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords), name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==mesh_topology[name], name

for name,m in camera_before.items():
    assert tuple(tuple(row) for row in bpy.data.objects[name].matrix_world)==m, name

bm=bmesh.new()
bm.from_mesh(body.data)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, len(nonmanifold)

after_coords=[v.co.copy() for v in body.data.vertices]
after_stats={k:stats(after_coords,ids) for k,ids in metric_ids.items()}

shoulder_width_ratio=after_stats['shoulder']['max_abs_x']/before_stats['shoulder']['max_abs_x']
waist_width_ratio=after_stats['waist']['max_abs_x']/before_stats['waist']['max_abs_x']
pelvis_width_ratio=after_stats['pelvis']['max_abs_x']/before_stats['pelvis']['max_abs_x']
waist_floor_raise=after_stats['waist']['min_z']-before_stats['waist']['min_z']

assert 1.12 <= shoulder_width_ratio <= 1.34, shoulder_width_ratio
assert 0.78 <= waist_width_ratio <= 0.94, waist_width_ratio
assert 1.10 <= pelvis_width_ratio <= 1.32, pelvis_width_ratio
assert waist_floor_raise >= 0.020, waist_floor_raise

report={
  'lane':'exp/s-creature-vibe-modeling',
  'gate':'R0-A2-v2-authority-body-mass',
  'status':'REVIEW_PENDING',
  'decision':'REVIEW_PENDING',
  'authority_image':'references/00_s_type_modeling_image_v1.png',
  'authority_sha256':AUTH_SHA,
  'source':'S-authority-r0-v2.blend',
  'source_policy':'accepted R0-A1 source; R0-A2 v1 not used as geometry input',
  'prior_review':'S_AUTHORITY_R0_A2_V1_REVIEW.md',
  'output':'S-authority-r0-a2-v2.blend',
  'scope':'central-body-weighted shoulder/anterior thorax + waist tuck + pelvis/rump only',
  'a2_envelope':{'y':[-0.16,1.14],'z_min':0.66},
  'lateral_falloff':{'full_strength_abs_x_max':0.11,'zero_strength_abs_x_min':0.21,'residual_floor':0.12},
  'fields':{
    'shoulder':{'support_y':[-0.16,0.36],'center_y':0.05,'central_lateral_gain':0.30,'ventral_deepen':0.085,'dorsal_lift':0.030},
    'waist':{'support_y':[0.26,0.78],'center_y':0.52,'central_lateral_reduction':0.20,'ventral_tuck':0.125},
    'pelvis':{'support_y':[0.62,1.14],'center_y':0.88,'central_lateral_gain':0.28,'ventral_deepen':0.045,'dorsal_lift':0.050},
  },
  'hard_fixed':['accepted R0-A1 head/neck','accepted crest mesh','body topology','outside A2 envelope','feet/toes','tail beyond envelope','review cameras'],
  'body_vertex_count':body_count,
  'editable_vertex_count':len(editable),
  'moved_vertex_count':len(moved),
  'max_displacement':max_disp,
  'mean_displacement':mean_disp,
  'outer_root_vertex_count':len(outer_root_moved),
  'outer_root_max_displacement':outer_root_max,
  'a1_locked_vertex_count':len(a1_locked),
  'a1_geometry_unchanged':True,
  'crest_geometry_unchanged':True,
  'other_meshes_unchanged':True,
  'body_topology_unchanged':True,
  'body_nonmanifold_edge_count':0,
  'camera_transforms_unchanged':True,
  'weight_counts':weight_counts,
  'before_stats':before_stats,
  'after_stats':after_stats,
  'shoulder_width_ratio':shoulder_width_ratio,
  'waist_width_ratio':waist_width_ratio,
  'pelvis_width_ratio':pelvis_width_ratio,
  'waist_floor_raise':waist_floor_raise,
  'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A3 blocked pending actual-image review'
}

with open(os.path.join(OUT,'S-authority-r0-a2-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a2-v2.blend'),compress=True)
print('S_AUTHORITY_R0_A2_V2_EDIT_COMPLETE',json.dumps(report))
