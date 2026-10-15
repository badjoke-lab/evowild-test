"""Explicitly restore all Blender mesh coordinates from pre-V5 preview checkpoint.

Use through live MCP execute_blender_code if SIDE/FRONT/FRONT34 shows a worse shape.
Does not save source files. Removes preview backup only after exact restoration.
"""
import bpy, bmesh, numpy as np
from pathlib import Path
STATION=Path(__file__).resolve().parents[1]/'experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
OUT=STATION/'review-v5'
filename=Path(bpy.data.filepath).resolve()
assert filename.parent==OUT and filename.name=='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend'
backup=OUT/'V5_RECOVERY_PREVIEW_BEFORE.npy'
assert backup.is_file(),'No preview backup found'
before=np.load(backup,allow_pickle=False).astype(np.float32)
bodies=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.name=='geometry_0']
assert len(bodies)==1
body=bodies[0]
if body.mode!='OBJECT':
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.mode_set(mode='OBJECT')
mesh=body.data
assert before.shape==(len(mesh.vertices),3)
mesh.vertices.foreach_set('co',before.ravel())
mesh.update()
actual=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
assert np.array_equal(actual,before)
body['v5_preview_only']='REVERTED_TO_V4'
body['review_decision']='REVISE'
backup.unlink()
print('S_HUNYUAN_V5_PREVIEW_ROLLBACK_EXACT_PASS_NO_BLEND_SAVED',len(mesh.vertices))
