"""Experimental Vibe Gate B2a-v5: pre-union forelimb-root topology rebuild.

Source: S-vibe-a4-v2.blend.

Single hypothesis:
The persistent triangular forelimb root is baked into B0 because the accepted
A3a forelimb begins at station0 with no buried proximal transition. Add two
closed 8-sided proximal rings inside the thorax while preserving source
stations0..6 exactly, then regenerate the same 0.025 voxel continuity body.

B2b remains blocked.
"""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output');os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']

CORE='S_rebuild_core_head_crest_neck_torso_tail'
FORE=('S_forelimb_L','S_forelimb_R')
HIND=('S_hindlimb_L','S_hindlimb_R')
UNION_NAMES=[CORE,*FORE,*HIND]
CREST='S_reference_crest_v11'

core=bpy.data.objects[CORE]
foreL=bpy.data.objects[FORE[0]]
foreR=bpy.data.objects[FORE[1]]
hindL=bpy.data.objects[HIND[0]]
hindR=bpy.data.objects[HIND[1]]
crest=bpy.data.objects[CREST]

for o in (foreL,foreR):
    assert len(o.data.vertices)==56,(o.name,len(o.data.vertices))

# Snapshot source forelimb stations0..6 exactly.
fore_source={}
fore_source_topology={}
for o in (foreL,foreR):
    fore_source[o.name]=[
        [o.data.vertices[s*8+k].co.copy() for k in range(8)]
        for s in range(7)
    ]
    fore_source_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

# Snapshot every non-forelimb source mesh before topology edit.
fixed_before={}
fixed_topology={}
for o in cage.objects:
    if o.type=='MESH' and o.name not in FORE:
        fixed_before[o.name]=[v.co.copy() for v in o.data.vertices]
        fixed_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

# Baseline union bbox before root rebuild.
orig_union_objs=[bpy.data.objects[n] for n in UNION_NAMES]
orig_union_coords=[v.co.copy() for o in orig_union_objs for v in o.data.vertices]
baseline_min=Vector((min(p.x for p in orig_union_coords),min(p.y for p in orig_union_coords),min(p.z for p in orig_union_coords)))
baseline_max=Vector((max(p.x for p in orig_union_coords),max(p.y for p in orig_union_coords),max(p.z for p in orig_union_coords)))

# New proximal ring specification.
# sign mirrors X only.
ROOT_SPEC=[
    # absX, Y, Z, lateral radius, sagittal radius
    (0.078,-0.090,1.050,0.090,0.120), # buried embed ring -2
    (0.098,-0.060,1.020,0.080,0.108), # transition ring -1
]

def make_ring(center,prev_center,next_center,lr,sr):
    tangent=next_center-prev_center
    if tangent.length==0:
        tangent=Vector((0,0,-1))
    tangent.normalize()
    lateral=Vector((1,0,0))
    lateral=lateral-tangent*lateral.dot(tangent)
    if lateral.length==0:
        lateral=Vector((1,0,0))
    lateral.normalize()
    sagittal=tangent.cross(lateral)
    if sagittal.length==0:
        sagittal=Vector((0,1,0))
    sagittal.normalize()
    pts=[]
    for k in range(8):
        a=k*math.tau/8.0
        pts.append(center+lateral*(lr*math.cos(a))+sagittal*(sr*math.sin(a)))
    return pts

def source_center(ring):
    return sum((p for p in ring),Vector())/8.0

def rebuild_forelimb(o,sign):
    old_rings=fore_source[o.name]
    old_centers=[source_center(r) for r in old_rings]
    c_m2=Vector((sign*ROOT_SPEC[0][0],ROOT_SPEC[0][1],ROOT_SPEC[0][2]))
    c_m1=Vector((sign*ROOT_SPEC[1][0],ROOT_SPEC[1][1],ROOT_SPEC[1][2]))
    c0=old_centers[0]
    c1=old_centers[1]

    r_m2=make_ring(c_m2,c_m2-(c_m1-c_m2),c_m1,ROOT_SPEC[0][3],ROOT_SPEC[0][4])
    r_m1=make_ring(c_m1,c_m2,c0,ROOT_SPEC[1][3],ROOT_SPEC[1][4])

    rings=[r_m2,r_m1]
    rings.extend([[p.copy() for p in ring] for ring in old_rings])

    verts=[tuple(p) for ring in rings for p in ring]
    faces=[]

    # Proximal cap buried inside thorax.
    faces.append(tuple(reversed(range(8))))

    # Ring loft: 9 rings => 8 intervals.
    for r in range(len(rings)-1):
        a0=r*8
        b0=(r+1)*8
        for k in range(8):
            k1=(k+1)%8
            faces.append((a0+k,a0+k1,b0+k1,b0+k))

    # Distal cap at exact source station6.
    last=(len(rings)-1)*8
    faces.append(tuple(last+k for k in range(8)))

    new_mesh=bpy.data.meshes.new(o.name+'_b2a_v5_mesh')
    new_mesh.from_pydata(verts,[],faces)
    new_mesh.update()

    old_mesh=o.data
    o.data=new_mesh

    # Closed-manifold source limb required before continuity union.
    bm=bmesh.new();bm.from_mesh(new_mesh)
    nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
    bm.free()
    assert not nonmanifold,f'{o.name} rebuilt root non-manifold {len(nonmanifold)}'

    assert len(new_mesh.vertices)==72
    # Existing stations0..6 begin at new ring index 2 and remain exact.
    for s in range(7):
        for k in range(8):
            idx=(s+2)*8+k
            assert tuple(new_mesh.vertices[idx].co)==tuple(old_rings[s][k]),f'{o.name} source station changed {s}:{k}'

    if old_mesh.users==0:
        bpy.data.meshes.remove(old_mesh)

rebuild_forelimb(foreL,-1)
rebuild_forelimb(foreR,1)

# All non-forelimb source geometry must still be exact before union.
for name,coords in fixed_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords),name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co),f'fixed source changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==fixed_topology[name],f'fixed topology changed {name}'

# Validate new union bbox remains local to original morphology.
new_union_objs=[bpy.data.objects[n] for n in UNION_NAMES]
new_union_coords=[v.co.copy() for o in new_union_objs for v in o.data.vertices]
new_union_min=Vector((min(p.x for p in new_union_coords),min(p.y for p in new_union_coords),min(p.z for p in new_union_coords)))
new_union_max=Vector((max(p.x for p in new_union_coords),max(p.y for p in new_union_coords),max(p.z for p in new_union_coords)))

bbox_preunion_drift=max(
    abs(new_union_min.x-baseline_min.x),abs(new_union_max.x-baseline_max.x),
    abs(new_union_min.y-baseline_min.y),abs(new_union_max.y-baseline_max.y),
    abs(new_union_min.z-baseline_min.z),abs(new_union_max.z-baseline_max.z)
)
assert bbox_preunion_drift<=0.030+1e-9,f'pre-union bbox drift {bbox_preunion_drift}'

# Preserve crest + toes exactly through continuity rebuild.
preserved=[o for o in cage.objects if o.type=='MESH' and o.name not in UNION_NAMES]
toe_names=sorted([o.name for o in preserved if '_toe_' in o.name])
assert crest in preserved
assert len(toe_names)==12,toe_names
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

# Join core + rebuilt forelimbs + accepted hindlimbs.
bpy.ops.object.select_all(action='DESELECT')
for o in new_union_objs:o.select_set(True)
bpy.context.view_layer.objects.active=core
bpy.ops.object.join()
body=bpy.context.view_layer.objects.active
body.name='S_B2a_v5_continuous_body'
body.data.name='S_B2a_v5_continuous_body_mesh'

voxel_size=0.025
body.data.remesh_voxel_size=voxel_size
if hasattr(body.data,'remesh_voxel_adaptivity'):body.data.remesh_voxel_adaptivity=0.0
if hasattr(body.data,'use_remesh_preserve_volume'):body.data.use_remesh_preserve_volume=True
if hasattr(body.data,'use_remesh_fix_poles'):body.data.use_remesh_fix_poles=True

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active=body
body.select_set(True)
assert bpy.ops.object.voxel_remesh.poll()
bpy.ops.object.voxel_remesh()
body.data.update()

bm=bmesh.new();bm.from_mesh(body.data)
nonmanifold=[e for e in bm.edges if len(e.link_faces)!=2]
bm.free()
assert len(nonmanifold)==0,f'continuous body non-manifold {len(nonmanifold)}'

coords=[v.co for v in body.data.vertices]
out_min=Vector((min(p.x for p in coords),min(p.y for p in coords),min(p.z for p in coords)))
out_max=Vector((max(p.x for p in coords),max(p.y for p in coords),max(p.z for p in coords)))

bbox_output_drift=max(
    abs(out_min.x-baseline_min.x),abs(out_max.x-baseline_max.x),
    abs(out_min.y-baseline_min.y),abs(out_max.y-baseline_max.y),
    abs(out_min.z-baseline_min.z),abs(out_max.z-baseline_max.z)
)
assert bbox_output_drift<=0.030+1e-9,f'output bbox drift {bbox_output_drift}'

# Crest/toes exact after union/remesh.
for name,coords0 in preserved_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords0)
    for i,co in enumerate(coords0):
        assert tuple(o.data.vertices[i].co)==tuple(co),f'preserved changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==preserved_topology[name]
assert preserved_hash()==pres_hash_before

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'B2a-v5-preunion-forelimb-root-rebuild',
 'source':'S-vibe-a4-v2.blend',
 'decision':'REVIEW_PENDING',
 'method':'add two buried proximal rings to each forelimb, then B0-style join + voxel remesh',
 'voxel_size':voxel_size,
 'new_root_spec':{
   'embed_m2':{'abs_x':ROOT_SPEC[0][0],'y':ROOT_SPEC[0][1],'z':ROOT_SPEC[0][2],'lateral_radius':ROOT_SPEC[0][3],'sagittal_radius':ROOT_SPEC[0][4]},
   'transition_m1':{'abs_x':ROOT_SPEC[1][0],'y':ROOT_SPEC[1][1],'z':ROOT_SPEC[1][2],'lateral_radius':ROOT_SPEC[1][3],'sagittal_radius':ROOT_SPEC[1][4]}
 },
 'rebuilt_forelimb_vertex_count_each':72,
 'source_stations_0_to_6_unchanged':True,
 'non_forelimb_source_geometry_unchanged_before_union':True,
 'baseline_union_bbox_min':list(baseline_min),
 'baseline_union_bbox_max':list(baseline_max),
 'rebuilt_union_bbox_min':list(new_union_min),
 'rebuilt_union_bbox_max':list(new_union_max),
 'preunion_bbox_max_drift':bbox_preunion_drift,
 'output_body_object':body.name,
 'output_body_vertex_count':len(body.data.vertices),
 'output_body_polygon_count':len(body.data.polygons),
 'continuous_nonmanifold_edge_count':0,
 'output_bbox_min':list(out_min),
 'output_bbox_max':list(out_max),
 'output_bbox_max_drift':bbox_output_drift,
 'preserved_meshes':sorted(preserved_before),
 'preserved_geometry_hash':pres_hash_before,
 'preserved_geometry_unchanged':True,
 'gate_a_source_overwritten':False,
 'status':'REVIEW_PENDING'
}
with open(os.path.join(OUT,'S-vibe-b2a-v5-validation.json'),'w') as f:json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-b2a-v5.blend'),compress=True)
print('VIBE_B2A_V5_EDIT_COMPLETE',json.dumps(report))
