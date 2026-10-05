"""Experimental Vibe Gate B1d-v1: anatomical shoulder-guide projection.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
The remaining shoulder-root triangle is an explicit shape-target defect.
Within the already-refined local patch, pull only vertices that lie outside a
mirrored rounded shoulder ellipsoid toward that guide. No topology change.
"""
import bpy, bmesh, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

XMIN,XMAX=0.070,0.180
YMIN,YMAX=-0.090,0.105
ZMIN,ZMAX=0.900,1.105
CENTER_X=0.115
CENTER_Y=-0.020
CENTER_Z=0.985
RX=0.085
RY=0.105
RZ=0.095
Q_THRESHOLD=1.04
GAIN=0.55
MAX_DISP=0.005
MAX_EXTENT_DRIFT=0.002

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
assert support, 'empty B1d support'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

boundary={i for i in support if any(j not in support for j in neighbors[i])}
interior=support-boundary
assert interior, 'empty B1d interior'

initial=[co.copy() for co in before]
candidates=[]
q_values={}
for i in sorted(interior):
    p=initial[i]
    sign=1.0 if p.x>=0 else -1.0
    cx=sign*CENTER_X
    dx=(p.x-cx)/RX
    dy=(p.y-CENTER_Y)/RY
    dz=(p.z-CENTER_Z)/RZ
    q=dx*dx+dy*dy+dz*dz
    q_values[i]=q
    if q>Q_THRESHOLD:
        candidates.append(i)

assert candidates, 'no B1d guide-outside candidates'

for i in candidates:
    p=initial[i]
    sign=1.0 if p.x>=0 else -1.0
    center=Vector((sign*CENTER_X,CENTER_Y,CENTER_Z))
    d=p-center
    q=q_values[i]
    scale=1.0/math.sqrt(q)
    target=center+d*scale
    proposed=p+(target-p)*GAIN
    delta=proposed-p
    if delta.length>MAX_DISP and delta.length>0:
        proposed=p+delta.normalized()*MAX_DISP
    # ensure the operation never expands away from the guide center
    old_r=(p-center).length
    new_r=(proposed-center).length
    assert new_r<=old_r+1e-9
    mesh.vertices[i].co=proposed
mesh.update()

fixed=set(range(vert_count))-set(candidates)
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'fixed changed {i}'

# Exact topology preservation.
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
 'gate':'B1d-v1-anatomical-shoulder-guide-projection',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'outside-only mirrored ellipsoid projection on refined shoulder-root patch',
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'guide':{'center_abs_x':CENTER_X,'center_y':CENTER_Y,'center_z':CENTER_Z,'radius_x':RX,'radius_y':RY,'radius_z':RZ},
 'parameters':{'q_threshold':Q_THRESHOLD,'gain':GAIN,'max_displacement':MAX_DISP},
 'support_vertex_count':len(support),
 'boundary_vertex_count':len(boundary),
 'interior_vertex_count':len(interior),
 'candidate_vertex_count':len(candidates),
 'changed_vertex_count':changed,
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'q_min_candidate':min(q_values[i] for i in candidates),
 'q_max_candidate':max(q_values[i] for i in candidates),
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
with open(os.path.join(OUT,'S-vibe-b1d-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1d-v1.blend'),compress=True)
print('VIBE_B1D_V1_EDIT_COMPLETE',json.dumps(report))
