"""Reproduce the live C correction: R7 inner rim fixed, smooth exterior taper.

Execute after 85. This is the same correction run through Blender MCP; outputs
are append-only and are never regenerated over saved evidence.
"""
import bpy,numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/R8_C_INNER_RIM_FIX.json';assert not OUT.exists()
data=np.load(ROOT/'evidence/R8_TRIAL_C_ARRAYS.npz')
r0=data['original'];old=data['rest'];e=data['edges'];t=data['tris']
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
ay=abs(r0[:,1]);factor=smooth((ay-.23)/.16)/np.maximum(smooth((ay-.15)/.19),1e-12)
r=r0+(old-r0)*factor[:,None]
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data
for v,p in zip(m.vertices,r):v.co=p
m.update();r=np.array([v.co[:] for v in m.vertices])
c0=np.cross(r0[t[:,1]]-r0[t[:,0]],r0[t[:,2]]-r0[t[:,0]])
c=np.cross(r[t[:,1]]-r[t[:,0]],r[t[:,2]]-r[t[:,0]])
ar=np.linalg.norm(c,axis=1)/np.linalg.norm(c0,axis=1)
cos=np.sum(c*c0,axis=1)/(np.linalg.norm(c,axis=1)*np.linalg.norm(c0,axis=1))
assert ar.min()>.68 and cos.min()>.94
length=np.linalg.norm(r[e[:,1]]-r[e[:,0]],axis=1);area=np.linalg.norm(c,axis=1);rows=[]
for f in [1,6,12,18,24]:
    bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
    ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
    er=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1)/length
    cp=np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]);a=np.linalg.norm(cp,axis=1)/area
    rows.append({'frame':f,'edge_max':float(er.max()),'area_min':float(a.min()),'area_max':float(a.max()),'negative_normals':int((np.sum(c*cp,axis=1)<0).sum())})
bpy.context.scene.frame_set(1)
report={'reason':'Preserve R7 inner hip rim exactly (abs(y)<=0.23); smooth transition to external form edit. Removes the 0.0038 rearward edge regression in initial C.',
 'static_area_min':float(ar.min()),'static_normal_cos_min':float(cos.min()),
 'max_displacement':float(np.linalg.norm(r-r0,axis=1).max()),'vertices_moved':int((np.linalg.norm(r-r0,axis=1)>0).sum()),'frames':rows}
OUT.write_text(json.dumps(report,indent=2)+'\n')
np.savez_compressed(ROOT/'evidence/R8_C_FINAL_ARRAYS.npz',rest=r,original=r0,edges=e,tris=t)
print(json.dumps(report))
