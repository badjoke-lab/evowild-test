"""Experimental Vibe Gate B1b-v4: compact 3D shoulder-root connection fairing.
Source: S-vibe-b0-v025.blend.

Single hypothesis:
The remaining root defect is a coupled 3D connection-shape problem. A compact,
residual-gated XYZ fairing can soften both the SIDE top step and FRONT34
triangular root without touching wider shoulder/chest morphology.

Editable source-coordinate mask:
- |X| [0.080, 0.165]
- Y [-0.075, 0.085]
- Z [0.925, 1.085]

Method:
- same-side residual-gated XYZ Laplacian fairing
- positive pass lambda 0.20
- 3 passes
- residual threshold 0.0020
- cumulative per-vertex 3D displacement clamp 0.006

Hard fixed:
- all non-mask body vertices
- crest, toes, topology and vertex count
"""
import bpy, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

XMIN,XMAX=0.080,0.165
YMIN,YMAX=-0.075,0.085
ZMIN,ZMAX=0.925,1.085
MARGIN_X=0.018
MARGIN_Y=0.025
MARGIN_Z=0.030
LAMBDA=0.20
PASSES=3
RESIDUAL_THRESHOLD=0.0020
MAX_D=0.006
MAX_EXTENT_DRIFT=0.004

body_before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count_before=len(mesh.vertices)
poly_count_before=len(mesh.polygons)
edge_count_before=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def smoothstep01(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3.0-2.0*t)

def boundary_weight(co):
    ax=abs(co.x); y=co.y; z=co.z
    if not (XMIN <= ax <= XMAX and YMIN <= y <= YMAX and ZMIN <= z <= ZMAX):
        return 0.0
    dx=min(ax-XMIN,XMAX-ax)
    dy=min(y-YMIN,YMAX-y)
    dz=min(z-ZMIN,ZMAX-z)
    return smoothstep01(dx/MARGIN_X)*smoothstep01(dy/MARGIN_Y)*smoothstep01(dz/MARGIN_Z)

weights=[boundary_weight(co) for co in body_before]
editable={i for i,w in enumerate(weights) if w>0.0}
fixed=set(range(len(mesh.vertices)))-editable
assert editable, 'No B1b-v4 editable vertices selected'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

def same_side_neighbors(i,current):
    srcx=body_before[i].x
    sign=1.0 if srcx>=0 else -1.0
    ns=[j for j in neighbors[i] if current[j].x*sign>0]
    return ns if ns else list(neighbors[i])

def clamp_to_source(i,p):
    src=body_before[i]
    d=p-src
    if d.length>MAX_D and d.length>0:
        p=src+d.normalized()*MAX_D
    # preserve side sign
    if src.x>0 and p.x<=0: p.x=1e-6
    if src.x<0 and p.x>=0: p.x=-1e-6
    return p

def fair_xyz_pass():
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(editable):
        ns=same_side_neighbors(i,current)
        assert ns
        avg=sum((current[j] for j in ns),Vector())/len(ns)
        residual=avg-current[i]
        if residual.length <= RESIDUAL_THRESHOLD:
            continue
        p=current[i]+residual*(LAMBDA*weights[i])
        updates[i]=clamp_to_source(i,p)
    for i,p in updates.items():
        mesh.vertices[i].co=p
    mesh.update()

for _ in range(PASSES):
    fair_xyz_pass()

for i,v in enumerate(mesh.vertices):
    if i in fixed:
        assert tuple(v.co)==tuple(body_before[i]), f'fixed vertex changed {i}'

assert len(mesh.vertices)==vert_count_before
assert len(mesh.polygons)==poly_count_before
assert len(mesh.edges)==edge_count_before
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

disp={}
for i in editable:
    d=(mesh.vertices[i].co-body_before[i]).length
    disp[i]=d
vals=list(disp.values())
max_d=max(vals) if vals else 0.0
mean_d=sum(vals)/len(vals) if vals else 0.0
changed=sum(1 for d in vals if d>1e-10)
assert max_d <= MAX_D+1e-9

before_ext={
 'x':(min(v.x for v in body_before),max(v.x for v in body_before)),
 'y':(min(v.y for v in body_before),max(v.y for v in body_before)),
 'z':(min(v.z for v in body_before),max(v.z for v in body_before)),
}
after_ext={
 'x':(min(v.co.x for v in mesh.vertices),max(v.co.x for v in mesh.vertices)),
 'y':(min(v.co.y for v in mesh.vertices),max(v.co.y for v in mesh.vertices)),
 'z':(min(v.co.z for v in mesh.vertices),max(v.co.z for v in mesh.vertices)),
}
extent_drift={}
for ax in ('x','y','z'):
    extent_drift[ax]=max(abs(after_ext[ax][0]-before_ext[ax][0]),abs(after_ext[ax][1]-before_ext[ax][1]))
    assert extent_drift[ax] <= MAX_EXTENT_DRIFT+1e-9, f'{ax} extent drift too large: {extent_drift[ax]}'

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
 'gate':'B1b-v4-compact-xyz-shoulder-root-fairing',
 'source':'S-vibe-b0-v025.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'compact residual-gated same-side XYZ fairing',
 'region':{
   'abs_x_min':XMIN,'abs_x_max':XMAX,
   'y_min':YMIN,'y_max':YMAX,
   'z_min':ZMIN,'z_max':ZMAX,
   'margin_x':MARGIN_X,'margin_y':MARGIN_Y,'margin_z':MARGIN_Z
 },
 'parameters':{
   'lambda':LAMBDA,'passes':PASSES,
   'residual_threshold':RESIDUAL_THRESHOLD,
   'max_displacement':MAX_D
 },
 'editable_vertex_count':len(editable),
 'fixed_body_vertex_count':len(fixed),
 'editable_vertex_indices':sorted(editable),
 'fixed_vertex_indices':sorted(fixed),
 'changed_vertex_count':changed,
 'max_displacement':max_d,
 'mean_displacement':mean_d,
 'whole_body_extent_before':before_ext,
 'whole_body_extent_after':after_ext,
 'whole_body_extent_drift':extent_drift,
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'preserved_meshes':sorted(preserved_before),
 'preserved_geometry_unchanged':True,
 'topology_unchanged':True,
 'vertex_count':len(mesh.vertices),
 'polygon_count':len(mesh.polygons),
 'edge_count':len(mesh.edges),
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b1b-v4-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1b-v4.blend'),compress=True)
print('VIBE_B1B_V4_EDIT_COMPLETE',json.dumps(report))
