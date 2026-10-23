"""R8 C: replace B's visibly dimpled displacement field with a smooth one.

Starts from preserved R7. Smooth compact anatomical fields reshape existing
vertices; any thin-triangle guard attenuates over a spatial radius, not rings.
"""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/R8_FORM_TRIAL_C.json';assert not OUT.exists()
source=ROOT/'protected/S_ZERO_R7_RIG_PROTECTED.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data;sc=bpy.context.scene;sc.frame_set(1)
rest=np.array([v.co[:] for v in m.vertices]);e=np.array([ed.vertices[:] for ed in m.edges])
m.calc_loop_triangles();t=np.array([tr.vertices[:] for tr in m.loop_triangles])
c0=np.cross(rest[t[:,1]]-rest[t[:,0]],rest[t[:,2]]-rest[t[:,0]]);a0=np.linalg.norm(c0,axis=1)
def smooth(a):
    a=np.clip(a,0,1);return a*a*(3-2*a)
def static(p):
    c=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]])
    a=np.linalg.norm(c,axis=1);cos=np.sum(c0*c,axis=1)/np.maximum(a0*a,1e-30)
    ar=a/a0;return ar,cos
x,y,z=rest.T;ay=abs(y);side=np.sign(y)
cx=np.where(y<0,.68+.69*(1.95-z),.67+.08*(1.80-z))
dx=x-cx
support=smooth((x-.30)/.18)*smooth((1.39-x)/.18)*smooth((z-1.12)/.20)*smooth((2.06-z)/.16)*smooth((ay-.15)/.19)
support*=1-smooth((x-1.00)/.12)*smooth((z-(1.78-.75*(x-1.12))+.06)/.12)
bulb=np.exp(-(dx/.25)**2-((z-1.52)/.33)**2)
delta=np.zeros_like(rest)
delta[:,1]=-side*.029*bulb*support
delta[:,0]=-.075*dx*np.exp(-((z-1.48)/.25)**2)*support-.008*np.exp(-((z-1.90)/.13)**2)*support
delta[:,2]=.004*np.exp(-((z-1.87)/.15)**2)*support
guard=[]
for iteration in range(30):
    p=(rest+delta).astype(np.float32).astype(float)
    ar,cos=static(p);bad=(ar<.68)|(ar>1.4)|(cos<.94)
    guard.append({'iteration':iteration,'bad_faces':int(bad.sum()),'area_min':float(ar.min()),'area_max':float(ar.max()),'normal_cos_min':float(cos.min())})
    if not bad.any():break
    centers=rest[t[bad]].mean(axis=1)
    # Use a minimum radial envelope to avoid compounding overlapping guards.
    attenuation=np.ones(len(rest))
    for center in centers:
        dist2=np.sum((rest-center)**2,axis=1)
        attenuation=np.minimum(attenuation,1-.42*np.exp(-dist2/.085**2))
    delta*=attenuation[:,None]
assert not bad.any(),guard[-1]
for v,pv in zip(m.vertices,p):v.co=pv
m.update();actual=np.array([v.co[:] for v in m.vertices]);ar,cos=static(actual)
frames=[]
length=np.linalg.norm(actual[e[:,1]]-actual[e[:,0]],axis=1)
cr=np.cross(actual[t[:,1]]-actual[t[:,0]],actual[t[:,2]]-actual[t[:,0]]);area=np.linalg.norm(cr,axis=1)
for f in [1,6,12,18,24]:
    sc.frame_set(f);bpy.context.view_layer.update();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    q=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
    er=np.linalg.norm(q[e[:,1]]-q[e[:,0]],axis=1)/length
    cq=np.cross(q[t[:,1]]-q[t[:,0]],q[t[:,2]]-q[t[:,0]]);aq=np.linalg.norm(cq,axis=1)/area
    frames.append({'frame':f,'edge_max':float(er.max()),'area_min':float(aq.min()),'area_max':float(aq.max()),'negative_normal_count':int((np.sum(cq*cr,axis=1)<0).sum())})
sc.frame_set(1)
# Reuse the reviewed surface chart, without copying B's mesh displacement.
with bpy.data.libraries.load(str(ROOT/'verification/S_ZERO_R8_HIP_DEFORMATION_VERIFIED.blend'),link=False) as (available,loaded):
    loaded.materials=['S | R8 pelvic planes']
m.materials.append(loaded.materials[0])
for face in m.polygons:
    if face.material_index==5:face.material_index=6
attr=m.color_attributes.new(name='R8 plane coordinates',type='FLOAT_COLOR',domain='CORNER')
for face in m.polygons:
    if face.material_index!=6:continue
    for li in face.loop_indices:
        xx,yy,zz=rest[m.loops[li].vertex_index]
        if yy<0:
            levels=[1.20,1.30,1.45,1.65,1.85,2.03]
            left=np.interp(zz,levels,[1.245,1.14,.99,.82,.62,.51]);right=np.interp(zz,levels,[1.245,1.245,1.235,1.16,1.035,.70]);center=np.interp(zz,levels,[1.245,1.195,1.11,.99,.82,.61])
        else:
            levels=[1.12,1.30,1.50,1.70,1.88,2.03]
            left=np.interp(zz,levels,[.80,.695,.57,.52,.48,.50]);right=np.interp(zz,levels,[.80,.86,.915,.915,.835,.65]);center=np.interp(zz,levels,[.80,.78,.74,.72,.65,.58])
        side_edge=np.interp(zz,[1.1,1.4,1.75,1.95,2.1],[.28,.275,.235,.12,.08])
        distance=min(xx-left,right-xx,abs(yy)-side_edge,zz-levels[0],2.035-zz)
        attr.data[li].color=(.5+distance,.5+(xx-center)*2.7,zz/2.1,1)
m.update()
np.savez_compressed(ROOT/'evidence/R8_TRIAL_C_ARRAYS.npz',rest=actual,original=rest,edges=e,tris=t)
report={'operation':'Smooth anatomical displacement of existing R7 vertices. No rings with hard attenuation edges, no remesh.',
 'supersedes':'B form has visible high-frequency dimples in SOLID viewport; do not select it as the next modeling base.',
 'guard':guard,'moved_vertices':int((np.linalg.norm(actual-rest,axis=1)>0).sum()),'max_displacement':float(np.linalg.norm(actual-rest,axis=1).max()),
 'static_area_min':float(ar.min()),'static_normal_cos_min':float(cos.min()),'static_negative_normals':int((cos<0).sum()),
 'frames':frames,'status':'UNSAVED C; visual review required'}
OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
