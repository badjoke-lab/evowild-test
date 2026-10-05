"""Gate C v6: restrained eye-marker correction only."""
import bpy,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v5.blend'))
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

left=bpy.data.objects['S_eye_L']
right=bpy.data.objects['S_eye_R']
old={
 'L':{'location':tuple(left.location),'scale':tuple(left.scale)},
 'R':{'location':tuple(right.location),'scale':tuple(right.scale)},
}

# Smaller, slightly more medial and flatter against the head.
left.location=(-.062,-.711,1.273)
right.location=( .062,-.711,1.273)
left.scale=(.72,.46,.64)
right.scale=(.72,.46,.64)

# Hard locks on all pre-existing cage meshes.
for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name],o.name+' coords changed'
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name],o.name+' topology changed'
    assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name],o.name+' modifiers changed'
    assert [m.name for m in o.data.materials]==source_mats[o.name],o.name+' materials changed'
assert digest()==source_hash
assert len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v6.blend'),compress=True)
report={
 'gate':'C','pass':'v6','status':'REVIEW_PENDING','source':'S-gateC-v5.blend',
 'scope':'eye object transforms only',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'existing_coordinates_unchanged':True,'existing_topology_unchanged':True,
 'existing_modifiers_unchanged':True,'existing_material_assignments_unchanged':True,
 'eye_objects':['S_eye_L','S_eye_R'],
 'old_eye_transforms':old,
 'new_eye_locations':[[-.062,-.711,1.273],[.062,-.711,1.273]],
 'new_eye_scale':[.72,.46,.64],
 'no_cue_band':True,'no_pattern':True,'no_animation':True,'no_armature':True,
 'limitations':['Gate C v6 eye-marker review pending','Cue Band and surface pattern remain deferred']
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v6.json'),'w'),indent=2)
print('GATE_C_V6_SAVED',json.dumps(report))
