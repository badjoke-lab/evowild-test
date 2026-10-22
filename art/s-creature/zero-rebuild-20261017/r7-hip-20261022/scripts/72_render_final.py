"""Render actual saved Blender geometry with identical cameras and lighting."""
import bpy,json,hashlib,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'hip'
jobs=[]
if mode=='hip':
    for label,source in [('R6',ROOT/'protected/S_ZERO_R6_RIG_PROTECTED.blend'),('R7',ROOT/'verification/S_ZERO_R7_HIP_TRIAL_B.blend')]:
        jobs.append((label+'_final_hip',source,[(f,v,'TEST_'+v) for f in [1,6,12,18,24] for v in ['SIDE_HIP','REAR34_HIP','BACK_HIP'] if v=='SIDE_HIP' or f in [12,24]],12,(640,544)))
elif mode=='static':
    for label,source in [('R6',ROOT/'protected/S_ZERO_R6_STATIC_PROTECTED.blend'),('R7',ROOT/'S_ZERO_CANDIDATE_REVISED_R7.blend')]:
        jobs.append((label+'_final_static',source,[(1,v,'CAM_'+v) for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']],16,(800,600)))
else:raise ValueError(mode)
for label,source,views,samples,res in jobs:
    folder=ROOT/'renders'/label;folder.mkdir(exist_ok=False)
    report=ROOT/'evidence'/('RENDER_'+label+'.json');assert not report.exists()
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=samples
    sc.cycles.seed=17;sc.cycles.use_denoising=True
    sc.render.resolution_x,sc.render.resolution_y=res;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    metadata={'blender':bpy.app.version_string,'source':str(source.relative_to(ROOT)),'sha256':digest,'engine':'CYCLES','samples':samples,
     'seed':17,'resolution':res,'view_transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'renders':[]}
    for frame,view,camera in views:
        output=folder/('F%02d_%s.png'%(frame,view));assert not output.exists()
        sc.frame_set(frame);sc.camera=bpy.data.objects[camera];sc.render.filepath=str(output)
        bpy.context.view_layer.update();start=time.time();bpy.ops.render.render(write_still=True)
        metadata['renders'].append({'file':str(output.relative_to(ROOT)),'frame':frame,'view':view,
         'camera_matrix':[list(r) for r in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,
         'seconds':time.time()-start,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
        print('R7_RENDER_DONE',label,frame,view,flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
    report.write_text(json.dumps(metadata,indent=2)+'\n')
print('R7_RENDER_BATCH_COMPLETE',mode,flush=True)
