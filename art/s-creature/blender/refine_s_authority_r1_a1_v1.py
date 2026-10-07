"""R1-A1 v1: localized surface continuity refinement.

Source: accepted R0 morphology output/S-authority-r0-a5-v2.blend.
Only shoulder/proximal-forelimb and pelvis/proximal-hindlimb supports are editable.
"""
import bpy,bmesh,os,json,math,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output');os.makedirs(OUT,exist_ok=True)

cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']
mesh=body.data

before=[v.co.copy() for v in mesh.vertices]
topology=[tuple(p.vertices) for p in mesh.polygons]
count=len(mesh.vertices)

# All separate meshes are exact locks.
other_fixed={}
other_topology={}
for o in cage.objects:
    if o.type=='MESH' and o!=body:
        other_fixed[o.name]=[v.co.copy() for v in o.data.vertices]
        other_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

camera_before={}
for stem in ('SIDE','FRONT','FRONT34','REAR34','BACK'):
    o=bpy.data.objects['S_REBUILD_CAM_'+stem]
    camera_before[o.name]=tuple(tuple(r) for r in o.matrix_world)

# Mesh adjacency.
adj=[set() for _ in range(count)]
for p in mesh.polygons:
    vs=list(p.vertices)
    for a,b in zip(vs,vs[1:]+vs[:1]):
        adj[a].add(b);adj[b].add(a)
assert all(adj)

def clamp(v,a=0.0,b=1.0):return max(a,min(b,v))
def smooth01(t):
    t=clamp(t)
    return t*t*(3.0-2.0*t)

def axis_weight(v,outer0,inner0,inner1,outer1):
    if v<=outer0 or v>=outer1:return 0.0
    if inner0<=v<=inner1:return 1.0
    if v<inner0:return smooth01((v-outer0)/(inner0-outer0))
    return smooth01((outer1-v)/(outer1-inner1))

def region_weight(p,kind):
    ax=abs(p.x)
    if kind=='fore':
        wy=axis_weight(p.y,-0.18,-0.10,0.14,0.26)
    else:
        wy=axis_weight(p.y,0.58,0.66,0.88,0.98)
    wz=axis_weight(p.z,0.70,0.78,1.04,1.12)
    wx=axis_weight(ax,0.06,0.085,0.20,0.235)
    return min(wx,wy,wz)

weights=[]
for p in before:
    weights.append(max(region_weight(p,'fore'),region_weight(p,'hind')))

editable=[i for i,w in enumerate(weights) if w>0]
fixed=[i for i,w in enumerate(weights) if w==0]
assert 200<=len(editable)<=3500,len(editable)

def roughness(coords,indices):
    vals=[]
    for i in indices:
        ns=adj[i]
        avg=sum((coords[j] for j in ns),Vector())/len(ns)
        vals.append((coords[i]-avg).length)
    return sum(vals)/len(vals),max(vals)

rough_before_mean,rough_before_max=roughness(before,editable)

coords=[p.copy() for p in before]
orig=[p.copy() for p in before]
LAM=0.38
MU=-0.40
CYCLES=4
CAP=0.025

def pass_once(coords,factor):
    nxt=[p.copy() for p in coords]
    for i in editable:
        w=weights[i]
        ns=adj[i]
        avg=sum((coords[j] for j in ns),Vector())/len(ns)
        p=coords[i]+(avg-coords[i])*(factor*w)
        delta=p-orig[i]
        if delta.length>CAP:
            p=orig[i]+delta.normalized()*CAP
        nxt[i]=p
    return nxt

for _ in range(CYCLES):
    coords=pass_once(coords,LAM)
    coords=pass_once(coords,MU)

for i in editable:
    mesh.vertices[i].co=coords[i]
mesh.update()

disps=[(mesh.vertices[i].co-before[i]).length for i in editable]
max_disp=max(disps)
mean_disp=sum(disps)/len(disps)
assert max_disp<=CAP+1e-8,max_disp

# Outside-support exact lock.
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]),f'fixed body changed {i}'

assert len(mesh.vertices)==count
assert [tuple(p.vertices) for p in mesh.polygons]==topology

after=[v.co.copy() for v in mesh.vertices]
rough_after_mean,rough_after_max=roughness(after,editable)
assert rough_after_mean < rough_before_mean,(rough_before_mean,rough_after_mean)

# Bounding-box drift.
def bbox(coords):
    return (
      (min(p.x for p in coords),min(p.y for p in coords),min(p.z for p in coords)),
      (max(p.x for p in coords),max(p.y for p in coords),max(p.z for p in coords)),
    )
bb0=bbox(before);bb1=bbox(after)
bbox_drift=max(abs(bb1[a][k]-bb0[a][k]) for a in (0,1) for k in range(3))
assert bbox_drift<=0.015+1e-9,bbox_drift

# Separate meshes exact.
for name,coords0 in other_fixed.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords0),name
    for i,co in enumerate(coords0):
        assert tuple(o.data.vertices[i].co)==tuple(co),f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==other_topology[name],name

for name,m in camera_before.items():
    assert tuple(tuple(r) for r in bpy.data.objects[name].matrix_world)==m,name

bm=bmesh.new();bm.from_mesh(mesh)
nm=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nm)==0,len(nm)

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R1-A1-v1-junction-continuity',
 'status':'REVIEW_PENDING','decision':'REVIEW_PENDING',
 'source':'S-authority-r0-a5-v2.blend',
 'r0_status':'ACCEPTED_R0_MORPHOLOGY',
 'output':'S-authority-r1-a1-v1.blend',
 'scope':'localized shoulder/proximal-forelimb + pelvis/proximal-hindlimb surface continuity',
 'method':{'type':'weighted Taubin','lambda':LAM,'mu':MU,'cycles':CYCLES,'max_displacement_cap':CAP},
 'editable_vertex_count':len(editable),
 'max_displacement':max_disp,'mean_displacement':mean_disp,
 'roughness_before_mean':rough_before_mean,'roughness_after_mean':rough_after_mean,
 'roughness_before_max':rough_before_max,'roughness_after_max':rough_after_max,
 'roughness_mean_ratio':rough_after_mean/rough_before_mean,
 'bbox_before':bb0,'bbox_after':bb1,'bbox_max_drift':bbox_drift,
 'outside_support_unchanged':True,'separate_meshes_unchanged':True,
 'body_topology_unchanged':True,'body_nonmanifold_edge_count':0,
 'camera_transforms_unchanged':True,
 'hard_fixed':['all body outside supports','head/neck','distal limbs','split feet','crest','tail blades','body topology','cameras'],
 'stop_rule':'render five views and STOP; R1-A2 blocked pending review'
}
json.dump(report,open(os.path.join(OUT,'S-authority-r1-a1-v1-validation.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r1-a1-v1.blend'),compress=True)
print('S_AUTHORITY_R1_A1_V1_EDIT_COMPLETE',json.dumps(report))
