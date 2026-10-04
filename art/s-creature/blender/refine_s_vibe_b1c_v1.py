"""Experimental Vibe Gate B1c-v1: local shoulder-root resurface.
Source: S-vibe-b0-v025.blend.

Representation change:
- subdivide only source edges whose linked source faces are fully contained
  inside the proximal shoulder-root support box
- one local cut only
- then apply a small boundary-tapered same-side XYZ fairing to the refined patch

This is a local B1 sculpt-topology test. It is not object-wide remesh and final
deformation topology remains a later stage.
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
MARGIN_X=0.025
MARGIN_Y=0.035
MARGIN_Z=0.040
LAMBDA=0.18
PASSES=3
RESIDUAL_THRESHOLD=0.0015
MAX_LOCAL_DISP=0.004
MAX_EXTENT_DRIFT=0.003
SUPPORT_EPS=1e-5

src_vert_count=len(mesh.vertices)
src_poly_count=len(mesh.polygons)
src_edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside_support(co, eps=0.0):
    ax=abs(co.x)
    return (XMIN-eps) <= ax <= (XMAX+eps) and (YMIN-eps) <= co.y <= (YMAX+eps) and (ZMIN-eps) <= co.z <= (ZMAX+eps)

def smoothstep01(t):
    t=max(0.0,min(1.0,t))
    return t*t*(3.0-2.0*t)

def weight(co):
    if not inside_support(co):
        return 0.0
    ax=abs(co.x)
    dx=min(ax-XMIN,XMAX-ax)
    dy=min(co.y-YMIN,YMAX-co.y)
    dz=min(co.z-ZMIN,ZMAX-co.z)
    return smoothstep01(dx/MARGIN_X)*smoothstep01(dy/MARGIN_Y)*smoothstep01(dz/MARGIN_Z)

bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()

orig_verts=list(bm.verts)
orig_coords={v:v.co.copy() for v in orig_verts}
orig_outside=[v for v in orig_verts if not inside_support(v.co)]
orig_inside=[v for v in orig_verts if inside_support(v.co)]
assert orig_inside, 'No original B1c support vertices'

# Only subdivide edges whose linked faces are fully contained in support.
eligible=[]
affected_source_faces=set()
for e in list(bm.edges):
    if not (inside_support(e.verts[0].co) and inside_support(e.verts[1].co)):
        continue
    if not e.link_faces:
        continue
    # Support is bilateral and non-convex because it uses |X|. Never subdivide
    # an edge/face that bridges across the sagittal plane.
    if e.verts[0].co.x * e.verts[1].co.x <= 0:
        continue
    sign=1.0 if e.verts[0].co.x>0 else -1.0
    fully_local=True
    for f in e.link_faces:
        if not all(inside_support(v.co) for v in f.verts):
            fully_local=False
            break
        if not all(v.co.x*sign>0 for v in f.verts):
            fully_local=False
            break
    if fully_local:
        eligible.append(e)
        affected_source_faces.update(e.link_faces)

assert eligible, 'No fully-contained B1c edges eligible for subdivision'
affected_face_count=len(affected_source_faces)

result=bmesh.ops.subdivide_edges(
    bm,
    edges=eligible,
    cuts=1,
    use_grid_fill=True,
    smooth=0.0
)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()

# Determine new vertices by object identity relative to the pre-subdivision
# BMesh vertex set. geom_inner may include pre-existing vertices, so it is not
# a valid "new vertex only" list.
orig_set=set(orig_verts)
new_verts=[v for v in bm.verts if v not in orig_set]

assert new_verts, 'Subdivision created no new B1c vertices'

# All new vertices must remain local by construction.
assert all(inside_support(v.co, SUPPORT_EPS) for v in new_verts), 'Subdivision escaped support region beyond numeric tolerance'

local_verts=[v for v in bm.verts if inside_support(v.co, SUPPORT_EPS)]
initial_local={v:v.co.copy() for v in local_verts}

# Verify original outside-support coordinates are still exact after subdivision.
for v in orig_outside:
    assert tuple(v.co)==tuple(orig_coords[v]), 'Subdivision moved outside-support original vertex'

def same_side_local_neighbors(v):
    sign=1.0 if v.co.x>=0 else -1.0
    ns=[]
    for e in v.link_edges:
        ov=e.other_vert(v)
        if inside_support(ov.co, SUPPORT_EPS) and ov.co.x*sign>0:
            ns.append(ov)
    return ns

def clamp_from_initial(v,p):
    src=initial_local[v]
    d=p-src
    if d.length>MAX_LOCAL_DISP and d.length>0:
        p=src+d.normalized()*MAX_LOCAL_DISP
    # Do not cross sagittal plane.
    if src.x>0 and p.x<=0: p.x=1e-6
    if src.x<0 and p.x>=0: p.x=-1e-6
    return p

for _ in range(PASSES):
    current={v:v.co.copy() for v in local_verts}
    updates={}
    for v in local_verts:
        w=weight(current[v])
        if w<=0.0:
            continue
        ns=same_side_local_neighbors(v)
        if len(ns)<2:
            continue
        avg=sum((current[n] for n in ns),Vector())/len(ns)
        residual=avg-current[v]
        if residual.length<=RESIDUAL_THRESHOLD:
            continue
        p=current[v]+residual*(LAMBDA*w)
        updates[v]=clamp_from_initial(v,p)
    for v,p in updates.items():
        v.co=p

# Outside-support original body vertices must remain exact.
for v in orig_outside:
    assert tuple(v.co)==tuple(orig_coords[v]), 'Fairing moved outside-support original vertex'

# Local displacement budget relative to post-subdivision starting positions.
local_disp={v:(v.co-initial_local[v]).length for v in local_verts}
max_local_disp=max(local_disp.values()) if local_disp else 0.0
mean_local_disp=sum(local_disp.values())/len(local_disp) if local_disp else 0.0
changed_local=sum(1 for d in local_disp.values() if d>1e-10)
assert max_local_disp<=MAX_LOCAL_DISP+1e-9

# Local resurface must remain manifold.
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
assert len(nonmanifold)==0, f'Non-manifold edges after B1c resurface: {len(nonmanifold)}'

# Capture extents before writing.
src_ext={
 'x':(min(v.co.x for v in orig_verts),max(v.co.x for v in orig_verts)),
 'y':(min(v.co.y for v in orig_verts),max(v.co.y for v in orig_verts)),
 'z':(min(v.co.z for v in orig_verts),max(v.co.z for v in orig_verts)),
}
# NOTE: orig_verts coordinates inside support may have moved; compute source extents
# from immutable original coordinate snapshot instead.
src_ext={
 'x':(min(c.x for c in orig_coords.values()),max(c.x for c in orig_coords.values())),
 'y':(min(c.y for c in orig_coords.values()),max(c.y for c in orig_coords.values())),
 'z':(min(c.z for c in orig_coords.values()),max(c.z for c in orig_coords.values())),
}
dst_ext={
 'x':(min(v.co.x for v in bm.verts),max(v.co.x for v in bm.verts)),
 'y':(min(v.co.y for v in bm.verts),max(v.co.y for v in bm.verts)),
 'z':(min(v.co.z for v in bm.verts),max(v.co.z for v in bm.verts)),
}
extent_drift={}
for ax in ('x','y','z'):
    extent_drift[ax]=max(abs(dst_ext[ax][0]-src_ext[ax][0]),abs(dst_ext[ax][1]-src_ext[ax][1]))
    assert extent_drift[ax]<=MAX_EXTENT_DRIFT+1e-9, f'{ax} extent drift too large: {extent_drift[ax]}'

# Preserve all separate meshes exactly.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

bm.to_mesh(mesh)
bm.free()
mesh.update()

# Store an outside-support coordinate hash that remains stable even though local
# vertex indices/topology changed.
def outside_body_coords():
    coords=[tuple(v.co) for v in mesh.vertices if not inside_support(v.co, SUPPORT_EPS)]
    return sorted(coords)

def fixed_hash():
    h=hashlib.sha256()
    for co in outside_body_coords():
        h.update(repr(co).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B1c-v1-local-shoulder-root-resurface',
 'source':'S-vibe-b0-v025.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'one support-contained local subdivision + boundary-anchored XYZ fairing',
 'support':{
   'abs_x_min':XMIN,'abs_x_max':XMAX,
   'y_min':YMIN,'y_max':YMAX,
   'z_min':ZMIN,'z_max':ZMAX,
   'margin_x':MARGIN_X,'margin_y':MARGIN_Y,'margin_z':MARGIN_Z
 },
 'parameters':{
   'subdivision_cuts':1,
   'lambda':LAMBDA,'passes':PASSES,
   'residual_threshold':RESIDUAL_THRESHOLD,
   'max_local_displacement':MAX_LOCAL_DISP
 },
 'source_vertex_count':src_vert_count,
 'source_polygon_count':src_poly_count,
 'source_edge_count':src_edge_count,
 'result_vertex_count':len(mesh.vertices),
 'result_polygon_count':len(mesh.polygons),
 'result_edge_count':len(mesh.edges),
 'eligible_subdivided_edge_count':len(eligible),
 'affected_source_face_count':affected_face_count,
 'new_vertex_count':len(new_verts),
 'local_vertex_count_after_subdivision':len(local_verts),
 'changed_local_vertex_count':changed_local,
 'max_local_displacement':max_local_disp,
 'mean_local_displacement':mean_local_disp,
 'whole_body_extent_before':src_ext,
 'whole_body_extent_after':dst_ext,
 'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'outside_support_vertex_count':len(outside_body_coords()),
 'fixed_geometry_hash':fixed_hash(),
 'outside_support_original_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_change_scope':'support-contained shoulder-root patch only',
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b1c-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1c-v1.blend'),compress=True)
print('VIBE_B1C_V1_EDIT_COMPLETE',json.dumps(report))
