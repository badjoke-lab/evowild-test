"""Gate C v7: add a compact Cue Band preview as new detail objects only."""
import bpy,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v6.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices
    )).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
source_mods={o.name:[(m.name,m.type) for m in o.modifiers] for o in cage.objects if o.type=='MESH'}
source_mats={o.name:[m.name for m in o.data.materials] for o in cage.objects if o.type=='MESH'}
eye_state={n:(tuple(bpy.data.objects[n].location),tuple(bpy.data.objects[n].scale)) for n in ('S_eye_L','S_eye_R')}

detail=bpy.data.collections.get('S_PRODUCTION_DETAIL')
if detail is None:
    detail=bpy.data.collections.new('S_PRODUCTION_DETAIL')
    bpy.context.scene.collection.children.link(detail)

for n in (
    'S_cue_band_top','S_cue_band_L','S_cue_band_R',
    'S_cue_pad_L','S_cue_pad_R','S_cue_light_L','S_cue_light_R','S_cue_receiver'
):
    assert bpy.data.objects.get(n) is None, n+' already exists'

def make_mat(name,rgba,rough=.45,metal=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color=rgba
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=rgba
        bsdf.inputs['Roughness'].default_value=rough
        bsdf.inputs['Metallic'].default_value=metal
    return m

band_mat=make_mat('S_CUE_BAND_DARK',(0.035,0.060,0.095,1.0),.38,.05)
pad_mat=make_mat('S_CUE_PAD_NAVY',(0.055,0.110,0.170,1.0),.34,.02)
light_mat=make_mat('S_CUE_LIGHT_CYAN',(0.03,0.78,0.96,1.0),.28,0.0)

def add_box(name,loc,scale,mat,rot=(0,0,0),bevel=.004):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    o=bpy.context.object
    o.name=name
    # move object to production detail collection
    for c in list(o.users_collection):
        c.objects.unlink(o)
    detail.objects.link(o)
    o.scale=scale
    o.data.materials.append(mat)
    if bevel>0:
        mod=o.modifiers.new('CueBandBevel','BEVEL')
        mod.width=bevel
        mod.segments=2
    return o

def add_sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc)
    o=bpy.context.object
    o.name=name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    detail.objects.link(o)
    o.scale=scale
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth=True
    return o

# Thin top bridge immediately behind the eyes and below the crest root.
add_box('S_cue_band_top',(0,-.642,1.305),(.060,.030,.009),band_mat,bevel=.003)

# Side rails hug the skull; small yaw keeps them aligned with the head taper.
add_box('S_cue_band_L',(-.061,-.650,1.286),(.010,.052,.014),band_mat,rot=(0,0,-.10),bevel=.003)
add_box('S_cue_band_R',( .061,-.650,1.286),(.010,.052,.014),band_mat,rot=(0,0, .10),bevel=.003)

# Compact cue pads sit behind the eye markers rather than outside them.
add_box('S_cue_pad_L',(-.069,-.610,1.282),(.014,.023,.017),pad_mat,bevel=.004)
add_box('S_cue_pad_R',( .069,-.610,1.282),(.014,.023,.017),pad_mat,bevel=.004)

# Tiny cyan indicators: readable but subordinate to the eyes.
add_sphere('S_cue_light_L',(-.081,-.608,1.283),(.006,.004,.006),light_mat)
add_sphere('S_cue_light_R',( .081,-.608,1.283),(.006,.004,.006),light_mat)

# Rear/top receiver module, centered and kept below the crest saddle.
add_box('S_cue_receiver',(0,-.586,1.314),(.024,.018,.011),pad_mat,bevel=.003)

# Hard locks on all existing cage meshes and v6 eye transforms.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifiers changed'
    assert [m.name for m in o.data.materials]==source_mats[o.name],o.name+' materials changed'
for n,(loc,scale) in eye_state.items():
    o=bpy.data.objects[n]
    assert tuple(o.location)==loc and tuple(o.scale)==scale,n+' eye transform changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v7.blend'),compress=True)
report={
 'gate':'C','pass':'v7','status':'REVIEW_PENDING','source':'S-gateC-v6.blend',
 'scope':'new Cue Band detail objects only',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'existing_coordinates_unchanged':True,'existing_topology_unchanged':True,
 'existing_modifiers_unchanged':True,'existing_material_assignments_unchanged':True,
 'eye_transforms_unchanged':True,
 'cue_band_objects':['S_cue_band_top','S_cue_band_L','S_cue_band_R','S_cue_pad_L','S_cue_pad_R','S_cue_light_L','S_cue_light_R','S_cue_receiver'],
 'no_pattern':True,'no_animation':True,'no_armature':True,
 'limitations':['Gate C v7 Cue Band review pending','Body surface pattern remains deferred']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v7.json'),'w'),indent=2)
print('GATE_C_V7_SAVED',json.dumps(report))
