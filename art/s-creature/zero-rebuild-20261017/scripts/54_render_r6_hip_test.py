"""Render the saved validation armature in three real poses; never save input."""
import bpy, hashlib, json, os, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=Path(bpy.data.filepath)
assert source.name=='S_ZERO_R6_HIP_DEFORMATION_TEST_B.blend'
out=ROOT/'renders/r6_hip_test_b';out.mkdir(exist_ok=True)
meta_path=ROOT/'evidence/RENDER_R6_HIP_TEST_B.json'
assert not meta_path.exists()
log=(ROOT/'evidence/RENDER_R6_HIP_TEST_B.log').open('x')
old_out=os.dup(1);old_err=os.dup(2);os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
sc=bpy.context.scene
try:sc.render.engine='CYCLES'
except TypeError as exc:raise RuntimeError('Cycles unavailable') from exc
sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.seed=17;sc.cycles.use_denoising=True
sc.render.resolution_x=960;sc.render.resolution_y=800;sc.render.resolution_percentage=100
fmt=sc.render.image_settings
assert 'PNG' in [i.identifier for i in fmt.bl_rna.properties['file_format'].enum_items]
fmt.file_format='PNG';fmt.color_mode='RGBA'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
meta={'source':str(source.relative_to(ROOT)),'source_sha256':sha,'blender':bpy.app.version_string,
      'samples':24,'seed':17,'resolution':[960,800],'poses':{},'note':'Actual armature evaluation. Ground hidden because this is a hip test without IK or ground contacts.'}
for state,frame in [('NEUTRAL',1),('NEAR_FORWARD',12),('NEAR_BACK',24)]:
    sc.frame_set(frame);bpy.context.view_layer.update()
    meta['poses'][state]={'frame':frame,'views':{}}
    for view in ['SIDE','SIDE_HIP','REAR34_HIP','BACK_HIP']:
        target=out/(state+'_'+view+'.png');assert not target.exists()
        sc.camera=bpy.data.objects['TEST_'+view];sc.render.filepath=str(target)
        start=time.time();bpy.ops.render.render(write_still=True)
        meta['poses'][state]['views'][view]={'file':str(target.relative_to(ROOT)),
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'seconds':time.time()-start,
            'camera_matrix':[list(r) for r in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale}
        meta_path.write_text(json.dumps(meta,indent=2)+'\n')
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
os.dup2(old_out,1);os.dup2(old_err,2);os.close(old_out);os.close(old_err);log.close()
print('R6 HIP TEST: 12 saved-file renders completed.',flush=True)
