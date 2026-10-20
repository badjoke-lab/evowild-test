"""Saved-file Cycles renders: recovered formal R6 five views and three hip poses."""
import bpy,hashlib,json,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert bpy.app.version==(4,3,2)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
mode=args[0] if args else 'all'
jobs=[]
if mode in ['all','static']:
    jobs.append(('revised_r6',ROOT/'S_ZERO_CANDIDATE_REVISED_R6.blend',
        [('STATIC',1,v,'CAM_'+v) for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']],32,(1200,900)))
if mode in ['all','hip']:
    jobs.append(('hip_recovered_c',ROOT/'verification/S_ZERO_R6_HIP_DEFORMATION_RECOVERED_C.blend',
        [(s,f,v,'TEST_'+v) for s,f in [('NEUTRAL',1),('NEAR_FORWARD',12),('NEAR_BACK',24)]
         for v in ['SIDE','SIDE_HIP','REAR34_HIP','BACK_HIP']],24,(960,800)))
for label,source,views,samples,resolution in jobs:
    out=ROOT/'renders'/label;out.mkdir(exist_ok=False)
    meta_path=ROOT/'evidence'/('RENDER_'+label+'.json');assert not meta_path.exists()
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    sc=bpy.context.scene
    try:sc.render.engine='CYCLES'
    except TypeError as exc:raise RuntimeError('Cycles not available') from exc
    sc.cycles.device='CPU';sc.cycles.samples=samples;sc.cycles.seed=17;sc.cycles.use_denoising=True
    sc.render.resolution_x,sc.render.resolution_y=resolution;sc.render.resolution_percentage=100
    settings=sc.render.image_settings
    assert 'PNG' in [i.identifier for i in settings.bl_rna.properties['file_format'].enum_items]
    assert 'RGBA' in [i.identifier for i in settings.bl_rna.properties['color_mode'].enum_items]
    settings.file_format='PNG';settings.color_mode='RGBA'
    meta={'source':str(source.relative_to(ROOT)),'source_sha256':sha,'blender':bpy.app.version_string,
          'engine':sc.render.engine,'samples':samples,'seed':17,'resolution':resolution,
          'view_transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'renders':[]}
    for state,frame,view,camera in views:
        target=out/((view if state=='STATIC' else state+'_'+view)+'.png')
        assert not target.exists()
        sc.frame_set(frame);sc.camera=bpy.data.objects[camera];sc.render.filepath=str(target)
        bpy.context.view_layer.update()
        start=time.time();bpy.ops.render.render(write_still=True)
        meta['renders'].append({'state':state,'frame':frame,'view':view,'file':str(target.relative_to(ROOT)),
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'seconds':time.time()-start,
            'camera_matrix':[list(r) for r in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale})
        print('RECOVERY_RENDER',label,state,view,flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
    meta_path.write_text(json.dumps(meta,indent=2)+'\n')
print('ALL_REQUESTED_RECOVERY_RENDERS_COMPLETE',flush=True)
