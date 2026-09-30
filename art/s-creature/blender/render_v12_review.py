"""Render v12 with the same cameras and settings as v11."""
import bpy,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output','review','v12');os.makedirs(OUT,exist_ok=True)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=768;s.render.resolution_y=768;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.eevee.taa_render_samples=64
for stem in ('front','side','front34'):
 s.camera=bpy.data.objects['CAM_'+stem.upper()];s.render.filepath=os.path.join(OUT,'S_blockout_'+stem+'.png');bpy.ops.render.render(write_still=True)
print('v12 review rendered')
