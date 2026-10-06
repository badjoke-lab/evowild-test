"""Authority reset R0-A3 v1: fore/hind limb segment rhythm only.

Source: accepted output/S-authority-r0-a2-v2.blend
No feet/toes or tail edits. No topology change.
"""
import bpy,bmesh,os,json,hashlib
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
crest=bpy.data.objects['S_authority_r0_a1_v2_crest']

body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# Absolute-X centerline templates; mirrored by side sign.
FORE=[
 ((.155,.040,.82),1.45),
 ((.168,.105,.68),1.25),
 ((.163,-.030,.52),1.38),
 ((.155,-.170,.34),1.08),
 ((.150,-.235,.20),1.22),
 ((.150,-.255,.12),1.05),
]
HIND=[
 ((.155,.740,.82),1.55),
 ((.175,.665,.73),1.28),
 ((.169,.820,.568),1.42),
 ((.160,1.020,.34),1.10),
 ((.153,1.070,.22),1.24),
 ((.150,.990,.12),1.05),
]

def clamp(v,a=0.0,b=1.0): return max(a,min(b,v))

def signed_chain(template,sign):
    return [(Vector((sign*x,y,z)),s) for (x,y,z),s in template]

def nearest_on_chain(p,chain):
    best=None
    for si in range(len(chain)-1):
        a,sa=chain[si]; b,sb=chain[si+1]
        d=b-a
        denom=d.length_squared
        t=0.0 if denom==0 else clamp((p-a).dot(d)/denom)
        q=a+d*t
        dist=(p-q).length
        scale=sa+(sb-sa)*t
        if best is None or dist<best[0]:
            best=(dist,q,scale,si,t)
    return best

# Snapshot all non-body meshes and review cameras.
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

eligible={}
counts={'fore_L':0,'fore_R':0,'hind_L':0,'hind_R':0}
upper_before={'fore':[],'hind':[]}

for i,p in enumerate(body_before):
    ax=abs(p.x)
    if p.z < 0.12 or p.z > 0.84:
        continue
    if ax < 0.07:
        continue
    # Preserve the accepted axial shoulder/pelvis body in the high overlap zone.
    if p.z > 0.72 and ax < 0.11:
        continue

    sign=1 if p.x>=0 else -1
    family=None; template=None
    if -0.35 <= p.y < 0.28:
        family='fore'; template=FORE
    elif 0.48 < p.y <= 1.18:
        family='hind'; template=HIND
    else:
        continue

    chain=signed_chain(template,sign)
    dist,q,scale,seg,t=nearest_on_chain(p,chain)
    if dist > 0.10:
        continue

    key=family+'_'+('R' if sign>0 else 'L')
    eligible[i]=(family,sign,dist,q,scale,seg,t)
    counts[key]+=1
    if 0.62 <= p.z <= 0.82 and dist>1e-5:
        upper_before[family].append((i,dist,q.copy()))

assert sum(counts.values()) >= 120, counts
assert min(counts.values()) >= 20, counts

eligible_set=set(eligible)
fixed=[i for i in range(body_count) if i not in eligible_set]

moved=[]
for i,(family,sign,dist,q,scale,seg,t) in eligible.items():
    p0=body_before[i]
    p=q+(p0-q)*scale
    d=(p-p0).length
    if d>1e-12:
        body.data.vertices[i].co=p
        moved.append((i,d,family))

assert moved
max_disp=max(d for _,d,_ in moved)
mean_disp=sum(d for _,d,_ in moved)/len(moved)
assert max_disp <= 0.065 + 1e-9, max_disp

# Exact hard lock outside limb support.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

# Contact/foot body region remains exact.
foot_locked=[i for i,p in enumerate(body_before) if p.z<0.12]
for i in foot_locked:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'foot boundary changed {i}'

# All separate meshes remain exact, especially crest and toes.
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

# Measure upper-segment radial growth using the same source-space chain anchors.
upper_ratio={}
for family,items in upper_before.items():
    ratios=[]
    for i,rb,q in items:
        ra=(body.data.vertices[i].co-q).length
        ratios.append(ra/rb)
    assert ratios
    upper_ratio[family]=sum(ratios)/len(ratios)

assert upper_ratio['fore'] >= 1.20, upper_ratio
assert upper_ratio['hind'] >= 1.22, upper_ratio

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R0-A3-v1-authority-limb-rhythm',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'authority_sha256':AUTH_SHA,
 'source':'S-authority-r0-a2-v2.blend',
 'accepted_prior_gates':['R0-A1','R0-A2'],
 'output':'S-authority-r0-a3-v1.blend',
 'scope':'forelimb + hindlimb segment radial rhythm only',
 'support':{'z':[0.12,0.84],'outer_high_zone_abs_x_min':0.11,'chain_max_distance':0.10},
 'profiles':{'fore':FORE,'hind':HIND},
 'hard_fixed':['R0-A1 geometry','R0-A2 body mass outside limb support','all separate toe meshes','contact body region z<0.12','tail','cameras','body topology'],
 'body_vertex_count':body_count,
 'eligible_counts':counts,
 'moved_vertex_count':len(moved),
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'upper_radial_ratio':upper_ratio,
 'foot_locked_vertex_count':len(foot_locked),
 'outside_support_unchanged':True,
 'separate_meshes_unchanged':True,
 'crest_geometry_unchanged':True,
 'toe_geometry_unchanged':True,
 'body_topology_unchanged':True,
 'body_nonmanifold_edge_count':0,
 'camera_transforms_unchanged':True,
 'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A4 blocked pending R0-A3 review'
}
with open(os.path.join(OUT,'S-authority-r0-a3-v1-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a3-v1.blend'),compress=True)
print('S_AUTHORITY_R0_A3_V1_EDIT_COMPLETE',json.dumps(report))
