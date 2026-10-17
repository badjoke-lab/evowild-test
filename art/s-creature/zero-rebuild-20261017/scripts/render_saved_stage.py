"""Render saved geometry from independent Blender process; no image synthesis."""
import bpy,sys,json,time
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:]
stage=args[0];views=args[1:] or ['SIDE','FRONT','FRONT34','REAR34','BACK']
root=Path(bpy.data.filepath).parent
sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24
sc.cycles.use_denoising=True
sc.render.resolution_x=1200;sc.render.resolution_y=900;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
meta={'source':bpy.data.filepath,'engine':sc.render.engine,'samples':sc.cycles.samples,'views':{}}
for v in views:
 sc.camera=bpy.data.objects['CAM_'+v]
 sc.render.filepath=str(root/'renders'/stage/(v+'.png'))
 t=time.time();bpy.ops.render.render(write_still=True)
 meta['views'][v]={'camera_matrix':[list(x) for x in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,'file':sc.render.filepath,'seconds':time.time()-t}
 (root/'evidence'/('RENDER_'+stage+'.json')).write_text(json.dumps(meta,indent=2)+'\n')
print('RENDER_STAGE_DONE',stage)
