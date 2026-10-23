"""Retain a partially improved R8, with formal unrigged model and separate rig.

Requires the independent 93-time comparison. Both quality decisions stay REVISE.
"""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
variant=globals().get('VARIANT','B');suffix='' if variant=='B' else variant
audit=json.loads((ROOT/('evidence/INDEPENDENT_R7_R8'+suffix+'_SWEEP.json')).read_text())
assert audit['weights_bones_keyframes_exact'] and audit['protected_other_meshes_exact']==140
# Finite Blender float32 evaluation differs by 6.36e-6 at T1.25 for C.
# Keep the exact differences in the report; do not claim bit-identical strain.
assert all(r['max_edge_delta']<1e-6 and r['min_area_delta']>-1e-5 and not r['new_self_pairs'] and not r['new_contact_objects'] for r in audit['per_time_comparison'])
assert all(f['whole_body']['rest_normal_dot_negative']==0 for f in audit['records']['R8']['frames'])
assert audit['static_vs_R7']['rest_normal_dot_negative']==0
STATIC=ROOT/('S_ZERO_CANDIDATE_REVISED_R8'+suffix+'.blend')
RIG=ROOT/('verification/S_ZERO_R8'+suffix+'_HIP_DEFORMATION_VERIFIED.blend')
OUT=ROOT/('evidence/R8'+suffix+'_SAVE_AND_RELOAD_AUDIT.json')
assert not STATIC.exists() and not RIG.exists() and not OUT.exists()
def sig(o):
    m=o.data
    return hashlib.sha256(repr(([tuple(v.co) for v in m.vertices],
      [(tuple(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],
      [(a.name,a.domain,a.data_type,[tuple(d.color) for d in a.data]) for a in m.color_attributes],
      [list(r) for r in o.matrix_world],[ma.name for ma in m.materials])).encode()).hexdigest()
trial=ROOT/('verification/S_ZERO_R8_FORM_TRIAL_'+variant+'.blend')
bpy.ops.wm.open_mainfile(filepath=str(trial),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data;sc=bpy.context.scene;sc.frame_set(1)
# Remove only the now-unused, newly introduced preview color layer.
if 'R8 pelvic planes' in m.color_attributes:m.color_attributes.remove(m.color_attributes['R8 pelvic planes'])
mat=m.materials[6]
for other in list(bpy.data.materials):
    if other!=mat and other.name.startswith('S | R8 pelvic planes') and other.users==0:bpy.data.materials.remove(other)
mat.name='S | R8 pelvic planes'
positions=np.array([v.co[:] for v in m.vertices]);polygons=[tuple(p.vertices) for p in m.polygons]
assignments=[p.material_index for p in m.polygons]
coords=np.array([d.color[:] for d in m.color_attributes['R8 plane coordinates'].data],dtype=np.float32)
sc['stage']='R8'+suffix+'_HIP_DEFORMATION_VERIFICATION_ONLY'
sc['candidate_status']='REVISE; R7 strain maxima retained, area minima improved over 93 samples. Not a gait or production approval.'
sc.render.filepath=str(ROOT/'renders/UNASSIGNED_REVIEW_RENDER.png')
bpy.ops.wm.save_as_mainfile(filepath=str(RIG),compress=True)
rig_geom=sig(b)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'protected/S_ZERO_R7_STATIC_PROTECTED.blend'),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data
protected={o.name:sig(o) for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH' and o!=b}
assert [tuple(p.vertices) for p in m.polygons]==polygons
for v,p in zip(m.vertices,positions):v.co=p
with bpy.data.libraries.load(str(RIG),link=False) as (available,loaded):
    assert 'S | R8 pelvic planes' in available.materials
    loaded.materials=['S | R8 pelvic planes']
assert len(m.materials)==6;m.materials.append(loaded.materials[0])
for p,slot in zip(m.polygons,assignments):p.material_index=slot
attr=m.color_attributes.new(name='R8 plane coordinates',type='FLOAT_COLOR',domain='CORNER')
attr.data.foreach_set('color',coords.ravel());m.update()
b['r8_revision']='Existing R7 pelvic skin: guarded lateral flattening and lower taper; continuous surface-chart white/dark boundary. Rig separate.'
sc=bpy.context.scene;sc.frame_set(1);sc['stage']='S_ZERO_CANDIDATE_REVISED_R8'+suffix
sc['candidate_status']='REVISE; partial pelvis/boundary improvement. Rounded plane construction and reference differences remain. No KEEP or runtime promotion.'
sc.camera=bpy.data.objects['CAM_FRONT34'];sc.render.filepath=str(ROOT/'renders/UNASSIGNED_REVIEW_RENDER.png')
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
assert not bpy.data.actions
assert not any(o.vertex_groups for o in bpy.data.objects if o.type=='MESH')
assert not any(md.type=='ARMATURE' for o in bpy.data.objects for md in o.modifiers)
assert sig(b)==rig_geom
bpy.ops.wm.save_as_mainfile(filepath=str(STATIC),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(STATIC),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
assert sig(b)==rig_geom
assert all(sig(bpy.data.objects[n])==v for n,v in protected.items())
report={'blender':bpy.app.version_string,'source_trial_sha256':hashlib.sha256(trial.read_bytes()).hexdigest(),
 'static':{'file':STATIC.name,'sha256':hashlib.sha256(STATIC.read_bytes()).hexdigest(),'bytes':STATIC.stat().st_size},
 'rig':{'file':str(RIG.relative_to(ROOT)),'sha256':hashlib.sha256(RIG.read_bytes()).hexdigest(),'bytes':RIG.stat().st_size},
 'static_matches_rig_rest_geometry_materials_colors':True,'saved_static_reloaded_exact':True,'protected_other_meshes_exact':len(protected),
 'static_armatures':sum(o.type=='ARMATURE' for o in bpy.data.objects),'static_actions':len(bpy.data.actions),
 'static_vertex_groups':sum(len(o.vertex_groups) for o in bpy.data.objects if o.type=='MESH'),
 'static_armature_modifiers':sum(md.type=='ARMATURE' for o in bpy.data.objects for md in o.modifiers),
 'static_decision':'REVISE: sharper anatomical boundary and modest real taper; broad planes and global reference silhouette remain incomplete.',
 'deformation_decision':'Improved minima with preserved R7 peak strain across 93 samples; REVISE. Hip test only.',
 'production_decision':'No KEEP. No runtime integration.'}
OUT.write_text(json.dumps(report,indent=2)+'\n');print('R8_SEPARATE_MODEL_AND_RIG_SAVED',STATIC.stat().st_size,RIG.stat().st_size)
