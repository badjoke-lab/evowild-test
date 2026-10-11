import bpy,json
from mathutils import Vector
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'art/s-creature/references/00_s_type_modeling_image_v1.png').is_file())
OUT=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/h0-body-armor-pass1'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'S_H0_body_armor_pass1.blend'))
s=bpy.context.scene;cam=s.camera
body=bpy.data.objects['S_H0_Original_Hunyuan_Body']
center=Vector((-.0355,.035,-.0354))
views={'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),'REAR34':(1,1,0),'BACK':(0,1,0)}
s.render.resolution_percentage=100
for mode in ('MATERIAL','SINGLE'):
 s.display.shading.color_type=mode
 s.display.shading.single_color=(.55,.55,.55)
 for variant in ('BASE','H0'):
  body.data.shape_keys.key_blocks['H0_Shoulder_Chest_Haunch_volume'].value=variant=='H0'
  for o in bpy.data.collections['H0_White_segmented_armor'].objects:o.hide_render=variant=='BASE'
  for name,d in views.items():
   cam.location=center+Vector(d).normalized()*5
   cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
   suffix='_CLAY' if mode=='SINGLE' else ''
   s.render.filepath=str(OUT/'review'/('S_'+variant+'_'+name+suffix+'.png'))
   bpy.ops.render.render(write_still=True)
# Save the editable deliverable in its actual revised state, facing FRONT34.
s.display.shading.color_type='MATERIAL'
cam.location=center+Vector(views['FRONT34']).normalized()*5
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(OUT/'review/S_H0_FRONT34.png')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'S_H0_body_armor_pass1.blend'),compress=True)
