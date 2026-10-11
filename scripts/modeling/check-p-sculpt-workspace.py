import bpy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'art/p-creature/workspaces/P-v6-canonical-sculpt-review.blend'
m=json.loads((ROOT/'art/p-creature/workspaces/P-v6-canonical-sculpt-review.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(p))
scene=bpy.context.scene
assert scene.get('approval','').startswith('REVIEW_PENDING'),scene.get('approval')
assert scene.camera and scene.camera.name=='CAM_SIDE'
assert all(bpy.data.objects.get('CAM_'+n) for n in ['SIDE','FRONT','FRONT34','REAR34','BACK'])
ref=bpy.data.objects['CANONICAL_P_IMAGE__DO_NOT_MODIFY']
assert ref.data.packed_file
assert ref.get('canonical_sha256')==m['reference_sha256']
assert sum(o.type=='MESH' for o in bpy.data.objects)>=m['mesh_objects']
print('P_CANONICAL_WORKSPACE_REOPENED_SUCCESS')
