"""Capture Blender's actual viewport, including each integer and half frame.

Run through MCP with MODE='static' or MODE='motion', START=1/13, END=12/24.
"""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
mode=globals().get('MODE','static');start=globals().get('START',1);end=globals().get('END',12)
variant=globals().get('VARIANT','B');suffix='' if variant=='B' else variant
assert Path(bpy.data.filepath)==ROOT/('verification/S_ZERO_R8_FORM_TRIAL_'+variant+'.blend')
sc=bpy.context.scene
window=bpy.context.window_manager.windows[0]
area=next(a for a in window.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW');sp=area.spaces.active
sp.overlay.show_overlays=False
assert 'MATERIAL' in [i.identifier for i in sp.shading.bl_rna.properties['type'].enum_items]
sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True
if mode!='static' or globals().get('SHADING')=='SOLID':
    sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO'
    sp.shading.show_shadows=True;sp.shading.show_cavity=True
capture=[]
with bpy.context.temp_override(window=window,area=area,region=region):
    if mode=='static':
        jobs=[(1,v,False) for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']]
    else:
        jobs=[]
        for f in range(start,end+1):
            jobs.append((float(f),'SIDE',True))
            if f<24:jobs.append((f+.5,'SIDE',True))
            if f in [1,12,24]:jobs.extend([(float(f),v,True) for v in ['REAR34','BACK']])
    for time,view,detail in jobs:
        f=int(time);sc.frame_set(f,subframe=float(time-f));bpy.context.view_layer.update()
        sp.region_3d.view_perspective='ORTHO'
        sp.region_3d.view_location=Vector((.80,0,1.52) if detail else (.03,0,1.56))
        sp.region_3d.view_distance=2.5 if detail else 6.5
        sp.region_3d.view_rotation=bpy.data.objects['CAM_'+view].matrix_world.to_quaternion()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=3 if mode=='static' else 1)
        name=('R8'+suffix+'_HIP_T%05.2f_%s.png'%(time,view)) if detail else 'R8'+suffix+'_STATIC_'+view+'.png'
        p=ROOT/'viewport'/name;assert not p.exists()
        result=bpy.types.blendermcp_server.get_viewport_screenshot(max_size=1000,filepath=str(p),format='png')
        assert result.get('success'),result
        capture.append({'time':time,'view':view,'detail':detail,'shading':sp.shading.type,'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out=ROOT/'evidence'/('MCP_CAPTURE_'+suffix+('_' if suffix else '')+mode+('_'+str(start)+'_'+str(end) if mode!='static' else '')+'.json')
assert not out.exists();out.write_text(json.dumps(capture,indent=2)+'\n')
sc.frame_set(1)
print('MCP_CAPTURED',len(capture),mode,start,end)
