"""Refine the existing pelvic color boundary and inspect actual live geometry.

This follows 76 in the same live session. No source asset is overwritten.
"""
import bpy, json, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']; m=b.data
stored=np.load(ROOT/'evidence/R8_TRIAL_A_ARRAYS.npz')
assert np.array_equal(np.array([v.co[:] for v in m.vertices]),stored['rest'])
assert 'R8 pelvic planes' not in m.color_attributes
old=m.color_attributes['R6 welded pelvis palette']
attr=m.color_attributes.new(name='R8 pelvic planes',type=old.data_type,domain=old.domain)
# Creating CustomData may invalidate the earlier RNA attribute handle.
old=m.color_attributes['R6 welded pelvis palette']
mat=m.materials[5].copy(); mat.name='S | R8 pelvic planes'
node=next(n for n in mat.node_tree.nodes if n.type=='VERTEX_COLOR'); node.layer_name=attr.name
m.materials.append(mat); slot=len(m.materials)-1
changed=0; white_corners=0; boundary_corners=0
for p in m.polygons:
    if p.material_index!=5: continue
    c=p.center; z=float(c.z)
    cx=float(np.interp(z,[1.10,1.35,1.55,1.75,1.95,2.10],[1.23,1.12,1.,.86,.67,.55]) if c.y<0 else
             np.interp(z,[1.10,1.30,1.55,1.75,1.95,2.10],[.80,.75,.72,.69,.58,.52]))
    u=c.x-cx
    # Restrained ivory / pearl / slate planes, following the existing thigh.
    white=np.array([.86,.88,.90]) if u<-.025 else np.array([.69,.76,.84]) if u<.095 else np.array([.44,.53,.65])
    for li in p.loop_indices:
        original=np.array(old.data[li].color[:3]); lum=float(original.mean())
        # Preserve the R7 skin pattern location while narrowing its blurred
        # transition. This is baked surface color, carried by the same vertices.
        t=float(np.clip((lum-.23)/.10,0,1)); t=t*t*(3-2*t)
        dark=np.array([.035,.046,.067])
        col=dark*(1-t)+white*t
        attr.data[li].color=(*col,1)
        white_corners+=int(t==1); boundary_corners+=int(0<t<1)
    p.material_index=slot; changed+=1
m.update()
sc=bpy.context.scene; sc.frame_set(1)
sc['stage']='R8_UNSAVED_FORM_TRIAL_A'
sc['candidate_status']='REVISE; real pelvic vertex edit and sharper same-palette boundary, pending full verification'
# Actual Blender rendering in memory, before retaining a model file.
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=12
sc.cycles.seed=17; sc.cycles.use_denoising=True
sc.render.resolution_x=800; sc.render.resolution_y=680; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
sc.camera=bpy.data.objects['TEST_SIDE_HIP']
out=ROOT/'renders/R8_UNSAVED_SIDE_HIP.png'; assert not out.exists()
sc.render.filepath=str(out)
report=ROOT/'evidence/R8_SURFACE_EDIT.json'; assert not report.exists()
report.write_text(json.dumps({'local_faces':changed,'white_corners':white_corners,'boundary_corners':boundary_corners,
 'method':'Existing R7 pelvis palette mask narrowed; ivory/pearl/slate surface regions follow original thigh axis. No mesh overlay.',
 'geometry_source':'R8_TRIAL_A_ARRAYS.npz','status':'UNSAVED visual trial'},indent=2)+'\n')
print('SURFACE_EDIT',changed,'faces; render target',str(out))
