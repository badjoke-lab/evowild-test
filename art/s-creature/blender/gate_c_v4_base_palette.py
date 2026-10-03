"""Gate C v4: object-level base-palette preview only."""
import bpy,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v3.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
scene=bpy.context.scene

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

# Ensure this is the first material pass.
assert len(bpy.data.materials)==0

def make_mat(name,rgba,rough=.62):
    m=bpy.data.materials.new(name)
    m.diffuse_color=rgba
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value=rgba
        bsdf.inputs['Roughness'].default_value=rough
        bsdf.inputs['Metallic'].default_value=0.0
    return m

core_mat=make_mat('S_CORE_BLUEGRAY',(0.38,0.50,0.64,1.0),.58)
limb_mat=make_mat('S_LIMB_NAVY',(0.13,0.20,0.30,1.0),.62)
crest_mat=make_mat('S_CREST_SLATE',(0.30,0.39,0.50,1.0),.52)
toe_mat=make_mat('S_TOE_DARK',(0.08,0.12,0.18,1.0),.68)

core_name='S_rebuild_core_head_crest_neck_torso_tail'
crest_name='S_rebuild_crest_low_fan_group'
limbs={'S_forelimb_L','S_forelimb_R','S_hindlimb_L','S_hindlimb_R'}

for o in cage.objects:
    if o.type!='MESH': continue
    o.data.materials.clear()
    if o.name==core_name:
        o.data.materials.append(core_mat)
    elif o.name==crest_name:
        o.data.materials.append(crest_mat)
    elif o.name in limbs:
        o.data.materials.append(limb_mat)
    elif '_toe_' in o.name:
        o.data.materials.append(toe_mat)
    else:
        raise AssertionError('unexpected mesh '+o.name)

scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.light='STUDIO'
scene.display.shading.studio_light='paint.sl'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=False

# Geometry and modifiers stay exact.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifiers changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v4.blend'),compress=True)
report={
 'gate':'C','pass':'v4','status':'REVIEW_PENDING','source':'S-gateC-v3.blend',
 'scope':'object-level base materials only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'coordinates_unchanged':True,'topology_unchanged':True,'modifier_stacks_unchanged':True,
 'materials':{
   'core':[0.38,0.50,0.64,1.0],
   'limbs':[0.13,0.20,0.30,1.0],
   'crest':[0.30,0.39,0.50,1.0],
   'toes':[0.08,0.12,0.18,1.0]
 },
 'workbench_color_type':'MATERIAL',
 'no_eye':True,'no_cue_band':True,'no_pattern':True,'no_animation':True,'no_armature':True,
 'limitations':['Gate C v4 palette review pending','Palette is base blocking only, not final surface pattern']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v4.json'),'w'),indent=2)
print('GATE_C_V4_SAVED',json.dumps(report))
