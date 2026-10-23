"""Run in live Blender MCP: shape the existing R7 pelvic skin, without remeshing.

No file is saved here. Geometry and strain are measured before a trial is retained.
The prior vertex order, faces, rig, weights and animation are kept intact.
"""
import bpy, json, hashlib
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/'protected/S_ZERO_R7_RIG_PROTECTED.blend'
out = ROOT/'evidence/R8_SCULPT_TRIAL_A.json'
assert not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
sc=bpy.context.scene; sc.frame_set(1)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']; m=b.data
rest=np.array([v.co[:] for v in m.vertices]); edges=np.array([e.vertices[:] for e in m.edges])
m.calc_loop_triangles(); tris=np.array([t.vertices[:] for t in m.loop_triangles])
weights=np.zeros((len(rest),len(b.vertex_groups)))
for v in m.vertices:
    for g in v.groups: weights[v.index,g.group]=g.weight
def smooth(a):
    a=np.clip(a,0,1); return a*a*(3-2*a)
def metrics(r,p):
    er=np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)/np.linalg.norm(r[edges[:,1]]-r[edges[:,0]],axis=1)
    c0=np.cross(r[tris[:,1]]-r[tris[:,0]],r[tris[:,2]]-r[tris[:,0]])
    c1=np.cross(p[tris[:,1]]-p[tris[:,0]],p[tris[:,2]]-p[tris[:,0]])
    ar=np.linalg.norm(c1,axis=1)/np.linalg.norm(c0,axis=1)
    cos=np.sum(c0*c1,axis=1)/(np.linalg.norm(c0,axis=1)*np.linalg.norm(c1,axis=1))
    return dict(edge_max=float(er.max()),edge_min=float(er.min()),area_min=float(ar.min()),area_max=float(ar.max()),normal_cos_min=float(cos.min()),negative_normals=int((cos<0).sum()))
def sweep():
    rows=[]
    r=np.array([v.co[:] for v in m.vertices])
    for f in [1,6,12,18,24]:
        sc.frame_set(f); bpy.context.view_layer.update()
        ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
        p=np.array([v.co[:] for v in me.vertices]); ev.to_mesh_clear()
        rows.append(dict(frame=f,**metrics(r,p)))
    sc.frame_set(1)
    return rows
baseline=sweep()
x,y,z=rest.T; ay=abs(y); side=np.sign(y)
near=y<0
cx=np.where(near,np.interp(z,[1.10,1.35,1.55,1.75,1.95,2.10],[1.23,1.12,1.,.86,.67,.55]),
                 np.interp(z,[1.10,1.30,1.55,1.75,1.95,2.10],[.80,.75,.72,.69,.58,.52]))
dx=x-cx
support=smooth((x-.30)/.14)*smooth((1.37-x)/.14)*smooth((z-1.12)/.16)*smooth((2.06-z)/.12)*smooth((ay-.15)/.12)
# Freeze the tail root and fade into its boundary without a displacement step.
support*=1-smooth((x-1.00)/.10)*smooth((z-(1.78-.75*(x-1.12))+.06)/.10)
cap=np.interp(z,[1.1,1.3,1.5,1.7,1.9,2.1],[.30,.35,.395,.425,.39,.32])-.22*abs(dx)
delta=np.zeros_like(rest)
# Two long lateral planes meet along the original thigh axis. Their envelope
# only reduces the existing bulb; it creates no separate plate or new anatomy.
delta[:,1]=-side*np.maximum(ay-cap,0)*.85*support
lower=np.exp(-((z-1.48)/.23)**2)
delta[:,0]=-.14*dx*lower*support-.012*np.exp(-((z-1.90)/.11)**2)*support
delta[:,2]=.006*np.exp(-((z-1.87)/.13)**2)*support
size=np.linalg.norm(delta,axis=1)
delta*=np.minimum(1,.045/np.maximum(size,1e-12))[:,None]
changed=np.linalg.norm(delta,axis=1)>1e-9
candidate=rest+delta
unguarded=metrics(rest,candidate.astype(np.float32).astype(float))
# The inherited Boolean skin has several extremely thin triangles. Limit
# displacement around those triangles instead of allowing them to reverse.
c0=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
a0=np.linalg.norm(c0,axis=1)
guard=[]
for iteration in range(48):
    candidate=(rest+delta).astype(np.float32).astype(float)
    c1=np.cross(candidate[tris[:,1]]-candidate[tris[:,0]],candidate[tris[:,2]]-candidate[tris[:,0]])
    a1=np.linalg.norm(c1,axis=1); ar=a1/a0
    cos=np.sum(c0*c1,axis=1)/np.maximum(a0*a1,1e-30)
    bad=(ar<.65)|(ar>1.5)|(cos<.94)
    guard.append({'iteration':iteration,'bad_faces':int(bad.sum()),'area_min':float(ar.min()),'cos_min':float(cos.min())})
    if not bad.any(): break
    ids=np.unique(tris[bad]); mask=np.zeros(len(rest),dtype=bool); mask[ids]=True
    for _ in range(2):
        ee=edges[np.any(mask[edges],axis=1)]; mask[np.unique(ee)]=True
    delta[mask]*=.70
assert not bad.any(),guard[-1]
for v,p in zip(m.vertices,candidate): v.co=p
m.update(); candidate=np.array([v.co[:] for v in m.vertices])
static=metrics(rest,candidate)
assert static['negative_normals']==0 and static['area_min']>.50,static
after=sweep()
np.savez_compressed(ROOT/'evidence/R8_TRIAL_A_ARRAYS.npz',rest=candidate,original=rest,edges=edges,tris=tris,weights=weights)
report={'blender':bpy.app.version_string,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'operation':'Direct vertex edits of existing R7 continuous skin in live Blender MCP; no new meshes or generated assets.',
 'vertices_moved':int((np.linalg.norm(candidate-rest,axis=1)>0).sum()),'max_displacement':float(np.linalg.norm(candidate-rest,axis=1).max()),
 'unguarded_rejected':unguarded,'local_static_guards':guard,
 'static_relative_to_R7':static,'R7_frames':baseline,'trial_frames':after,'weights_rig_animation_unchanged':True,
 'status':'UNSAVED TRIAL; visual review and full sweep required'}
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
