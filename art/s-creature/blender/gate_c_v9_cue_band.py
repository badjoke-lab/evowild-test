"""Gate C v9: forehead-band placement and integrated cue lights only."""
import bpy,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateC-v8.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}
source_mods={o.name:[(m.name,m.type) for m in o.modifiers] for o in cage.objects if o.type=='MESH'}
source_mats={o.name:[m.name for m in o.data.materials] for o in cage.objects if o.type=='MESH'}
eye_state={n:(tuple(bpy.data.objects[n].location),tuple(bpy.data.objects[n].scale)) for n in ('S_eye_L','S_eye_R')}

# Bring the visible band toward the forehead, clear of the crest roots.
o=bpy.data.objects['S_cue_band_top']; o.location=(0,-.692,1.302); o.scale=(.074,.017,.012)
for n,x,rz in [('S_cue_band_L',-.064,-.08),('S_cue_band_R',.064,.08)]:
    o=bpy.data.objects[n]
    o.location=(x,-.675,1.286)
    o.scale=(.013,.042,.017)
    o.rotation_euler=(0,0,rz)
for n,x in [('S_cue_pad_L',-.073),('S_cue_pad_R',.073)]:
    o=bpy.data.objects[n]
    o.location=(x,-.650,1.282)
    o.scale=(.018,.026,.021)
# Integrate cyan lights onto the pad rather than outside the eye line.
for n,x in [('S_cue_light_L',-.079),('S_cue_light_R',.079)]:
    o=bpy.data.objects[n]
    o.location=(x,-.649,1.283)
    o.scale=(.004,.003,.004)
o=bpy.data.objects['S_cue_receiver']; o.location=(0,-.580,1.315); o.scale=(.030,.022,.013)

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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateC-v9.blend'),compress=True)
report={'gate':'C','pass':'v9','status':'REVIEW_PENDING','source':'S-gateC-v8.blend','scope':'Cue Band transforms only','base_geometry_sha256':digest(),'existing_coordinates_unchanged':True,'existing_topology_unchanged':True,'existing_modifiers_unchanged':True,'existing_material_assignments_unchanged':True,'eye_transforms_unchanged':True,'no_pattern':True}
json.dump(report,open(os.path.join(OUT,'S-gateC-v9.json'),'w'),indent=2)
