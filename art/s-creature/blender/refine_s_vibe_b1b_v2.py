"""Experimental Vibe Gate B1b-v2: X-only local shoulder/chest plane fairing.
Source: S-vibe-b0-v025.blend.

Goal:
- reduce lateral shoulder-root/chest-side protrusion visible in FRONT34
- preserve SIDE profile exactly by keeping Y/Z coordinates unchanged

Editable mask (source coordinates):
- Y [-0.12, 0.18]
- Z [0.80, 1.12]
- |X| >= 0.055

Method:
- boundary-tapered inward-only positive fairing on X only
- same-side neighbors only
- cumulative inward |delta X| capped at 0.012
- 4 positive passes, lambda 0.32; no negative pass; no outward moves

Hard fixed:
- all non-mask body vertices
- Y/Z of every body vertex
- crest and toes
- topology and vertex count
"""
import bpy, os, json, hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B0_continuous_body_v025']
mesh=body.data

YMIN,YMAX=-0.12,0.18
ZMIN,ZMAX=0.80,1.12
ABS_X_MIN=0.055
MARGIN_Y=0.045
MARGIN_Z=0.045
LAMBDA=0.32
CYCLES=4
MAX_DX=0.012

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
    if not (YMIN <= y <= YMAX and ZMIN <= z <= ZMAX and abs(co.x)>=ABS_X_MIN):
        return 0.0
    dy=min(y-YMIN,YMAX-y)
    dz=min(z-ZMIN,ZMAX-z)
    return smoothstep01(dy/MARGIN_Y)*smoothstep01(dz/MARGIN_Z)

weights=[boundary_weight(co) for co in body_before]
editable={i for i,w in enumerate(weights) if w>0.0}
fixed=set(range(len(mesh.vertices)))-editable
assert editable, 'No B1b editable vertices selected'

neighbors=[set() for _ in mesh.vertices]
for e in mesh.edges:
    a,b=e.vertices
    neighbors[a].add(b); neighbors[b].add(a)

def same_side_neighbors(i,current):
    xi=current[i].x
    sign=1.0 if xi>=0 else -1.0
    ns=[j for j in neighbors[i] if current[j].x*sign>0]
    return ns if ns else list(neighbors[i])

def fair_inward_x_pass():
    current=[v.co.copy() for v in mesh.vertices]
    updates={}
    for i in sorted(editable):
        ns=same_side_neighbors(i,current)
        assert ns
        src=body_before[i].x
        sign=1.0 if src>=0 else -1.0
        radius=abs(current[i].x)
        average=sum(abs(current[j].x) for j in ns)/len(ns)
        # Only reduce outward local residual; never fill valleys outward.
        residual=max(0.0,radius-average)
        target=radius-LAMBDA*weights[i]*residual
        target=max(abs(src)-MAX_DX,target,1e-6)
        updates[i]=sign*min(radius,target)
    for i,x in updates.items():
        co=mesh.vertices[i].co
        mesh.vertices[i].co=(x,co.y,co.z)
    mesh.update()

for _ in range(CYCLES):
    fair_inward_x_pass()

# All Y/Z exact, fixed X exact.
for i,v in enumerate(mesh.vertices):
    src=body_before[i]
    assert v.co.y==src.y, f'Y changed {i}'
    assert v.co.z==src.z, f'Z changed {i}'
    if i in fixed:
        assert v.co.x==src.x, f'fixed X changed {i}'

# Topology exact.
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

dx={i:mesh.vertices[i].co.x-body_before[i].x for i in editable}
absdx=[abs(v) for v in dx.values()]
max_dx=max(absdx) if absdx else 0.0
mean_dx=sum(absdx)/len(absdx) if absdx else 0.0
changed=sum(1 for v in absdx if v>1e-10)
assert max_dx <= MAX_DX+1e-8
assert all(mesh.vertices[i].co.x*body_before[i].x>0 for i in editable)
assert all(abs(mesh.vertices[i].co.x)<=abs(body_before[i].x)+1e-9 for i in editable), 'Outward movement'
max_outward=max([max(0.0,abs(mesh.vertices[i].co.x)-abs(body_before[i].x)) for i in editable])

x_before=(min(v.x for v in body_before),max(v.x for v in body_before))
x_after=(min(v.co.x for v in mesh.vertices),max(v.co.x for v in mesh.vertices))
x_extent_drift=max(abs(x_after[0]-x_before[0]),abs(x_after[1]-x_before[1]))
assert x_extent_drift <= 0.006+1e-9, f'whole body X extent drift too large: {x_extent_drift}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(fixed):
        h.update(b'body');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    # Y/Z for editable vertices are also hard-fixed
    for i in sorted(editable):
        h.update(b'yz');h.update(str(i).encode());h.update(repr((mesh.vertices[i].co.y,mesh.vertices[i].co.z)).encode())
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B1b-v2-x-only-shoulder-plane-fairing',
 'source':'S-vibe-b0-v025.blend',
 'decision':'REVIEW_PENDING',
 'body_object':body.name,
 'method':'boundary-tapered same-side X-only inward residual reduction',
 'region':{'y_min':YMIN,'y_max':YMAX,'z_min':ZMIN,'z_max':ZMAX,'abs_x_min':ABS_X_MIN,'margin_y':MARGIN_Y,'margin_z':MARGIN_Z},
 'parameters':{'lambda':LAMBDA,'positive_passes':CYCLES,'max_abs_delta_x':MAX_DX,'negative_pass':False},
 'editable_vertex_count':len(editable),
 'fixed_body_vertex_count':len(fixed),
 'fixed_vertex_indices':sorted(fixed),
 'editable_vertex_indices':sorted(editable),
 'changed_vertex_count':changed,
 'max_abs_delta_x':max_dx,
 'mean_abs_delta_x':mean_dx,
 'max_outward_delta_x':max_outward,
 'budget_saturated_vertex_count':sum(1 for d in absdx if d>=MAX_DX-1e-7),
 'whole_body_x_before':x_before,
 'whole_body_x_after':x_after,
 'whole_body_x_extent_drift':x_extent_drift,
 'all_body_yz_unchanged':True,
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
with open(os.path.join(OUT,'S-vibe-b1b-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b1b-v2.blend'),compress=True)
print('VIBE_B1B_V2_EDIT_COMPLETE',json.dumps(report))
