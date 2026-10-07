"""Authority reset R0-A3 v2: anisotropic fore/hind limb section shaping.

Source: accepted output/S-authority-r0-a2-v2.blend
Do not accumulate from R0-A3 v1.

Goal:
- upper segments: moderate lateral + sagittal mass
- joints: restrained lateral width + stronger directional sagittal depth
- distal shafts: slim laterally + modest sagittal depth
- contact / foot region exact

No topology, toe, tail, accepted A1/A2 outside-support, or camera edits.
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
crest=bpy.data.objects['S_authority_r0_a1_v2_crest']

body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# (abs_x, y, z, lateral_scale, sagittal_scale)
FORE=[
 (.155,.040,.82,1.28,1.34),
 (.168,.105,.68,1.10,1.20),
 (.163,-.030,.52,1.07,1.34),
 (.155,-.170,.34,.94,1.04),
 (.150,-.235,.20,1.00,1.14),
 (.150,-.255,.12,1.00,1.00),
]
HIND=[
 (.155,.740,.82,1.34,1.40),
 (.175,.665,.73,1.10,1.18),
 (.169,.820,.568,1.07,1.38),
 (.160,1.020,.34,.94,1.05),
 (.153,1.070,.22,1.00,1.14),
 (.150,.990,.12,1.00,1.00),
]

def clamp(v,a=0.0,b=1.0): return max(a,min(b,v))

def signed_chain(template,sign):
    return [(Vector((sign*x,y,z)),ls,ss) for x,y,z,ls,ss in template]

def nearest_on_chain(p,chain):
    best=None
    for si in range(len(chain)-1):
        a,la,sa=chain[si]
        b,lb,sb=chain[si+1]
        d=b-a
        denom=d.length_squared
        t=0.0 if denom==0 else clamp((p-a).dot(d)/denom)
        q=a+d*t
        dist=(p-q).length
        lat_scale=la+(lb-la)*t
        sag_scale=sa+(sb-sa)*t
        tangent=d.normalized() if d.length else Vector((0,0,-1))

        # Project world X into the cross-section plane orthogonal to tangent.
        lateral=Vector((1,0,0))
        lateral=lateral-tangent*lateral.dot(tangent)
        if lateral.length < 1e-9:
            lateral=Vector((1,0,0))
        lateral.normalize()

        sagittal=tangent.cross(lateral)
        if sagittal.length < 1e-9:
            sagittal=Vector((0,1,0))
        sagittal.normalize()

        if best is None or dist<best[0]:
            best=(dist,q,lat_scale,sag_scale,si,t,tangent,lateral,sagittal)
    return best

# All non-body meshes and cameras are exact hard locks.
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

# Metrics are measured against local cross-section axes from source geometry.
metric_sets={
 'upper_fore':[],
 'upper_hind':[],
 'joint_fore':[],
 'joint_hind':[],
 'distal_fore':[],
 'distal_hind':[],
}

for i,p in enumerate(body_before):
    ax=abs(p.x)
    if p.z < 0.12 or p.z > 0.84:
        continue
    # Keep accepted axial body in high overlap zone exact.
    if p.z > 0.72 and ax < 0.115:
        continue

    sign=1 if p.x>=0 else -1
    family=None; template=None
    if -0.35 <= p.y <= 0.28:
        family='fore'; template=FORE
    elif 0.48 <= p.y <= 1.18:
        family='hind'; template=HIND
    else:
        continue

    chain=signed_chain(template,sign)
    info=nearest_on_chain(p,chain)
    dist,q,lat_scale,sag_scale,seg,t,tangent,lateral,sagittal=info
    if dist > 0.095:
        continue

    radial=p-q
    lat0=radial.dot(lateral)
    sag0=radial.dot(sagittal)
    long0=radial.dot(tangent)

    # Require enough section radius for stable ratio metrics.
    eligible[i]=(family,sign,dist,q,lat_scale,sag_scale,seg,t,tangent,lateral,sagittal,lat0,sag0,long0)
    counts[family+'_'+('R' if sign>0 else 'L')]+=1

    z=p.z
    if 0.66 <= z <= 0.84:
        metric_sets['upper_'+family].append(i)
    if family=='fore' and 0.44 <= z <= 0.60:
        metric_sets['joint_fore'].append(i)
    if family=='hind' and 0.50 <= z <= 0.64:
        metric_sets['joint_hind'].append(i)
    if 0.20 <= z <= 0.40:
        metric_sets['distal_'+family].append(i)

assert sum(counts.values()) >= 120, counts
assert min(counts.values()) >= 20, counts

eligible_set=set(eligible)
fixed=[i for i in range(body_count) if i not in eligible_set]

moved=[]
for i,info in eligible.items():
    family,sign,dist,q,lat_scale,sag_scale,seg,t,tangent,lateral,sagittal,lat0,sag0,long0=info
    p0=body_before[i]

    # Preserve longitudinal placement; reshape only the local section.
    p=q + lateral*(lat0*lat_scale) + sagittal*(sag0*sag_scale) + tangent*long0
    d=(p-p0).length
    if d>1e-12:
        body.data.vertices[i].co=p
        moved.append((i,d,family))

assert moved
max_disp=max(d for _,d,_ in moved)
mean_disp=sum(d for _,d,_ in moved)/len(moved)
assert max_disp <= 0.055 + 1e-9, max_disp

# Hard locks.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i in fixed:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

foot_locked=[i for i,p in enumerate(body_before) if p.z<0.12]
for i in foot_locked:
    assert tuple(body.data.vertices[i].co)==tuple(body_before[i]), f'foot/contact changed {i}'

for name,coords in mesh_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords),name
    for j,co in enumerate(coords):
        assert tuple(o.data.vertices[j].co)==tuple(co), f'fixed mesh changed {name}:{j}'
    assert [tuple(p.vertices) for p in o.data.polygons]==mesh_topology[name],name

for name,m in camera_before.items():
    assert tuple(tuple(row) for row in bpy.data.objects[name].matrix_world)==m,name

bm=bmesh.new(); bm.from_mesh(body.data)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0,len(nonmanifold)

# Compute directional section-growth metrics using each source vertex's local axes.
def mean_ratio(indices,axis_name):
    vals=[]
    for i in indices:
        if i not in eligible:
            continue
        info=eligible[i]
        tangent,lateral,sagittal=info[8],info[9],info[10]
        p0=body_before[i]
        p1=body.data.vertices[i].co
        q=info[3]
        r0=p0-q
        r1=p1-q
        if axis_name=='lateral':
            a0=abs(r0.dot(lateral)); a1=abs(r1.dot(lateral))
        else:
            a0=abs(r0.dot(sagittal)); a1=abs(r1.dot(sagittal))
        if a0>0.004:
            vals.append(a1/a0)
    assert vals,(axis_name,len(indices))
    return sum(vals)/len(vals),len(vals)

upper_lat_fore,nulf=mean_ratio(metric_sets['upper_fore'],'lateral')
upper_lat_hind,nulh=mean_ratio(metric_sets['upper_hind'],'lateral')
joint_sag_fore,njsf=mean_ratio(metric_sets['joint_fore'],'sagittal')
joint_sag_hind,njsh=mean_ratio(metric_sets['joint_hind'],'sagittal')
distal_lat_fore,ndlf=mean_ratio(metric_sets['distal_fore'],'lateral')
distal_lat_hind,ndlh=mean_ratio(metric_sets['distal_hind'],'lateral')

assert 1.12 <= upper_lat_fore <= 1.30, upper_lat_fore
assert 1.15 <= upper_lat_hind <= 1.34, upper_lat_hind
assert joint_sag_fore >= 1.18, joint_sag_fore
assert joint_sag_hind >= 1.18, joint_sag_hind
assert distal_lat_fore <= 1.02, distal_lat_fore
assert distal_lat_hind <= 1.02, distal_lat_hind

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R0-A3-v2-authority-anisotropic-limb-rhythm',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'authority_sha256':AUTH_SHA,
 'source':'S-authority-r0-a2-v2.blend',
 'source_role':'accepted R0-A2 source; R0-A3 v1 not used as geometry input',
 'accepted_prior_gates':['R0-A1','R0-A2'],
 'output':'S-authority-r0-a3-v2.blend',
 'scope':'forelimb + hindlimb anisotropic segment section rhythm only',
 'support':{
   'z':[0.12,0.84],
   'fore_y':[-0.35,0.28],
   'hind_y':[0.48,1.18],
   'chain_max_distance':0.095,
   'high_overlap_lock':'z>0.72 and abs(x)<0.115'
 },
 'profiles':{'fore':FORE,'hind':HIND},
 'construction':'local chain cross-section: projected world-X lateral axis + YZ sagittal axis; longitudinal placement preserved',
 'hard_fixed':['R0-A1 head/crest/neck','R0-A2 body outside limb support','source z<0.12 contact region','all separate toe meshes','tail','cameras','body topology'],
 'body_vertex_count':body_count,
 'eligible_counts':counts,
 'moved_vertex_count':len(moved),
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'directional_metrics':{
   'upper_lateral_mean':{'fore':upper_lat_fore,'hind':upper_lat_hind,'sample_count_fore':nulf,'sample_count_hind':nulh},
   'joint_sagittal_mean':{'fore':joint_sag_fore,'hind':joint_sag_hind,'sample_count_fore':njsf,'sample_count_hind':njsh},
   'distal_lateral_mean':{'fore':distal_lat_fore,'hind':distal_lat_hind,'sample_count_fore':ndlf,'sample_count_hind':ndlh},
 },
 'foot_locked_vertex_count':len(foot_locked),
 'outside_support_unchanged':True,
 'separate_meshes_unchanged':True,
 'crest_geometry_unchanged':True,
 'toe_geometry_unchanged':True,
 'body_topology_unchanged':True,
 'body_nonmanifold_edge_count':0,
 'camera_transforms_unchanged':True,
 'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A4 blocked pending R0-A3 v2 review'
}
with open(os.path.join(OUT,'S-authority-r0-a3-v2-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a3-v2.blend'),compress=True)
print('S_AUTHORITY_R0_A3_V2_EDIT_COMPLETE',json.dumps(report))
