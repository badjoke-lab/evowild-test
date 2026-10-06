"""Authority reset R0-A1 v1: rebuild head + paired crest + neck line only.

Highest authority:
  references/00_s_type_modeling_image_v1.png
Source:
  output/S-vibe-b2a-v5.blend (technical donor only; globally rejected)
Output:
  output/S-authority-r0-v1.blend

No torso, limb, foot, tail, topology, or camera edits are allowed here.
"""
import bpy, bmesh, os, json, math, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
os.makedirs(OUT,exist_ok=True)

AUTH_PATH=os.path.join(ROOT,'references','00_s_type_modeling_image_v1.png')
assert os.path.exists(AUTH_PATH)
assert os.path.getsize(AUTH_PATH)==1982782

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

AUTH_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert sha256_file(AUTH_PATH)==AUTH_SHA

cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']

# Snapshot body topology + all source coordinates.
body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# R0-A1 support excludes the forelimb root at y ~ -0.09 and all torso mass.
# Front is -Y. Only the high forward head/neck body is editable.
def in_a1_support(co):
    return co.y <= -0.18 and co.z >= 0.84

editable=[i for i,co in enumerate(body_before) if in_a1_support(co)]
fixed=[i for i,co in enumerate(body_before) if not in_a1_support(co)]
assert 100 <= len(editable) <= 15000, len(editable)
support_min_y=min(body_before[i].y for i in editable)
HEAD_SPLIT=support_min_y+0.25
NECK_BACK=-0.18
assert support_min_y < HEAD_SPLIT < NECK_BACK

# Snapshot every non-body mesh. Old crest is the only object allowed to be replaced.
old_crests=[o for o in cage.objects if o.type=='MESH' and o.name.startswith('S_reference_crest')]
assert len(old_crests)==1, [o.name for o in old_crests]
old_crest=old_crests[0]

other_fixed={}
other_topology={}
for o in cage.objects:
    if o.type=='MESH' and o not in (body,old_crest):
        other_fixed[o.name]=[v.co.copy() for v in o.data.vertices]
        other_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

# ----------------------------
# Head + neck line deformation
# ----------------------------

def clamp(v,a=0.0,b=1.0):
    return max(a,min(b,v))

moved=[]
for i in editable:
    v=body.data.vertices[i]
    p=v.co.copy()

    if p.y <= HEAD_SPLIT:
        # Longer, lower wedge head. Normalize against the donor's actual
        # forward extent instead of assuming the obsolete -1.0 Gate-A range.
        denom=max(HEAD_SPLIT-support_min_y,1e-6)
        frontness=clamp((HEAD_SPLIT-p.y)/denom)
        p.y -= 0.165*(frontness**1.10)
        p.z -= 0.050 + 0.055*frontness
        p.x *= 1.0 - 0.10*frontness
    else:
        # Neck: lower upper line, broaden/deepen mid-neck, taper back to the
        # untouched shoulder boundary at y=-0.18.
        u=clamp((p.y-HEAD_SPLIT)/(NECK_BACK-HEAD_SPLIT))
        env=math.sin(math.pi*u)
        old_cz=1.285 + (1.005-1.285)*u
        p.x *= 1.0 + 0.28*env
        p.z = old_cz + (p.z-old_cz)*(1.0+0.20*env)
        p.z -= 0.050*(1.0-u) + 0.020*env
        p.y -= 0.032*(1.0-u)*env

    d=(p-v.co).length
    if d>1e-12:
        moved.append((i,d))
        v.co=p

assert moved
max_disp=max(d for _,d in moved)
assert max_disp <= 0.24 + 1e-9, max_disp
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology

# Hard lock: every body vertex outside the declared support remains bit-exact.
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

# --------------------------------
# Rebuild crest from authority read
# --------------------------------
bpy.data.objects.remove(old_crest,do_unlink=True)

# Two dominant paired blades + compact secondary blades.
# Primary blades own the silhouette; secondaries remain short at the skull base.
blade_specs=[
    dict(name='dominant_L',
         root=(-0.052,-0.535,1.300),ctrl=(-0.074,-0.185,1.555),tip=(-0.082,0.235,1.725),
         widths=(0.060,0.108,0.020),thickness=(0.009,0.008,0.002),roll_deg=-24.0,kind='dominant'),
    dict(name='dominant_R',
         root=( 0.052,-0.535,1.300),ctrl=( 0.074,-0.185,1.555),tip=( 0.082,0.235,1.725),
         widths=(0.060,0.108,0.020),thickness=(0.009,0.008,0.002),roll_deg= 24.0,kind='dominant'),

    dict(name='secondary_upper_L',
         root=(-0.060,-0.550,1.275),ctrl=(-0.070,-0.360,1.405),tip=(-0.074,-0.090,1.500),
         widths=(0.043,0.060,0.014),thickness=(0.007,0.006,0.002),roll_deg=-18.0,kind='secondary'),
    dict(name='secondary_upper_R',
         root=( 0.060,-0.550,1.275),ctrl=( 0.070,-0.360,1.405),tip=( 0.074,-0.090,1.500),
         widths=(0.043,0.060,0.014),thickness=(0.007,0.006,0.002),roll_deg= 18.0,kind='secondary'),

    dict(name='secondary_low_L',
         root=(-0.056,-0.565,1.250),ctrl=(-0.064,-0.430,1.330),tip=(-0.068,-0.225,1.390),
         widths=(0.032,0.043,0.010),thickness=(0.006,0.005,0.0018),roll_deg=-14.0,kind='secondary'),
    dict(name='secondary_low_R',
         root=( 0.056,-0.565,1.250),ctrl=( 0.064,-0.430,1.330),tip=( 0.068,-0.225,1.390),
         widths=(0.032,0.043,0.010),thickness=(0.006,0.005,0.0018),roll_deg= 14.0,kind='secondary'),
]

def qbez(a,b,c,t):
    u=1.0-t
    return a*(u*u)+b*(2*u*t)+c*(t*t)

def profile(vals,t):
    a,b,c=vals
    if t<=0.48:
        s=t/0.48
        return a+(b-a)*s
    s=(t-0.48)/0.52
    return b+(c-b)*s

verts=[]
faces=[]
meta=[]
sections=11

for spec in blade_specs:
    r=Vector(spec['root'])
    q=Vector(spec['ctrl'])
    tip=Vector(spec['tip'])
    roll=math.radians(spec['roll_deg'])
    rings=[]
    centers=[]

    for si in range(sections):
        t=si/(sections-1)
        center=qbez(r,q,tip,t)
        tangent=(q-r)*(2*(1-t))+(tip-q)*(2*t)
        tyz=Vector((0,tangent.y,tangent.z))
        if tyz.length==0:
            tyz=Vector((0,1,0))
        tyz.normalize()

        sagittal_broad=Vector((0,-tyz.z,tyz.y))
        lateral=Vector((1,0,0))
        broad=(sagittal_broad*math.cos(roll))+(lateral*math.sin(roll))
        thin=(lateral*math.cos(roll))-(sagittal_broad*math.sin(roll))
        broad.normalize()
        thin.normalize()

        half_w=profile(spec['widths'],t)
        half_t=profile(spec['thickness'],t)
        ring=[]
        for sb,st in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=center+broad*(sb*half_w)+thin*(st*half_t)
            ring.append(len(verts))
            verts.append(tuple(p))
        rings.append(ring)
        centers.append(tuple(center))

    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))

    meta.append({
        'name':spec['name'],
        'kind':spec['kind'],
        'root':spec['root'],
        'ctrl':spec['ctrl'],
        'tip':spec['tip'],
        'widths':spec['widths'],
        'roll_deg':spec['roll_deg'],
        'centers':centers,
    })

mesh=bpy.data.meshes.new('S_authority_r0_a1_crest_mesh')
mesh.from_pydata(verts,[],faces)
mesh.update()
crest=bpy.data.objects.new('S_authority_r0_a1_crest',mesh)
cage.objects.link(crest)
for p in mesh.polygons:
    p.use_smooth=False

bm=bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
nonmanifold_crest=[e for e in bm.edges if len(e.link_faces)!=2]
bm.to_mesh(mesh)
bm.free()
assert not nonmanifold_crest

# Body remains manifold after coordinate-only edit.
bm=bmesh.new()
bm.from_mesh(body.data)
body_nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert not body_nonmanifold

# Every non-body/non-crest mesh remains exact.
for name,coords in other_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==other_topology[name], name

before_min_y=min(p.y for p in body_before if p.z>=0.84)
after_min_y=min(v.co.y for v in body.data.vertices if v.co.z>=0.84)
global_high_min_y_delta=before_min_y-after_min_y
forward_extension=max(body_before[i].y-body.data.vertices[i].co.y for i in editable)
assert forward_extension >= 0.10, forward_extension

dominants=[m for m in meta if m['kind']=='dominant']
assert len(dominants)==2
assert dominants[0]['tip'][0] < 0 < dominants[1]['tip'][0]
assert abs(dominants[0]['tip'][0]-dominants[1]['tip'][0]) >= 0.12

report={
    'lane':'exp/s-creature-vibe-modeling',
    'gate':'R0-A1-v1-authority-head-crest-neck',
    'status':'REVIEW_PENDING',
    'decision':'REVIEW_PENDING',
    'authority_image':'references/00_s_type_modeling_image_v1.png',
    'authority_sha256':AUTH_SHA,
    'source':'S-vibe-b2a-v5.blend',
    'source_role':'technical donor only; globally rejected morphology',
    'output':'S-authority-r0-v1.blend',
    'editable':['head body vertices in support','neck body vertices in support','crest replacement'],
    'body_support':'source-coordinate y <= -0.18 and z >= 0.84; head split derived from donor support_min_y + 0.25',
    'support_min_y':support_min_y,
    'head_split_y':HEAD_SPLIT,
    'hard_fixed':['all body vertices outside support','body topology','torso','limbs outside support','feet','all toes','tail','review cameras','all other mesh objects'],
    'body_vertex_count':body_count,
    'editable_body_vertex_count':len(editable),
    'moved_body_vertex_count':len(moved),
    'max_body_displacement':max_disp,
    'body_topology_unchanged':True,
    'fixed_body_vertices_unchanged':True,
    'other_meshes_unchanged':True,
    'body_nonmanifold_edge_count':0,
    'head_forward_extension':forward_extension,
    'global_high_min_y_delta':global_high_min_y_delta,
    'crest_object':crest.name,
    'crest_blade_count':len(blade_specs),
    'dominant_blade_count':2,
    'secondary_blade_count':4,
    'crest_nonmanifold_edge_count':0,
    'blade_meta':meta,
    'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK then STOP; R0-A2 blocked pending actual-image review'
}

with open(os.path.join(OUT,'S-authority-r0-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-v1.blend'),compress=True)
print('S_AUTHORITY_R0_A1_V1_EDIT_COMPLETE',json.dumps(report))
