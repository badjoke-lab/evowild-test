"""Gate C v8: transform-only Cue Band visibility correction."""
import bpy,os,json,hashlib

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v7.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']

def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
source_mods={o.name:[(m.name,m.type) for m in o.modifiers] for o in cage.objects if o.type=='MESH'}
source_mats={o.name:[m.name for m in o.data.materials] for o in cage.objects if o.type=='MESH'}
eye_state={n:(tuple(bpy.data.objects[n].location),tuple(bpy.data.objects[n].scale)) for n in ('S_eye_L','S_eye_R')}

names=['S_cue_band_top','S_cue_band_L','S_cue_band_R','S_cue_pad_L','S_cue_pad_R','S_cue_light_L','S_cue_light_R','S_cue_receiver']
old={n:{'location':tuple(bpy.data.objects[n].location),'scale':tuple(bpy.data.objects[n].scale)} for n in names}

# Expose the band slightly without covering eyes or crest.
bpy.data.objects['S_cue_band_top'].location=(0,-.645,1.306)
bpy.data.objects['S_cue_band_top'].scale=(.074,.034,.011)

for n,x,rz in [('S_cue_band_L',-.066,-.10),('S_cue_band_R',.066,.10)]:
    o=bpy.data.objects[n]
    o.location=(x,-.648,1.288)
    o.scale=(.013,.060,.016)

for n,x in [('S_cue_pad_L',-.078),('S_cue_pad_R',.078)]:
    o=bpy.data.objects[n]
    o.location=(x,-.610,1.283)
    o.scale=(.018,.028,.021)

for n,x in [('S_cue_light_L',-.094),('S_cue_light_R',.094)]:
    o=bpy.data.objects[n]
    o.location=(x,-.608,1.284)
    o.scale=(.007,.005,.007)

o=bpy.data.objects['S_cue_receiver']
o.location=(0,-.582,1.315)
o.scale=(.030,.022,.013)

for o in cage.objects:
    if o.type!='MESH': continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name]
    assert [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    assert [(m.name,m.type) for m in o.modifiers]==source_mods[o.name]
    assert [m.name for m in o.data.materials]==source_mats[o.name]
for n,(loc,scale) in eye_state.items():
    o=bpy.data.objects[n]
    assert tuple(o.location)==loc and tuple(o.scale)==scale
assert digest()==source_hash
assert len(bpy.data.actions)==0 and not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v8.blend'),compress=True)
report={
 'gate':'C','pass':'v8','status':'REVIEW_PENDING','source':'S-gateC-v7.blend',
 'scope':'Cue Band transforms only',
 'source_geometry_sha256':source_hash,'base_geometry_sha256':digest(),
 'existing_coordinates_unchanged':True,'existing_topology_unchanged':True,
 'existing_modifiers_unchanged':True,'existing_material_assignments_unchanged':True,
 'eye_transforms_unchanged':True,
 'cue_band_objects':names,
 'old_transforms':old,
 'no_pattern':True,'no_animation':True,'no_armature':True
}
json.dump(report,open(os.path.join(OUT,'S-gateC-v8.json'),'w'),indent=2)
print('GATE_C_V8_SAVED',json.dumps(report))
