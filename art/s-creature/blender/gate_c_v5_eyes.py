"""Gate C v5: add two small cyan eye-marker objects only."""
import bpy,bmesh,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v4.blend'))
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

detail=bpy.data.collections.get('S_PRODUCTION_DETAIL')
if detail is None:
    detail=bpy.data.collections.new('S_PRODUCTION_DETAIL')
    bpy.context.scene.collection.children.link(detail)
assert bpy.data.objects.get('S_eye_L') is None and bpy.data.objects.get('S_eye_R') is None

eye_mat=bpy.data.materials.new('S_EYE_CYAN')
eye_mat.diffuse_color=(0.05,0.72,0.95,1.0)
eye_mat.use_nodes=True
bsdf=eye_mat.node_tree.nodes.get('Principled BSDF')
if bsdf:
    bsdf.inputs['Base Color'].default_value=(0.05,0.72,0.95,1.0)
    bsdf.inputs['Roughness'].default_value=.32
    bsdf.inputs['Metallic'].default_value=0.0

def make_eye(name,x):
    mesh=bpy.data.meshes.new(name+'_mesh')
    bm=bmesh.new()
    bmesh.ops.create_uvsphere(bm,u_segments=16,v_segments=8,radius=.017)
    bm.to_mesh(mesh); bm.free()
    o=bpy.data.objects.new(name,mesh)
    detail.objects.link(o)
    o.location=(x,-.714,1.274)
    o.scale=(1.0,.72,.92)
    mesh.materials.append(eye_mat)
    for p in mesh.polygons:p.use_smooth=True
    return o

left=make_eye('S_eye_L',-.073)
right=make_eye('S_eye_R',.073)

# Hard locks on all pre-existing cage meshes.
for o in cage.objects:
    if o.type!='MESH':continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifiers changed'
    assert [m.name for m in o.data.materials]==source_mats[o.name],o.name+' materials changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v5.blend'),compress=True)
report={
 'gate':'C','pass':'v5','status':'REVIEW_PENDING','source':'S-gateC-v4.blend',
 'scope':'two eye-marker objects only',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'existing_coordinates_unchanged':True,'existing_topology_unchanged':True,
 'existing_modifiers_unchanged':True,'existing_material_assignments_unchanged':True,
 'eye_objects':['S_eye_L','S_eye_R'],
 'eye_radius':.017,'eye_color':[0.05,0.72,0.95,1.0],
 'no_cue_band':True,'no_pattern':True,'no_animation':True,'no_armature':True,
 'limitations':['Gate C v5 eye-marker review pending','Cue Band and surface pattern remain deferred']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v5.json'),'w'),indent=2)
print('GATE_C_V5_SAVED',json.dumps(report))
