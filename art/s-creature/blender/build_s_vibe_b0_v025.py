"""Experimental Vibe Gate B0-v025: continuity feasibility test.
Source: immutable accepted Gate A model S-vibe-a4-v2.blend.
Join core + four limb cages, then voxel-remesh the joined closed volumes.
Preserve crest and all toe meshes exactly. Never overwrite Gate A.
"""
import bpy, os, json, hashlib, bmesh
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']

CORE='S_rebuild_core_head_crest_neck_torso_tail'
UNION_NAMES=[
 CORE,
 'S_forelimb_L','S_forelimb_R',
 'S_hindlimb_L','S_hindlimb_R'
]
CREST='S_reference_crest_v11'
union_objs=[bpy.data.objects[n] for n in UNION_NAMES]
crest=bpy.data.objects[CREST]

preserved=[o for o in cage.objects if o.type=='MESH' and o.name not in UNION_NAMES]
assert crest in preserved
# Preserve crest + all toe meshes; no unexpected preserved geometry.
toe_names=sorted([o.name for o in preserved if '_toe_' in o.name])
assert len(toe_names)==12, toe_names
assert sorted(o.name for o in preserved)==sorted([CREST]+toe_names)

preserved_before={o.name:[v.co.copy() for v in o.data.vertices] for o in preserved}
preserved_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in preserved}

def preserved_hash():
    h=hashlib.sha256()
    for name in sorted(preserved_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
        for i,p in enumerate(o.data.polygons):
            h.update(name.encode());h.update(b'p');h.update(str(i).encode());h.update(repr(tuple(p.vertices)).encode())
    return h.hexdigest()

pres_hash_before=preserved_hash()

# Source union bounds for comparison.
all_source=[v.co.copy() for o in union_objs for v in o.data.vertices]
src_min=Vector((min(p.x for p in all_source),min(p.y for p in all_source),min(p.z for p in all_source)))
src_max=Vector((max(p.x for p in all_source),max(p.y for p in all_source),max(p.z for p in all_source)))

# Join blockout volumes.
bpy.ops.object.select_all(action='DESELECT')
for o in union_objs: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects[CORE]
bpy.ops.object.join()
body=bpy.context.view_layer.objects.active
body.name='S_B0_continuous_body_v025'
body.data.name='S_B0_continuous_body_v025_mesh'

# Voxel-remesh the joined original mesh data.
voxel_size=0.025
assert hasattr(body.data,'remesh_voxel_size')
body.data.remesh_voxel_size=voxel_size
if hasattr(body.data,'remesh_voxel_adaptivity'):
    body.data.remesh_voxel_adaptivity=0.0
if hasattr(body.data,'use_remesh_preserve_volume'):
    body.data.use_remesh_preserve_volume=True
if hasattr(body.data,'use_remesh_fix_poles'):
    body.data.use_remesh_fix_poles=True

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active=body
body.select_set(True)
assert bpy.ops.object.voxel_remesh.poll(), 'object.voxel_remesh unavailable'
bpy.ops.object.voxel_remesh()

# Basic body validation.
body.data.update()
body_verts=len(body.data.vertices); body_polys=len(body.data.polygons)
assert body_verts>0 and body_polys>0

bm=bmesh.new(); bm.from_mesh(body.data)
nonmanifold=sum(1 for e in bm.edges if len(e.link_faces)!=2)
bm.free()

coords=[v.co for v in body.data.vertices]
out_min=Vector((min(p.x for p in coords),min(p.y for p in coords),min(p.z for p in coords)))
out_max=Vector((max(p.x for p in coords),max(p.y for p in coords),max(p.z for p in coords)))

# Preserved crest/toes exact.
for name,coords0 in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords0)
    for i,co in enumerate(coords0):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'preserved vertex changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name], f'preserved topology changed {name}'
assert preserved_hash()==pres_hash_before

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B0-v025-continuity-feasibility',
 'source':'S-vibe-a4-v2.blend',
 'decision':'REVIEW_PENDING',
 'method':'join core+4 limbs then object.voxel_remesh',
 'voxel_size':voxel_size,
 'joined_source_objects':UNION_NAMES,
 'output_body_object':body.name,
 'body_vertex_count':body_verts,
 'body_polygon_count':body_polys,
 'nonmanifold_edge_count':nonmanifold,
 'source_bbox_min':list(src_min),
 'source_bbox_max':list(src_max),
 'output_bbox_min':list(out_min),
 'output_bbox_max':list(out_max),
 'preserved_meshes':sorted(preserved_before),
 'preserved_geometry_hash':pres_hash_before,
 'preserved_geometry_unchanged':True,
 'gate_a_source_overwritten':False,
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b0-v025-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b0-v025.blend'),compress=True)
print('VIBE_B0_V025_EDIT_COMPLETE',json.dumps(report))
