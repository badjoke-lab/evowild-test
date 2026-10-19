"""Capture actual Blender MCP viewport pixels after reopening saved R5.

This captures the live viewport, separate from the five Cycles renders.
Camera/UI changes are temporary and never written back to the .blend.
"""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'S_ZERO_CANDIDATE_REVISED_R5.blend'
OUT=ROOT/'renders/revised_r5_viewport'
REPORT=ROOT/'evidence/MCP_R5_VIEWPORT_CAPTURE.json'
assert not REPORT.exists()
OUT.mkdir(parents=True,exist_ok=True)
digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
window=bpy.context.window_manager.windows[0]
area=next(a for a in window.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
space=area.spaces.active
space.overlay.show_overlays=False
space.shading.type='SOLID'
space.shading.color_type='MATERIAL'
space.shading.light='STUDIO'
space.shading.show_shadows=True
space.shading.show_cavity=True
space.region_3d.view_perspective='ORTHO'
space.region_3d.view_location=Vector((1.72,0,1.40))
space.region_3d.view_distance=2.3
records={}
with bpy.context.temp_override(window=window,area=area,region=region):
    for name in ['SIDE','FRONT34','REAR34','BACK']:
        space.region_3d.view_rotation=bpy.data.objects['CAM_'+name].matrix_world.to_quaternion()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
        path=OUT/(name+'.png');assert not path.exists()
        result=bpy.types.blendermcp_server.get_viewport_screenshot(max_size=1200,filepath=str(path),format='png')
        assert result.get('success'),result
        records[name]=result
        records[name]['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==digest
REPORT.write_text(json.dumps({'source':SOURCE.name,'source_sha256':digest,'actual_live_viewport':True,
    'display':'Solid material colors, studio cavity; not Cycles or retouched image.','views':records},indent=2)+'\n')
print('LIVE_R5_VIEWPORTS_SAVED',list(records))

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
assert not bpy.data.is_dirty
