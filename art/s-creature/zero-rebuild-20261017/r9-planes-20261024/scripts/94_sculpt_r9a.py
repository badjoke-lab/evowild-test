"""Actual existing-mesh edit through Blender MCP; R8C files stay immutable."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert Path(bpy.data.filepath)==ROOT/'protected/S_ZERO_R8C_RIG_PROTECTED.blend'
OUT=ROOT/'evidence/R9A_SCULPT.json';TRIAL=ROOT/'verification/S_ZERO_R9A_FORM_TRIAL.blend'
assert not OUT.exists() and not TRIAL.exists()
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data;sc=bpy.context.scene;sc.frame_set(1)
r=np.array([v.co[:] for v in m.vertices]);e=np.array([a.vertices[:] for a in m.edges]);m.calc_loop_triangles();t=np.array([a.vertices[:] for a in m.loop_triangles])
c0=np.cross(r[t[:,1]]-r[t[:,0]],r[t[:,2]]-r[t[:,0]]);a0=np.linalg.norm(c0,axis=1)
def smooth(a):
    a=np.clip(a,0,1);return a*a*(3-2*a)
x,y,z=r.T;ay=abs(y)
cx=np.where(y<0,.68+.69*(1.95-z),.67+.08*(1.8-z));dx=x-cx
support=smooth((x-.32)/.17)*smooth((1.40-x)/.16)*smooth((z-1.18)/.22)*smooth((2.03-z)/.19)*smooth((ay-.23)/.16)
support*=1-smooth((x-1.00)/.12)*smooth((z-(1.78-.75*(x-1.12))+.06)/.12)
# Two broad sloping planes meet across the thigh axis. C1 shoulder of the cap
# blends into untouched skin without the per-ring attenuation that dimpled R8B.
cap=.423+.06*(z-1.60)-.18*abs(dx)
d=np.maximum(ay-cap,0);eps=.008
positive=np.where(d<eps,d*d/(2*eps),d-eps/2)
delta=np.zeros_like(r);delta[:,1]=-np.sign(y)*positive*support
checks=[]
for strength in [.72,.54,.405]:
    p=(r+strength*delta).astype(np.float32).astype(float)
    c=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]);a=np.linalg.norm(c,axis=1)
    ar=a/a0;cos=np.sum(c*c0,axis=1)/np.maximum(a*a0,1e-30)
    checks.append({'strength':strength,'area_min':float(ar.min()),'area_max':float(ar.max()),'normal_cos_min':float(cos.min())})
    if ar.min()>.78 and ar.max()<1.2 and cos.min()>.97:break
else:raise AssertionError(checks)
assert np.array_equal(p[ay<=.23],r[ay<=.23])
for v,co in zip(m.vertices,p):v.co=co
m.update()
# Broaden the upper white area; retain the lower taper and material family.
# A localized union with the inherited R6 white field closes upper gray islands.
chart=m.color_attributes['R8 plane coordinates'];old_chart=np.array([q.color[:] for q in chart.data])
chart.name='R9 plane coordinates';inherited=m.color_attributes['R6 welded pelvis palette']
original=np.load(ROOT.parent/'r8-form-20261023/evidence/R8_C_FINAL_ARRAYS.npz')['original']
for face in m.polygons:
    if face.material_index!=6:continue
    for li in face.loop_indices:
        xx,yy,zz=original[m.loops[li].vertex_index]
        if yy<0:
            levels=[1.20,1.30,1.45,1.65,1.85,2.06]
            left=np.interp(zz,levels,[1.245,1.14,.965,.77,.52,.43]);right=np.interp(zz,levels,[1.245,1.245,1.25,1.205,1.10,.88])
            center=np.interp(zz,levels,[1.245,1.195,1.105,.985,.80,.64])
        else:
            levels=[1.12,1.30,1.50,1.70,1.88,2.06]
            left=np.interp(zz,levels,[.80,.695,.54,.47,.42,.43]);right=np.interp(zz,levels,[.80,.86,.94,.96,.91,.77])
            center=np.interp(zz,levels,[.80,.78,.74,.71,.65,.60])
        edge=np.interp(zz,[1.1,1.4,1.75,1.95,2.1],[.28,.275,.225,.09,.06])
        distance=min(xx-left,right-xx,abs(yy)-edge,zz-levels[0],2.075-zz)
        # Only preserve original bright skin on the outer upper pelvis.
        lum=sum(inherited.data[li].color[:3])/3
        if 1.78<zz<2.08 and abs(yy)>.13 and .38<xx<1.14 and lum>.45:
            distance=max(distance,min((lum-.45)*.18,(zz-1.78)*.4,(2.08-zz)*.4,abs(yy)-.13))
        chart.data[li].color=(.5+distance,.5+(xx-center)*2.7,zz/2.1,1)
mat=m.materials[6].copy();mat.name='S | R9 pelvic planes';m.materials[6]=mat
for node in mat.node_tree.nodes:
    if node.type=='VERTEX_COLOR':node.layer_name='R9 plane coordinates'
m.update();rest=np.array([v.co[:] for v in m.vertices]);length=np.linalg.norm(rest[e[:,1]]-rest[e[:,0]],axis=1)
cr=np.cross(rest[t[:,1]]-rest[t[:,0]],rest[t[:,2]]-rest[t[:,0]]);area=np.linalg.norm(cr,axis=1)
frames=[]
for f in [1,6,12,18,24]:
    sc.frame_set(f);bpy.context.view_layer.update();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();q=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
    er=np.linalg.norm(q[e[:,1]]-q[e[:,0]],axis=1)/length;cq=np.cross(q[t[:,1]]-q[t[:,0]],q[t[:,2]]-q[t[:,0]]);aq=np.linalg.norm(cq,axis=1)/area
    frames.append({'frame':f,'edge_max':float(er.max()),'area_min':float(aq.min()),'area_max':float(aq.max()),'negative_normals':int((np.sum(cq*cr,axis=1)<0).sum())})
assert all(x['edge_max']<1.328385 and x['area_min']>.7605 and x['negative_normals']==0 for x in frames),frames
sc.frame_set(1);sc['stage']='R9A_TRIAL_NOT_APPROVED';sc['candidate_status']='REVISE; pending independent 93-time and image review'
sc.render.filepath=str(ROOT/'renders/UNASSIGNED_R9_RENDER.png')
np.savez_compressed(ROOT/'evidence/R9A_ARRAYS.npz',rest=rest,original=r,edges=e,tris=t)
bpy.ops.wm.save_as_mainfile(filepath=str(TRIAL),compress=True)
report={'operation':'Existing R8C vertices reshaped through live Blender MCP; two broad lateral thigh planes, C1 blended boundary. No new mesh/remesh/image generation.',
 'geometry_checks':checks,'vertices_moved':int((np.linalg.norm(rest-r,axis=1)>0).sum()),'maximum_displacement':float(np.linalg.norm(rest-r,axis=1).max()),
 'inner_hip_rim_abs_y_le_0_23_exact':True,'surface_chart':'Broader upper white field; local union with inherited bright R6 upper skin removes isolated gray islands.',
 'quick_frames':frames,'trial_sha256':hashlib.sha256(TRIAL.read_bytes()).hexdigest(),'decision':'TRIAL: REVISE; visual and 93-time review pending'}
OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
