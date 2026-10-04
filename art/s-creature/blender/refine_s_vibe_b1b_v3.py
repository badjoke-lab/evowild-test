"""Experimental Vibe Gate B1b-v3: Y/Z-only shoulder-root connection fairing.
Source: S-vibe-b0-v025.blend.

Single hypothesis:
A small residual-gated Y/Z-only fairing at the proximal forelimb/shoulder root
can reduce the upper-edge step and triangular root connection while preserving
all lateral X coordinates exactly.

Editable source-coordinate mask:
- |X| [0.070, 0.180]
- Y [-0.10, 0.10]
- Z [0.90, 1.12]

Method:
- same-side residual-gated Laplacian fairing in the Y/Z plane only
- positive pass lambda 0.24
- 3 passes
- residual threshold 0.0015
- cumulative per-vertex Y/Z displacement clamp 0.006

Hard fixed:
- X of every body vertex
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

XMIN,XMAX=0.070,0.180
YMIN,YMAX=-0.10,0.10
ZMIN,ZMAX=0.90,1.12
MARGIN_X=0.020
MARGIN_Y=0.030
MARGIN_Z=0.035
LAMBDA=0.24
PASSES=3
RESIDUAL_THRESHOLD=0.0015
MAX_DYZ=0.006
MAX_Y_EXTENT_DRIFT=0.004
MAX_Z_EXTENT_DRIFT=0.004

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
assert editable, 'No B1b-v3 editable vertices selected'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

def same_side_neighbors(i,current):
    srcx=body_before[i].x
    sign=1.0 if srcx>=0 else -1.0
    ns=[j for j in neighbors[i] if current[j].x*sign>0]
    return ns if ns else list(neighbors[i])

def clamp_to_source(i,y,z):
    src=body_before[i]
    dy=y-src.y
    dz=z-src.z
    d=math.sqrt(dy*dy+dz*dz)
    if d>MAX_DYZ and d>0:
        s=MAX_DYZ/d
        y=src.y+dy*s
        z=src.z+dz*s
    return y,z

def fair_yz_pass():
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(editable):
        ns=same_side_neighbors(i,current)
        assert ns
        avg_y=sum(current[j].y for j in ns)/len(ns)
        avg_z=sum(current[j].z for j in ns)/len(ns)
        ry=avg_y-current[i].y
        rz=avg_z-current[i].z
        residual=math.sqrt(ry*ry+rz*rz)
        if residual <= RESIDUAL_THRESHOLD:
            continue
        gain=LAMBDA*weights[i]
        ny=current[i].y+ry*gain
        nz=current[i].z+rz*gain
        updates[i]=clamp_to_source(i,ny,nz)
    for i,(y,z) in updates.items():
        srcx=body_before[i].x
        mesh.vertices[i].co=(srcx,y,z)
    mesh.update()

for _ in range(PASSES):
    fair_yz_pass()

# Hard-lock body X everywhere and full coords outside the mask.
for i,v in enumerate(mesh.vertices):
    src=body_before[i]
    assert v.co.x==src.x, f'X changed {i}'
    if i in fixed:
        assert tuple(v.co)==tuple(src), f'fixed vertex changed {i}'

# Topology/count exact.
assert len(mesh.vertices)==vert_count_before
assert len(mesh.polygons)==poly_count_before
assert len(mesh.edges)==edge_count_before
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Preserved meshes exact.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

# Measure actual Y/Z displacement.
disp={}
for i in editable:
    src=body_before[i]
    cur=mesh.vertices[i].co
    dy=cur.y-src.y
    dz=cur.z-src.z
    disp[i]=math.sqrt(dy*dy+dz*dz)
vals=list(disp.values())
max_d=max(vals) if vals else 0.0
mean_d=sum(vals)/len(vals) if vals else 0.0
changed=sum(1 for d in vals if d>1e-10)
assert max_d <= MAX_DYZ+1e-9

y_before=(min(v.y for v in body_before),max(v.y for v in body_before))
z_before=(min(v.z for v in body_before),max(v.z for v in body_before))
y_after=(min(v.co.y for v in mesh.vertices),max(v.co.y for v in mesh.vertices))
z_after=(min(v.co.z for v in mesh.vertices),max(v.co.z for v in mesh.vertices))
y_extent_drift=max(abs(y_after[0]-y_before[0]),abs(y_after[1]-y_before[1]))
z_extent_drift=max(abs(z_after[0]-z_before[0]),abs(z_after[1]-z_before[1]))
assert y_extent_drift <= MAX_Y_EXTENT_DRIFT+1e-9, f'Y extent drift too large: {y_extent_drift}'
assert z_extent_drift <= MAX_Z_EXTENT_DRIFT+1e-9, f'Z extent drift too large: {z_extent_drift}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(fixed):
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    # X is hard-fixed for every editable vertex.
    for i in sorted(editable):
        h.update(b'x');h.update(str(i).encode());h.update(repr(mesh.vertices[i].co.x).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B1b-v3-yz-shoulder-root-connection-fairing',
 'source':'S-vibe-b0-v025.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'residual-gated same-side Y/Z-only local fairing',
 'region':{
   'abs_x_min':XMIN,'abs_x_max':XMAX,
   'y_min':YMIN,'y_max':YMAX,
   'z_min':ZMIN,'z_max':ZMAX,
   'margin_x':MARGIN_X,'margin_y':MARGIN_Y,'margin_z':MARGIN_Z
 },
 'parameters':{
   'lambda':LAMBDA,'passes':PASSES,
   'residual_threshold':RESIDUAL_THRESHOLD,
   'max_yz_displacement':MAX_DYZ
 },
 'editable_vertex_count':len(editable),
 'fixed_body_vertex_count':len(fixed),
 'editable_vertex_indices':sorted(editable),
 'fixed_vertex_indices':sorted(fixed),
 'changed_vertex_count':changed,
 'max_yz_displacement':max_d,
 'mean_yz_displacement':mean_d,
 'all_body_x_unchanged':True,
 'whole_body_y_before':y_before,
 'whole_body_y_after':y_after,
 'whole_body_z_before':z_before,
 'whole_body_z_after':z_after,
 'whole_body_y_extent_drift':y_extent_drift,
 'whole_body_z_extent_drift':z_extent_drift,
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
with open(os.path.join(OUT,'S-vibe-b1b-v3-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1b-v3.blend'),compress=True)
print('VIBE_B1B_V3_EDIT_COMPLETE',json.dumps(report))
