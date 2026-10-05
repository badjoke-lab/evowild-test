"""Experimental Vibe Gate B1e-v1: expanded-support seam blend.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
The persistent triangular shoulder-root artifact is tied to the old B1c support
boundary, which every later test kept fixed. Allow only that old boundary plus
one mesh-neighbor ring to move, while anchoring a new larger outer support.

No topology change.
"""
import bpy, bmesh, os, json, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

# Old B1c support.
OXMIN,OXMAX=0.070,0.180
OYMIN,OYMAX=-0.090,0.105
OZMIN,OZMAX=0.900,1.105

# New expanded anchored support.
NXMIN,NXMAX=0.055,0.205
NYMIN,NYMAX=-0.130,0.145
NZMIN,NZMAX=0.860,1.145

LAMBDA=0.25
PASSES=2
RESIDUAL_THRESHOLD=0.0015
MAX_DISP=0.0035
MAX_EXTENT_DRIFT=0.002
MIN_EDITABLE=40
MAX_EDITABLE=260

before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count=len(mesh.vertices);poly_count=len(mesh.polygons);edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside_old(co):
    ax=abs(co.x)
    return OXMIN<=ax<=OXMAX and OYMIN<=co.y<=OYMAX and OZMIN<=co.z<=OZMAX

def inside_new(co):
    ax=abs(co.x)
    return NXMIN<=ax<=NXMAX and NYMIN<=co.y<=NYMAX and NZMIN<=co.z<=NZMAX

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

old_support={i for i,co in enumerate(before) if inside_old(co)}
new_support={i for i,co in enumerate(before) if inside_new(co)}
assert old_support and new_support

old_boundary={i for i in old_support if any(j not in old_support for j in neighbors[i])}
new_boundary={i for i in new_support if any(j not in new_support for j in neighbors[i])}

ring=set()
for i in old_boundary:
    for j in neighbors[i]:
        if j in new_support:
            ring.add(j)

editable=(old_boundary|ring)-new_boundary
assert MIN_EDITABLE<=len(editable)<=MAX_EDITABLE, f'B1e-v1 editable count {len(editable)} outside [{MIN_EDITABLE},{MAX_EDITABLE}]'

initial=[co.copy() for co in before]

def same_side_neighbors(i,current):
    sign=1.0 if initial[i].x>=0 else -1.0
    return [j for j in neighbors[i] if current[j].x*sign>0]

def clamp_from_initial(i,p):
    d=p-initial[i]
    if d.length>MAX_DISP and d.length>0:
        p=initial[i]+d.normalized()*MAX_DISP
    if initial[i].x>0 and p.x<=0: p.x=1e-6
    if initial[i].x<0 and p.x>=0: p.x=-1e-6
    return p

candidate_hits=set()
for _ in range(PASSES):
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(editable):
        ns=same_side_neighbors(i,current)
        if len(ns)<3:
            continue
        avg=sum((current[j] for j in ns),Vector())/len(ns)
        residual=avg-current[i]
        if residual.length<=RESIDUAL_THRESHOLD:
            continue
        p=current[i]+residual*LAMBDA
        p=clamp_from_initial(i,p)
        updates[i]=p
        candidate_hits.add(i)
    for i,p in updates.items():
        mesh.vertices[i].co=p
    mesh.update()

# Final deterministic clamp.
for i in sorted(editable):
    d=mesh.vertices[i].co-initial[i]
    if d.length>MAX_DISP and d.length>0:
        mesh.vertices[i].co=initial[i]+d.normalized()*MAX_DISP
mesh.update()

fixed=set(range(vert_count))-editable
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'fixed changed {i}'

# New outer boundary is explicitly fixed.
for i in new_boundary:
    assert tuple(mesh.vertices[i].co)==tuple(before[i]), f'new boundary changed {i}'

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

disp={i:(mesh.vertices[i].co-before[i]).length for i in editable}
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
 'gate':'B1e-v1-expanded-support-seam-blend',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'old-support-boundary plus one-ring same-side XYZ seam blend inside expanded anchored support',
 'old_support':{'abs_x_min':OXMIN,'abs_x_max':OXMAX,'y_min':OYMIN,'y_max':OYMAX,'z_min':OZMIN,'z_max':OZMAX},
 'expanded_support':{'abs_x_min':NXMIN,'abs_x_max':NXMAX,'y_min':NYMIN,'y_max':NYMAX,'z_min':NZMIN,'z_max':NZMAX},
 'parameters':{'lambda':LAMBDA,'passes':PASSES,'residual_threshold':RESIDUAL_THRESHOLD,'max_displacement':MAX_DISP},
 'old_support_vertex_count':len(old_support),
 'old_boundary_vertex_count':len(old_boundary),
 'expanded_support_vertex_count':len(new_support),
 'expanded_boundary_vertex_count':len(new_boundary),
 'editable_vertex_count':len(editable),
 'candidate_hit_count':len(candidate_hits),
 'changed_vertex_count':changed,
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
 'fixed_vertex_indices':sorted(fixed),
 'editable_vertex_indices':sorted(editable),
 'whole_body_extent_before':src_ext,
 'whole_body_extent_after':dst_ext,
 'whole_body_extent_drift':extent_drift,
 'non_manifold_edge_count':0,
 'fixed_geometry_hash':fixed_hash(),
 'outside_and_expanded_boundary_geometry_unchanged':True,
 'preserved_geometry_unchanged':True,
 'topology_unchanged_from_b1c_v2':True,
 'vertex_count':len(mesh.vertices),
 'polygon_count':len(mesh.polygons),
 'edge_count':len(mesh.edges),
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b1e-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1e-v1.blend'),compress=True)
print('VIBE_B1E_V1_EDIT_COMPLETE',json.dumps(report))
