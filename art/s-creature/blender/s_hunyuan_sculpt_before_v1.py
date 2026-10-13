"""Render protected source with the exact V1 comparison cameras and lighting."""
import bpy,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'art/s-creature/blender'))
from s_hunyuan_sculpt_review_render import render
station=root/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
bpy.ops.wm.open_mainfile(filepath=str(station/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
render(body,[body.matrix_world@v.co for v in body.data.vertices],station/'review-v1','BEFORE')
