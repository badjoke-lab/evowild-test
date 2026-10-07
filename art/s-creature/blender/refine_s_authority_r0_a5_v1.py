"""Authority reset R0-A5 v1: long layered blade/feather tail.

Source: accepted output/S-authority-r0-a4-v3.blend.

Editable:
- continuous-body tail support only,
- newly added tail blade objects.

Everything else remains exact.
"""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
AUTH_PATH=os.path.join(ROOT,'references','00_s_type_modeling_image_v1.png')
AUTH_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

assert os.path.getsize(AUTH_PATH)==1982782
assert sha256_file(AUTH_PATH)==AUTH_SHA

cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']

body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# Existing meshes (crest + accepted split feet etc.) are exact locks.
mesh_fixed={}
mesh_topology={}
for o in cage.objects:
    if o.type=='MESH' and o!=body:
        mesh_fixed[o.name]=[v.co.copy() for v in o.data.vertices]
        mesh_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

camera_before={}
for stem in ('SIDE','FRONT','FRONT34','REAR34','BACK'):
    o=bpy.data.objects['S_REBUILD_CAM_'+stem]
    camera_before[o.name]=tuple(tuple(row) for row in o.matrix_world)

ROOT_Y=1.10
TAIL_Z_MIN=0.82
TAIL_ABS_X_MAX=0.13

def in_tail_support(p):
    return p.y>=ROOT_Y and p.z>=TAIL_Z_MIN and abs(p.x)<=TAIL_ABS_X_MAX

editable=[i for i,p in enumerate(body_before) if in_tail_support(p)]
editable_set=set(editable)
fixed=[i for i in range(body_count) if i not in editable_set]
assert 40 <= len(editable) <= 1800,len(editable)

source_max_y=max(body_before[i].y for i in editable)
source_min_y=min(body_before[i].y for i in editable)
assert source_max_y > 1.55,(source_min_y,source_max_y)

def clamp(v,a=0.0,b=1.0): return max(a,min(b,v))
def smooth01(t):
    t=clamp(t)
    return t*t*(3.0-2.0*t)

moved=[]
for i in editable:
    v=body.data.vertices[i]
    p0=body_before[i]
    p=p0.copy()

    t=clamp((p0.y-ROOT_Y)/(source_max_y-ROOT_Y))
    e=smooth01(t)

    # Long but light central tail core.
    p.y += 0.34*e
    p.x *= 1.0-0.48*e

    # Compress vertical thickness toward a gently lifting centerline.
    target_cz=0.965+0.055*t
    p.z = p.z + (target_cz-p.z)*(0.46*e) + 0.012*e

    d=(p-p0).length
    if d>1e-12:
        v.co=p
        moved.append((i,d))

assert moved
max_disp=max(d for _,d in moved)
new_core_max_y=max(body.data.vertices[i].co.y for i in editable)
assert 1.90 <= new_core_max_y <= 2.05,new_core_max_y
assert max_disp <= 0.36+1e-9,max_disp

# Hard lock outside tail support.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]),f'fixed body changed {i}'

# Layered laminae. Tail direction is +Y.
def qbez(a,b,c,t):
    u=1.0-t
    return a*(u*u)+b*(2*u*t)+c*(t*t)

def profile(vals,t):
    a,b,c=vals
    if t<=0.5:
        s=t/0.5
        return a+(b-a)*s
    s=(t-0.5)/0.5
    return b+(c-b)*s

def make_blade(spec):
    root=Vector(spec['root']); ctrl=Vector(spec['ctrl']); tip=Vector(spec['tip'])
    roll=math.radians(spec['roll_deg'])
    verts=[]; faces=[]; rings=[]; centers=[]
    sections=12
    for si in range(sections):
        t=si/(sections-1)
        center=qbez(root,ctrl,tip,t)
        tangent=(ctrl-root)*(2*(1-t))+(tip-ctrl)*(2*t)
        if tangent.length==0: tangent=Vector((0,1,0))
        tangent.normalize()

        lateral=Vector((1,0,0))
        lateral=lateral-tangent*lateral.dot(tangent)
        if lateral.length<1e-8: lateral=Vector((1,0,0))
        lateral.normalize()

        broad=tangent.cross(lateral)
        if broad.length<1e-8: broad=Vector((0,0,1))
        broad.normalize()

        # Roll broad plate around tail tangent to make layering readable in back view.
        broad_r=broad*math.cos(roll)+lateral*math.sin(roll)
        thin_r=lateral*math.cos(roll)-broad*math.sin(roll)
        broad_r.normalize(); thin_r.normalize()

        hw=profile(spec['broad'],t)
        ht=profile(spec['thin'],t)
        ring=[]
        for sb,st in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=center+broad_r*(sb*hw)+thin_r*(st*ht)
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring); centers.append(tuple(center))

    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))

    m=bpy.data.meshes.new(spec['name']+'_mesh')
    m.from_pydata(verts,[],faces); m.update()
    o=bpy.data.objects.new(spec['name'],m); cage.objects.link(o)
    for p in m.polygons: p.use_smooth=False

    bm=bmesh.new(); bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    nm=[e for e in bm.edges if len(e.link_faces)!=2]
    bm.to_mesh(m); bm.free()
    assert not nm,spec['name']
    return o,centers

blade_specs=[
 dict(name='S_tail_blade_center',
      root=(0.000,1.16,1.015),ctrl=(0.000,1.58,1.070),tip=(0.000,2.20,1.105),
      broad=(0.035,0.075,0.010),thin=(0.006,0.005,0.0015),roll_deg=0),

 dict(name='S_tail_blade_upper_L',
      root=(-0.018,1.17,1.020),ctrl=(-0.035,1.55,1.100),tip=(-0.060,2.12,1.185),
      broad=(0.034,0.070,0.010),thin=(0.006,0.005,0.0015),roll_deg=-25),
 dict(name='S_tail_blade_upper_R',
      root=( 0.018,1.17,1.020),ctrl=( 0.035,1.55,1.100),tip=( 0.060,2.12,1.185),
      broad=(0.034,0.070,0.010),thin=(0.006,0.005,0.0015),roll_deg= 25),

 dict(name='S_tail_blade_mid_L',
      root=(-0.022,1.20,0.995),ctrl=(-0.045,1.56,0.995),tip=(-0.075,2.04,0.985),
      broad=(0.032,0.066,0.009),thin=(0.0055,0.0048,0.0015),roll_deg=-32),
 dict(name='S_tail_blade_mid_R',
      root=( 0.022,1.20,0.995),ctrl=( 0.045,1.56,0.995),tip=( 0.075,2.04,0.985),
      broad=(0.032,0.066,0.009),thin=(0.0055,0.0048,0.0015),roll_deg= 32),

 dict(name='S_tail_blade_lower_L',
      root=(-0.018,1.23,0.965),ctrl=(-0.040,1.57,0.915),tip=(-0.065,1.96,0.855),
      broad=(0.030,0.060,0.008),thin=(0.0050,0.0045,0.0013),roll_deg=-20),
 dict(name='S_tail_blade_lower_R',
      root=( 0.018,1.23,0.965),ctrl=( 0.040,1.57,0.915),tip=( 0.065,1.96,0.855),
      broad=(0.030,0.060,0.008),thin=(0.0050,0.0045,0.0013),roll_deg= 20),
]

new_blades=[]
blade_meta=[]
for spec in blade_specs:
    o,centers=make_blade(spec)
    new_blades.append(o)
    blade_meta.append({
      'name':spec['name'],'root':spec['root'],'ctrl':spec['ctrl'],'tip':spec['tip'],
      'broad':spec['broad'],'thin':spec['thin'],'roll_deg':spec['roll_deg'],'centers':centers
    })

assert len(new_blades)==7
longest_tip=max(spec['tip'][1] for spec in blade_specs)
assert 2.18 <= longest_tip <= 2.22,longest_tip

# Existing mesh geometry (feet, crest) remains exact.
for name,coords in mesh_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords),name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co),f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==mesh_topology[name],name

for name,m in camera_before.items():
    assert tuple(tuple(row) for row in bpy.data.objects[name].matrix_world)==m,name

bm=bmesh.new(); bm.from_mesh(body.data)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0,len(nonmanifold)

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R0-A5-v1-authority-long-layered-tail',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'authority_sha256':AUTH_SHA,
 'source':'S-authority-r0-a4-v3.blend',
 'accepted_prior_gates':['R0-A1','R0-A2','R0-A3','R0-A4'],
 'output':'S-authority-r0-a5-v1.blend',
 'scope':'continuous-body tail core + seven new layered tail laminae only',
 'tail_support':{'source_y_min':ROOT_Y,'z_min':TAIL_Z_MIN,'abs_x_max':TAIL_ABS_X_MAX},
 'source_tail_support_vertex_count':len(editable),
 'source_tail_max_y':source_max_y,
 'new_core_max_y':new_core_max_y,
 'core_max_displacement':max_disp,
 'blade_count':len(new_blades),
 'blade_objects':[o.name for o in new_blades],
 'blade_meta':blade_meta,
 'longest_blade_tip_y':longest_tip,
 'hard_fixed':['all body vertices outside tail support','R0-A1/A2/A3 body outside support','all R0-A4 foot meshes','crest','body topology','cameras','all pre-existing non-body meshes'],
 'outside_tail_support_unchanged':True,
 'preexisting_meshes_unchanged':True,
 'feet_geometry_unchanged':True,
 'crest_geometry_unchanged':True,
 'body_topology_unchanged':True,
 'body_nonmanifold_edge_count':0,
 'camera_transforms_unchanged':True,
 'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A6 blocked pending R0-A5 review'
}

json.dump(report,open(os.path.join(OUT,'S-authority-r0-a5-v1-validation.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a5-v1.blend'),compress=True)
print('S_AUTHORITY_R0_A5_V1_EDIT_COMPLETE',json.dumps(report))
