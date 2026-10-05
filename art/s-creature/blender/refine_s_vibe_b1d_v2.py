"""Experimental Vibe Gate B1d-v2: tapered shoulder-to-upper-limb bridge guide.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
The remaining angular forelimb attachment needs a continuous bridge axis, not
another isotropic smooth or single ellipsoid. Pull only support-interior
vertices that lie outside a mirrored tapered capsule guide connecting shoulder
mass to upper forelimb root.

No topology change.
"""
import bpy, bmesh, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

# Same refined local support as B1c/B1d-v1.
XMIN,XMAX=0.070,0.180
YMIN,YMAX=-0.090,0.105
ZMIN,ZMAX=0.900,1.105

SHOULDER_X=0.105
SHOULDER_Y=-0.050
SHOULDER_Z=1.030
LIMB_X=0.135
LIMB_Y=0.045
LIMB_Z=0.925
R0=0.082
R1=0.058
THRESHOLD_SCALE=1.06
GAIN=0.50
MAX_DISP=0.0048
MAX_EXTENT_DRIFT=0.002
MIN_CANDIDATES=6
MAX_CANDIDATES=120

before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count=len(mesh.vertices);poly_count=len(mesh.polygons);edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside_support(co):
    ax=abs(co.x)
    return XMIN<=ax<=XMAX and YMIN<=co.y<=YMAX and ZMIN<=co.z<=ZMAX

support={i for i,co in enumerate(before) if inside_support(co)}
assert support, 'empty B1d-v2 support'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

boundary={i for i in support if any(j not in support for j in neighbors[i])}
interior=support-boundary
assert interior, 'empty B1d-v2 interior'

initial=[co.copy() for co in before]
candidates=[]
guide_metrics={}

for i in sorted(interior):
    p=initial[i]
    sign=1.0 if p.x>=0 else -1.0
    a=Vector((sign*SHOULDER_X,SHOULDER_Y,SHOULDER_Z))
    b=Vector((sign*LIMB_X,LIMB_Y,LIMB_Z))
    axis=b-a
    denom=axis.length_squared
    assert denom>0
    t=max(0.0,min(1.0,(p-a).dot(axis)/denom))
    center=a+axis*t
    radius=R0+(R1-R0)*t
    radial=p-center
    dist=radial.length
    q=dist/radius if radius>0 else 999.0
    guide_metrics[i]=(t,radius,dist,q,center)
    if q>THRESHOLD_SCALE:
        candidates.append(i)

assert MIN_CANDIDATES <= len(candidates) <= MAX_CANDIDATES, f'B1d-v2 candidate count {len(candidates)} outside [{MIN_CANDIDATES},{MAX_CANDIDATES}]'

for i in candidates:
    p=initial[i]
    t,radius,dist,q,center=guide_metrics[i]
    radial=p-center
    if dist<=1e-12:
        continue
    target=center+radial*(radius/dist)
    proposed=p+(target-p)*GAIN
    delta=proposed-p
    if delta.length>MAX_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_DISP
    # inward only relative to bridge centerline
    assert (proposed-center).length <= dist+1e-9
    mesh.vertices[i].co=proposed
mesh.update()

fixed=set(range(vert_count))-set(candidates)
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'fixed changed {i}'

# Topology exact.
assert len(mesh.vertices)==vert_count
assert len(mesh.polygons)==poly_count
assert len(mesh.edges)==edge_count
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Preserved separate meshes exact.
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
assert max_disp<=MAX_DISP+1e-7

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

bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(fixed):
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B1d-v2-tapered-shoulder-limb-bridge',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'outside-only mirrored tapered capsule bridge projection',
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'guide':{
   'shoulder_anchor_abs_x':SHOULDER_X,'shoulder_y':SHOULDER_Y,'shoulder_z':SHOULDER_Z,
   'limb_anchor_abs_x':LIMB_X,'limb_y':LIMB_Y,'limb_z':LIMB_Z,
   'radius_start':R0,'radius_end':R1
 },
 'parameters':{'threshold_scale':THRESHOLD_SCALE,'gain':GAIN,'max_displacement':MAX_DISP},
 'support_vertex_count':len(support),
 'boundary_vertex_count':len(boundary),
 'interior_vertex_count':len(interior),
 'candidate_vertex_count':len(candidates),
 'changed_vertex_count':changed,
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'q_min_candidate':min(guide_metrics[i][3] for i in candidates),
 'q_max_candidate':max(guide_metrics[i][3] for i in candidates),
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
with open(os.path.join(OUT,'S-vibe-b1d-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1d-v2.blend'),compress=True)
print('VIBE_B1D_V2_EDIT_COMPLETE',json.dumps(report))
