"""Render the independently saved models with matching cameras and settings."""
import bpy,json,hashlib,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
mode=sys.argv[sys.argv.index('--')+1]
variant=sys.argv[sys.argv.index('--')+2] if len(sys.argv)>sys.argv.index('--')+2 else 'B'
suffix='' if variant=='B' else variant;new='R8'+suffix
if mode=='static':
    sources=[('R7',ROOT/'protected/S_ZERO_R7_STATIC_PROTECTED.blend'),(new,ROOT/('S_ZERO_CANDIDATE_REVISED_'+new+'.blend'))]
    views=[(1,v,'CAM_'+v) for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']];res=(800,600);samples=16
elif mode=='hip':
    sources=[('R7',ROOT/'protected/S_ZERO_R7_RIG_PROTECTED.blend'),(new,ROOT/('verification/S_ZERO_'+new+'_HIP_DEFORMATION_VERIFIED.blend'))]
    views=[(f,v,'TEST_'+v) for f in [1,6,12,18,24] for v in ['SIDE_HIP','REAR34_HIP','BACK_HIP'] if v=='SIDE_HIP' or f in [1,12,24]];res=(640,544);samples=12
else:raise ValueError(mode)
for label,source in sources:
    folder=ROOT/'renders'/(label+'_'+mode)
    out=ROOT/'evidence'/('RENDER_'+label+'_'+mode+'.json')
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if label=='R7' and folder.exists():
        prior=json.loads(out.read_text());assert prior['source_sha256']==sha and prior['resolution']==list(res) and prior['samples']==samples and prior['seed']==17
        assert all(hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256'] for r in prior['renders'])
        print('REUSE_VERIFIED_R7_RENDERS',mode,flush=True);continue
    folder.mkdir(exist_ok=False);assert not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=samples;sc.cycles.seed=17;sc.cycles.use_denoising=True
    sc.render.resolution_x,sc.render.resolution_y=res;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    rows=[]
    for frame,view,camera in views:
        p=folder/('F%02d_%s.png'%(frame,view));assert not p.exists()
        sc.frame_set(frame);sc.camera=bpy.data.objects[camera];sc.render.filepath=str(p);bpy.context.view_layer.update()
        started=time.time();bpy.ops.render.render(write_still=True)
        rows.append({'frame':frame,'view':view,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
          'camera_matrix':[list(r) for r in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,'seconds':time.time()-started})
        print('RENDER_DONE',label,mode,frame,view,flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
    out.write_text(json.dumps({'blender':bpy.app.version_string,'source':str(source.relative_to(ROOT)),'source_sha256':sha,
      'engine':sc.render.engine,'samples':samples,'seed':17,'resolution':res,'view_transform':sc.view_settings.view_transform,
      'look':sc.view_settings.look,'renders':rows},indent=2)+'\n')
print('RENDER_BATCH_COMPLETE',mode,flush=True)
