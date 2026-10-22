"""Inspect protected R6 in live Blender MCP; no source-file writes."""
import bpy, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'protected/S_ZERO_R6_RIG_PROTECTED.blend'
OUT=ROOT/'evidence/R6_BASELINE.json'
assert not OUT.exists()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rest=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges])
m.calc_loop_triangles();tris=np.array([t.vertices[:] for t in m.loop_triangles])
length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1)
cross=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
areas=np.linalg.norm(cross,axis=1)
weights=np.zeros((len(rest),3))
for v in m.vertices:
    for g in v.groups:weights[v.index,g.group]=g.weight
records=[]
for frame in range(1,25):
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
    er=np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)/length
    ar=np.linalg.norm(np.cross(p[tris[:,1]]-p[tris[:,0]],p[tris[:,2]]-p[tris[:,0]]),axis=1)/areas
    r={'frame':frame,'edge_max':float(er.max()),'edge_min':float(er.min()),'area_min':float(ar.min()),'area_max':float(ar.max()),
       'pose_quaternions':{pb.name:list(pb.rotation_quaternion) for pb in rig.pose.bones}}
    if frame in [1,6,12,18,24]:
        r['compressed_triangles']=[{'indices':tris[i].tolist(),'ratio':float(ar[i]),'coords':rest[tris[i]].tolist(),'weights':weights[tris[i]].tolist()} for i in np.argsort(ar)[:12]]
        r['stretched_edges']=[{'indices':edges[i].tolist(),'ratio':float(er[i]),'coords':rest[edges[i]].tolist(),'weights':weights[edges[i]].tolist()} for i in np.argsort(er)[-8:][::-1]]
    records.append(r)
np.savez_compressed(ROOT/'evidence/R6_BODY_ARRAYS.npz',rest=rest,edges=edges,tris=tris,weights=weights)
report={'blender':bpy.app.version_string,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'body_matrix':[list(r) for r in b.matrix_world],'groups':[g.name for g in b.vertex_groups],
 'modifiers':[(md.name,md.type) for md in b.modifiers],
 'bones':{bn.name:{'head':list(bn.head_local),'tail':list(bn.tail_local)} for bn in rig.data.bones},'frames':records}
OUT.write_text(json.dumps(report,indent=2)+'\n')
window=bpy.context.window_manager.windows[0]
area=next(a for a in window.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
sp=area.spaces.active;sp.overlay.show_overlays=False;sp.shading.type='MATERIAL'
# Solid uses the same studio setup for both snapshots and avoids shader compilation races.
sp.shading.type='SOLID';sp.shading.color_type='MATERIAL';sp.shading.light='STUDIO'
sp.shading.show_shadows=True;sp.shading.show_cavity=True
captures=[]
with bpy.context.temp_override(window=window,area=area,region=region):
    for frame in [1,6,12,18,24]:
        bpy.context.scene.frame_set(frame)
        for view in ['SIDE','REAR34','BACK']:
            sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_location=Vector((.80,0,1.52));sp.region_3d.view_distance=2.5
            sp.region_3d.view_rotation=bpy.data.objects['CAM_'+view].matrix_world.to_quaternion()
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
            path=ROOT/'viewport'/('R6_F%02d_%s.png'%(frame,view));assert not path.exists()
            result=bpy.types.blendermcp_server.get_viewport_screenshot(max_size=1200,filepath=str(path),format='png')
            assert result.get('success'),result
            captures.append({'frame':frame,'view':view,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'result':result})
(ROOT/'evidence/MCP_R6_CAPTURES.json').write_text(json.dumps(captures,indent=2)+'\n')
print('R6_BASELINE',[(r['frame'],round(r['edge_max'],4),round(r['area_min'],4)) for r in records])
