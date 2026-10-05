"""Experimental Vibe Gate B2a-v1: proximal forelimb root massing.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
Use the accepted Gate-A3a station0->station1 centerline and elliptical radii
as the anatomical guide for the proximal forelimb root. Reshape only local
support-interior vertices whose elliptical cross-section deviates materially
from that accepted guide. Preserve axial position along the segment.

No topology change. B2b hindlimb remains blocked.
"""
import bpy, bmesh, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

# Accepted Gate A3a station0 -> station1 landmarks.
S0_X,S0_Y,S0_Z=0.115,-0.030,0.985
S0_LR,S0_SR=0.068,0.095
S1_X,S1_Y,S1_Z=0.148,0.035,0.845
S1_LR,S1_SR=0.056,0.070

# Local proximal forelimb support only.
XMIN,XMAX=0.055,0.215
YMIN,YMAX=-0.075,0.085
ZMIN,ZMAX=0.780,1.060

Q_ERROR_THRESHOLD=0.12
Q_MIN=0.45
Q_MAX=1.90
GAIN=0.45
MAX_DISP=0.0050
MAX_EXTENT_DRIFT=0.002
MIN_CANDIDATES=20
MAX_CANDIDATES=220
TOP_PER_SIDE=100

before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count=len(mesh.vertices); poly_count=len(mesh.polygons); edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside_support(co):
    ax=abs(co.x)
    return XMIN<=ax<=XMAX and YMIN<=co.y<=YMAX and ZMIN<=co.z<=ZMAX

support={i for i,co in enumerate(before) if inside_support(co)}
assert support, 'empty B2a-v1 support'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b); neighbors[b].add(a)

boundary={i for i in support if any(j not in support for j in neighbors[i])}
interior=support-boundary
assert interior, 'empty B2a-v1 interior'

initial=[co.copy() for co in before]
metrics={}
raw_candidates=[]

for i in sorted(interior):
    p=initial[i]
    sign=1.0 if p.x>=0 else -1.0
    s0=Vector((sign*S0_X,S0_Y,S0_Z))
    s1=Vector((sign*S1_X,S1_Y,S1_Z))
    axis=s1-s0
    denom=axis.length_squared
    assert denom>0

    t_raw=(p-s0).dot(axis)/denom
    if not (0.0<=t_raw<=1.0):
        continue
    t=t_raw
    center=s0+axis*t

    tangent=axis.normalized()
    lateral=Vector((1.0,0.0,0.0))
    lateral=lateral-tangent*lateral.dot(tangent)
    if lateral.length<=1e-12:
        lateral=Vector((1.0,0.0,0.0))
    lateral.normalize()
    sagittal=tangent.cross(lateral)
    if sagittal.length<=1e-12:
        sagittal=Vector((0.0,1.0,0.0))
    sagittal.normalize()

    lr=S0_LR+(S1_LR-S0_LR)*t
    sr=S0_SR+(S1_SR-S0_SR)*t
    d=p-center
    u=d.dot(lateral)
    v=d.dot(sagittal)
    q=math.sqrt((u/lr)**2 + (v/sr)**2)
    metrics[i]=(t,center,lateral,sagittal,lr,sr,u,v,q)

    if Q_MIN<=q<=Q_MAX and abs(q-1.0)>Q_ERROR_THRESHOLD:
        raw_candidates.append(i)

assert raw_candidates, 'no B2a-v1 elliptical-guide candidates'

# If the anatomical criterion is broad, keep the strongest deviations balanced
# per side rather than raising the displacement budget.
pos=sorted(
    [i for i in raw_candidates if initial[i].x>=0],
    key=lambda i:abs(metrics[i][8]-1.0),
    reverse=True
)[:TOP_PER_SIDE]
neg=sorted(
    [i for i in raw_candidates if initial[i].x<0],
    key=lambda i:abs(metrics[i][8]-1.0),
    reverse=True
)[:TOP_PER_SIDE]
candidates=sorted(pos+neg)
assert MIN_CANDIDATES<=len(candidates)<=MAX_CANDIDATES, (
    f'B2a-v1 candidate count {len(candidates)} outside [{MIN_CANDIDATES},{MAX_CANDIDATES}]'
)

q_before=[]
q_after=[]
for i in candidates:
    p=initial[i]
    t,center,lateral,sagittal,lr,sr,u,v,q=metrics[i]
    if q<=1e-12:
        continue

    # Preserve axial t and project only the cross-sectional offsets toward q=1.
    target=center + lateral*(u/q) + sagittal*(v/q)
    proposed=p+(target-p)*GAIN
    delta=proposed-p
    if delta.length>MAX_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_DISP

    # Maintain side; no sagittal-plane crossing.
    if p.x>0 and proposed.x<=0: proposed.x=1e-6
    if p.x<0 and proposed.x>=0: proposed.x=-1e-6

    d2=proposed-center
    u2=d2.dot(lateral)
    v2=d2.dot(sagittal)
    q2=math.sqrt((u2/lr)**2 + (v2/sr)**2)
    assert abs(q2-1.0)<=abs(q-1.0)+1e-8, f'elliptical guide error increased {i}'
    q_before.append(abs(q-1.0))
    q_after.append(abs(q2-1.0))
    mesh.vertices[i].co=proposed
mesh.update()

fixed=set(range(vert_count))-set(candidates)
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'fixed changed {i}'

# Support boundary must remain exact.
for i in boundary:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'boundary changed {i}'

# Topology exact.
assert len(mesh.vertices)==vert_count
assert len(mesh.polygons)==poly_count
assert len(mesh.edges)==edge_count
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Separate preserved meshes exact.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

disp={i:(mesh.vertices[i].co-before[i]).length for i in candidates}
vals=list(disp.values())
max_disp=max(vals) if vals else 0.0
mean_disp=sum(vals)/len(vals) if vals else 0.0
changed=sum(1 for d in vals if d>1e-10)
assert max_disp<=MAX_DISP+1e-7, f'max displacement {max_disp}'

src_ext={
 'x':(min(v.x for v in before),max(v.x for v in before)),
 'y':(min(v.y for v in before),max(v.y for v in before)),
 'z':(min(v.z for v in before),max(v.z for v in before)),
}
after=[v.co for v in mesh.vertices]
dst_ext={
 'x':(min(v.x for v in after),max(v.x for v in after)),
 'y':(min(v.y for v in after),max(v.y for v in after)),
 'z':(min(v.z for v in after),max(v.z for v in after)),
}
extent_drift={}
for ax in ('x','y','z'):
    extent_drift[ax]=max(abs(dst_ext[ax][0]-src_ext[ax][0]),abs(dst_ext[ax][1]-src_ext[ax][1]))
    assert extent_drift[ax]<=MAX_EXTENT_DRIFT+1e-9, f'{ax} extent drift {extent_drift[ax]}'

bm=bmesh.new(); bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, f'non-manifold edges {len(nonmanifold)}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(fixed):
        h.update(b'body'); h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode()); h.update(b'p'); h.update(str(i).encode()); h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B2a-v1-proximal-forelimb-root-massing',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'signed tapered elliptical projection using accepted A3a station0-to-station1 guide',
 'station0':{'abs_x':S0_X,'y':S0_Y,'z':S0_Z,'lateral_radius':S0_LR,'sagittal_radius':S0_SR},
 'station1':{'abs_x':S1_X,'y':S1_Y,'z':S1_Z,'lateral_radius':S1_LR,'sagittal_radius':S1_SR},
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'parameters':{
   'q_error_threshold':Q_ERROR_THRESHOLD,'q_min':Q_MIN,'q_max':Q_MAX,
   'gain':GAIN,'max_displacement':MAX_DISP,'top_per_side':TOP_PER_SIDE
 },
 'support_vertex_count':len(support),
 'boundary_vertex_count':len(boundary),
 'interior_vertex_count':len(interior),
 'raw_candidate_vertex_count':len(raw_candidates),
 'candidate_vertex_count':len(candidates),
 'selected_positive_count':len(pos),
 'selected_negative_count':len(neg),
 'changed_vertex_count':changed,
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'mean_abs_q_error_before':sum(q_before)/len(q_before),
 'mean_abs_q_error_after':sum(q_after)/len(q_after),
 'q_min_selected':min(metrics[i][8] for i in candidates),
 'q_max_selected':max(metrics[i][8] for i in candidates),
 'fixed_vertex_indices':sorted(fixed),
 'candidate_vertex_indices':sorted(candidates),
 'whole_body_extent_before':src_ext,
 'whole_body_extent_after':dst_ext,
 'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'fixed_geometry_hash':fixed_hash(),
 'outside_and_boundary_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_unchanged_from_b1c_v2':True,
 'vertex_count':len(mesh.vertices),
 'polygon_count':len(mesh.polygons),
 'edge_count':len(mesh.edges),
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b2a-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b2a-v1.blend'),compress=True)
print('VIBE_B2A_V1_EDIT_COMPLETE',json.dumps(report))
