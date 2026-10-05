"""Experimental Vibe Gate B1c-v3: upper shoulder-root cap Z-only shaping.

Source: S-vibe-b1c-v2.blend.

Single hypothesis:
The remaining triangular artifact is concentrated in a raised upper cap.
Keep all X/Y coordinates exact and reduce only positive Z residuals inside a
small cap mask. Topology remains exactly B1c-v2.
"""
import bpy, bmesh, os, json, hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

XMIN,XMAX=0.085,0.170
YMIN,YMAX=-0.075,0.055
ZMIN,ZMAX=1.015,1.100
RESIDUAL_THRESHOLD=0.0015
LAMBDA=0.65
PASSES=2
MAX_Z_DROP=0.004

before=[v.co.copy() for v in mesh.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]
edge_before=[tuple(e.vertices) for e in mesh.edges]
vert_count=len(mesh.vertices);poly_count=len(mesh.polygons);edge_count=len(mesh.edges)

preserved=[o for o in cage.objects if o.type=='MESH' and o!=body]
preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def inside(co):
    ax=abs(co.x)
    return XMIN<=ax<=XMAX and YMIN<=co.y<=YMAX and ZMIN<=co.z<=ZMAX

mask={i for i,co in enumerate(before) if inside(co)}
assert mask, 'empty B1c-v3 cap mask'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b);neighbors[b].add(a)

# Keep mask boundary fixed; only true interior cap vertices may move.
boundary=set()
for i in mask:
    if any(j not in mask for j in neighbors[i]):
        boundary.add(i)
interior=mask-boundary
assert interior, 'empty B1c-v3 cap interior'

def same_side_mask_neighbors(i,current):
    sx=1.0 if before[i].x>=0 else -1.0
    return [j for j in neighbors[i] if j in mask and current[j].x*sx>0]

initial=[co.copy() for co in before]
moved_candidates=set()

for _ in range(PASSES):
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(interior):
        ns=same_side_mask_neighbors(i,current)
        if len(ns)<3:
            continue
        avg_z=sum(current[j].z for j in ns)/len(ns)
        residual_up=current[i].z-avg_z
        if residual_up<=RESIDUAL_THRESHOLD:
            continue
        proposed=current[i].z-LAMBDA*residual_up
        floor=initial[i].z-MAX_Z_DROP
        nz=max(floor,proposed)
        updates[i]=nz
        moved_candidates.add(i)
    for i,nz in updates.items():
        src=initial[i]
        mesh.vertices[i].co=(src.x,src.y,nz)
    mesh.update()

# Final exact clamp and XY lock.
for i in interior:
    src=initial[i]
    z=max(src.z-MAX_Z_DROP,mesh.vertices[i].co.z)
    mesh.vertices[i].co=(src.x,src.y,z)
mesh.update()

fixed=set(range(vert_count))-interior
for i in range(vert_count):
    src=before[i];cur=mesh.vertices[i].co
    assert cur.x==src.x, f'X changed {i}'
    assert cur.y==src.y, f'Y changed {i}'
    if i in fixed:
        assert cur.z==src.z, f'fixed Z changed {i}'

# Topology exact.
assert len(mesh.vertices)==vert_count
assert len(mesh.polygons)==poly_count
assert len(mesh.edges)==edge_count
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Separate meshes exact.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

drops={i:before[i].z-mesh.vertices[i].co.z for i in interior}
vals=list(drops.values())
max_drop=max(vals) if vals else 0.0
mean_drop=sum(vals)/len(vals) if vals else 0.0
changed=sum(1 for d in vals if d>1e-10)
assert max_drop<=MAX_Z_DROP+1e-7
assert all(d>=-1e-10 for d in vals)

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
assert all(v<=1e-9 for v in extent_drift.values()), f'extent drift {extent_drift}'

bm=bmesh.new();bm.from_mesh(mesh)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(fixed):
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for i in sorted(interior):
        h.update(b'xy');h.update(str(i).encode());h.update(repr((mesh.vertices[i].co.x,mesh.vertices[i].co.y)).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B1c-v3-upper-cap-z-only-shaping',
 'source':'S-vibe-b1c-v2.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'mask-interior positive-Z-residual reduction; Z down only',
 'mask':{'abs_x_min':XMIN,'abs_x_max':XMAX,'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX},
 'parameters':{'lambda':LAMBDA,'passes':PASSES,'residual_threshold':RESIDUAL_THRESHOLD,'max_extra_z_drop':MAX_Z_DROP},
 'mask_vertex_count':len(mask),
 'boundary_vertex_count':len(boundary),
 'interior_vertex_count':len(interior),
 'candidate_vertex_count':len(moved_candidates),
 'changed_vertex_count':changed,
 'max_extra_z_drop':max_drop,
 'mean_extra_z_drop':mean_drop,
 'all_body_xy_unchanged':True,
 'fixed_vertex_indices':sorted(fixed),
 'interior_vertex_indices':sorted(interior),
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
with open(os.path.join(OUT,'S-vibe-b1c-v3-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1c-v3.blend'),compress=True)
print('VIBE_B1C_V3_EDIT_COMPLETE',json.dumps(report))
