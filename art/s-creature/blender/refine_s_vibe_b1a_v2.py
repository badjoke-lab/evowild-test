"""Experimental Vibe Gate B1a-v2: local shoulder/chest surface cleanup.
Source: S-vibe-b0-v025.blend.
Editable: vertices of S_B0_continuous_body_v025 whose ORIGINAL coordinates lie
inside Y[-0.12, 0.22], Z[0.74, 1.14], with boundary-tapered weights.
Method: two Taubin-style lambda/mu relax cycles.
All body vertices outside the region, crest, toes, topology and vertex count are hard-locked.
"""
import bpy, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

YMIN,YMAX=-0.12,0.22
ZMIN,ZMAX=0.74,1.14
MARGIN_Y=0.060
MARGIN_Z=0.070
LAMBDA=0.32
MU=-0.33
CYCLES=4

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
    y,z=co.y,co.z
    if not (YMIN <= y <= YMAX and ZMIN <= z <= ZMAX):
        return 0.0
    dy=min(y-YMIN,YMAX-y)
    dz=min(z-ZMIN,ZMAX-z)
    wy=smoothstep01(dy/MARGIN_Y)
    wz=smoothstep01(dz/MARGIN_Z)
    return wy*wz

weights=[boundary_weight(co) for co in body_before]
editable={i for i,w in enumerate(weights) if w>0.0}
fixed=set(range(len(mesh.vertices)))-editable
assert editable, 'No B1a editable vertices selected'

# Mesh adjacency from the unchanged topology.
neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b); neighbors[b].add(a)
assert all(neighbors[i] for i in editable)

def relax_pass(alpha):
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in editable:
        ns=neighbors[i]
        avg=sum((current[j] for j in ns),Vector())/len(ns)
        lap=avg-current[i]
        updates[i]=current[i] + lap*(alpha*weights[i])
    for i,p in updates.items():
        mesh.vertices[i].co=p
    mesh.update()

for _ in range(CYCLES):
    relax_pass(LAMBDA)
    relax_pass(MU)

# Hard fixed body vertices exact.
for i in fixed:
    assert tuple(mesh.vertices[i].co)==tuple(body_before[i]), f'fixed body changed {i}'

# Topology and counts exact.
assert len(mesh.vertices)==vert_count_before
assert len(mesh.polygons)==poly_count_before
assert len(mesh.edges)==edge_count_before
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
assert [tuple(e.vertices) for e in mesh.edges]==edge_before

# Crest/toes exact.
for name,coords in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]

# Displacement stats.
deltas=[(mesh.vertices[i].co-body_before[i]).length for i in editable]
changed=[d for d in deltas if d>1e-10]
max_disp=max(deltas) if deltas else 0.0
mean_disp=(sum(deltas)/len(deltas)) if deltas else 0.0
assert max_disp <= 0.010, f'B1a-v2 displacement too large: {max_disp}'

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
 'gate':'B1a-v2-local-shoulder-chest-relax',
 'source':'S-vibe-b0-v025.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'boundary-tapered Taubin-style local relax',
 'region':{'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX,'margin_y':MARGIN_Y,'margin_z':MARGIN_Z},
 'parameters':{'lambda':LAMBDA,'mu':MU,'cycles':CYCLES},
 'editable_vertex_count':len(editable),
 'fixed_body_vertex_count':len(fixed),
 'fixed_vertex_indices':sorted(fixed),
 'editable_vertex_indices':sorted(editable),
 'changed_vertex_count':len(changed),
 'max_displacement':max_disp,
 'mean_displacement':mean_disp,
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
with open(os.path.join(OUT,'S-vibe-b1a-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1a-v2.blend'),compress=True)
print('VIBE_B1A_V1_EDIT_COMPLETE',json.dumps(report))
