"""Experimental Vibe Gate B1c-v2: high-curvature ridge suppression on the
already-refined B1c-v1 shoulder-root patch.

Source: S-vibe-b1c-v1.blend.
No topology change is allowed in this pass.

Single hypothesis:
The remaining visible triangular cap is carried by a small set of high residual
vertices inside the refined patch. Move only those vertices toward the local
same-side neighbor mean while fixing the support boundary and everything else.
"""
import bpy, bmesh, os, json, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

XMIN,XMAX=0.070,0.180
YMIN,YMAX=-0.090,0.105
ZMIN,ZMAX=0.900,1.105
RESIDUAL_THRESHOLD=0.0025
LAMBDA=0.35
PASSES=2
MAX_DISP=0.0035
MAX_EXTENT_DRIFT=0.002
EPS=1e-5

before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count=len(mesh.vertices); poly_count=len(mesh.polygons); edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside(co, eps=0.0):
    ax=abs(co.x)
    return (XMIN-eps)<=ax<=(XMAX+eps) and (YMIN-eps)<=co.y<=(YMAX+eps) and (ZMIN-eps)<=co.z<=(ZMAX+eps)

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

support={i for i,co in enumerate(before) if inside(co,EPS)}
assert support, 'empty B1c-v2 support'

# Boundary = support vertex touching anything outside support.
boundary=set()
for i in support:
    if any(j not in support for j in neighbors[i]):
        boundary.add(i)
interior=support-boundary
assert interior, 'empty B1c-v2 interior'

# Same-side neighbors only, still inside support.
def local_same_side_neighbors(i,current):
    sx=1.0 if before[i].x>=0 else -1.0
    return [j for j in neighbors[i] if j in support and current[j].x*sx>0]

initial=[co.copy() for co in before]

def clamp_from_initial(i,p):
    src=initial[i]
    d=p-src
    if d.length>MAX_DISP and d.length>0:
        p=src+d.normalized()*MAX_DISP
    # never cross sagittal plane
    if src.x>0 and p.x<=0: p.x=1e-6
    if src.x<0 and p.x>=0: p.x=-1e-6
    return p

moved_candidates=set()
for _ in range(PASSES):
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(interior):
        ns=local_same_side_neighbors(i,current)
        if len(ns)<3:
            continue
        avg=sum((current[j] for j in ns),Vector())/len(ns)
        residual=avg-current[i]
        if residual.length<=RESIDUAL_THRESHOLD:
            continue
        p=current[i]+residual*LAMBDA
        p=clamp_from_initial(i,p)
        updates[i]=p
        moved_candidates.add(i)
    for i,p in updates.items():
        mesh.vertices[i].co=p
    mesh.update()

# Final deterministic clamp relative to B1c-v1 source, preserving the
# original displacement budget even after multiple passes and float roundoff.
for i in sorted(interior):
    d=mesh.vertices[i].co-initial[i]
    if d.length>MAX_DISP and d.length>0:
        mesh.vertices[i].co=initial[i]+d.normalized()*MAX_DISP
mesh.update()

# Hard fixed: all outside support + support boundary exact.
fixed=set(range(vert_count))-interior
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'fixed changed {i}'

# Topology exact.
assert len(mesh.vertices)==vert_count
assert len(mesh.polygons)==poly_count
assert len(mesh.edges)==edge_count
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Preserved meshes exact.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

disp={i:(mesh.vertices[i].co-before[i]).length for i in interior}
vals=list(disp.values())
max_disp=max(vals) if vals else 0.0
mean_disp=sum(vals)/len(vals) if vals else 0.0
changed=sum(1 for d in vals if d>1e-10)
assert max_disp<=MAX_DISP+1e-7, f'max additional displacement {max_disp} > {MAX_DISP}'

src_ext={
 'x':(min(v.x for v in before),max(v.x for v in before)),
 'y':(min(v.y for v in before),max(v.y for v in before)),
 'z':(min(v.z for v in before),max(v.z for v in before)),
}
dst=[v.co for v in mesh.vertices]
dst_ext={
 'x':(min(v.x for v in dst),max(v.x for v in dst)),
 'y':(min(v.y for v in dst),max(v.y for v in dst)),
 'z':(min(v.z for v in dst),max(v.z for v in dst)),
}
extent_drift={}
for ax in ('x','y','z'):
    extent_drift[ax]=max(abs(dst_ext[ax][0]-src_ext[ax][0]),abs(dst_ext[ax][1]-src_ext[ax][1]))
    assert extent_drift[ax]<=MAX_EXTENT_DRIFT+1e-9, f'{ax} extent drift too large {extent_drift[ax]}'

bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0, f'non-manifold edges: {len(nonmanifold)}'

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
 'gate':'B1c-v2-high-curvature-root-ridge-suppression',
 'source':'S-vibe-b1c-v1.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'support-boundary-fixed residual-gated XYZ fairing on refined topology',
 'support':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'parameters':{'lambda':LAMBDA,'passes':PASSES,'residual_threshold':RESIDUAL_THRESHOLD,'max_additional_displacement':MAX_DISP},
 'support_vertex_count':len(support),
 'boundary_vertex_count':len(boundary),
 'interior_vertex_count':len(interior),
 'candidate_vertex_count':len(moved_candidates),
 'changed_vertex_count':changed,
 'max_additional_displacement':max_disp,
 'mean_additional_displacement':mean_disp,
 'fixed_vertex_indices':sorted(fixed),
 'interior_vertex_indices':sorted(interior),
 'whole_body_extent_before':src_ext,
 'whole_body_extent_after':dst_ext,
 'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'fixed_geometry_hash':fixed_hash(),
 'outside_and_boundary_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_unchanged_from_b1c_v1':True,
 'vertex_count':len(mesh.vertices),
 'polygon_count':len(mesh.polygons),
 'edge_count':len(mesh.edges),
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b1c-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1c-v2.blend'),compress=True)
print('VIBE_B1C_V2_EDIT_COMPLETE',json.dumps(report))
