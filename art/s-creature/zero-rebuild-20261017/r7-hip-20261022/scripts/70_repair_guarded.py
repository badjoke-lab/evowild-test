"""Actual local mesh relaxation and skin-weight trials on protected R6.

All three original bones, pivots, keyframes and angles are unchanged.
Only the pelvic patch's vertices and mixed hip weights may change.
"""
import bpy, json, hashlib, math
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/R7_TRIALS_B.json'
assert not OUT.exists()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'protected/S_ZERO_R6_RIG_PROTECTED.blend'),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];m=b.data
sc=bpy.context.scene;sc.frame_set(1)
rest0=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges])
m.calc_loop_triangles();tris=np.array([t.vertices[:] for t in m.loop_triangles])
w0=np.zeros((len(rest0),3))
for v in m.vertices:
    for g in v.groups:w0[v.index,g.group]=g.weight
w0/=w0.sum(axis=1)[:,None]

def allowed(p):
    x,y,z=p
    return .30<x<1.27 and 1.27<z<1.93 and abs(y)>.11 and not(x>1.02 and z>1.75-.75*(x-1.12))
initial_mask=np.array([allowed(p) for p in rest0]);mask=initial_mask.copy()
# Every face touching a moved vertex must be wholly within the permitted patch.
for p in m.polygons:
    if not all(initial_mask[i] for i in p.vertices):
        for i in p.vertices:mask[i]=False
# Smooth compact spatial falloff; no displacement at the guard boundaries.
x,y,z=rest0.T
fall=np.clip(np.minimum.reduce([(x-.30)/.12,(1.27-x)/.12,(z-1.27)/.12,(1.93-z)/.12,(abs(y)-.11)/.10]),0,1)
fall*=mask
a,c=edges.T
degree=np.bincount(a,minlength=len(rest0))+np.bincount(c,minlength=len(rest0))
rest=rest0.copy()
original_cross=np.cross(rest0[tris[:,1]]-rest0[tris[:,0]],rest0[tris[:,2]]-rest0[tris[:,0]])
original_area=np.linalg.norm(original_cross,axis=1)
relaxation_checks=[]
# Tangential mesh relaxation redistributes skinny triangles, capped at 4mm.
for iteration in range(4):
    cross=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
    normals=np.zeros_like(rest)
    for j in range(3):np.add.at(normals,tris[:,j],cross)
    normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-15)[:,None]
    avg=np.zeros_like(rest)
    np.add.at(avg,a,rest[c]);np.add.at(avg,c,rest[a]);avg/=degree[:,None]
    delta=avg-rest;delta-=normals*np.sum(delta*normals,axis=1)[:,None]
    step=.32*fall[:,None]*delta
    for backtrack in range(30):
        proposal=rest+step
        shift=proposal-rest0;size=np.linalg.norm(shift,axis=1)
        proposal=rest0+shift*np.minimum(1,.004/np.maximum(size,1e-12))[:,None]
        cr=np.cross(proposal[tris[:,1]]-proposal[tris[:,0]],proposal[tris[:,2]]-proposal[tris[:,0]])
        ar=np.linalg.norm(cr,axis=1)/original_area
        cosine=np.sum(cr*original_cross,axis=1)/np.maximum(np.linalg.norm(cr,axis=1)*original_area,1e-30)
        bad=(ar<.75)|(ar>1.5)|(cosine<.995)
        if not bad.any():break
        affected=np.unique(tris[bad]);step[affected]*=.5
    assert not bad.any(), int(bad.sum())
    rest=proposal
    relaxation_checks.append({'iteration':iteration,'backtracks':backtrack,'min_area_ratio':float(ar.min()),'max_area_ratio':float(ar.max()),'min_normal_cosine':float(cosine.min())})
assert np.array_equal(rest[~mask],rest0[~mask])
for v,p in zip(m.vertices,rest):v.co=p
m.update()
# Read float32 coordinates back; all measurements use the actual Blender mesh.
rest=np.array([v.co[:] for v in m.vertices])
length=np.linalg.norm(rest[edges[:,1]]-rest[edges[:,0]],axis=1)
cross0=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
area0=np.linalg.norm(cross0,axis=1)

def apply(w):
    ids=list(range(len(rest)))
    for g in b.vertex_groups:g.remove(ids)
    for i,row in enumerate(w):
        for k,v in enumerate(row):
            if v>1e-10:b.vertex_groups[k].add([i],float(v),'REPLACE')
    m.update()

def measure(frames=[1,6,12,18,21,24]):
    records=[]
    for f in frames:
        sc.frame_set(f);bpy.context.view_layer.update()
        ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
        er=np.linalg.norm(p[edges[:,1]]-p[edges[:,0]],axis=1)/length
        cr=np.cross(p[tris[:,1]]-p[tris[:,0]],p[tris[:,2]]-p[tris[:,0]])
        ar=np.linalg.norm(cr,axis=1)/area0
        records.append({'frame':f,'edge_max':float(er.max()),'edge_min':float(er.min()),'edge_p99':float(np.quantile(er,.99)),
         'area_min':float(ar.min()),'area_max':float(ar.max()),'area_p01':float(np.quantile(ar,.01)),
         'edges_over_1_5':int((er>1.5).sum()),'area_below_0_6':int((ar<.6).sum()),'normal_dot_negative':int((np.sum(cr*cross0,axis=1)<0).sum())})
    return records

trials=[];best=None
def trial(label,w):
    global best
    assert np.all(np.isfinite(w)) and w.min()>=0 and np.max(abs(w.sum(axis=1)-1))<1e-6
    assert np.array_equal(w[w0[:,0]==1],w0[w0[:,0]==1])
    assert np.array_equal(w[np.max(w0,axis=1)==1],w0[np.max(w0,axis=1)==1])
    apply(w);r=measure()
    worst=max(v['edge_max'] for v in r);least=min(v['area_min'] for v in r)
    score=worst+1.2*(1-least)
    rec={'label':label,'score':score,'frames':r};trials.append(rec)
    print('TRIAL',label,'max_edge',round(worst,5),'min_area',round(least,5),'score',round(score,5),flush=True)
    if best is None or score<best[0]:best=(score,label,w.copy(),r)

trial('mesh_only_original_weights',w0)
for power in [1.1,1.25,1.5,1.75,2.0]:
    w=w0**power;w/=w.sum(axis=1)[:,None]
    trial('mesh_weight_power_'+str(power),w)
w=w0*w0*(3-2*w0);w/=w.sum(axis=1)[:,None]
trial('mesh_weight_smoothstep',w)

# Finite-element cotangent Laplacian reduces sensitivity to irregular triangles.
# Non-positive edge sums are clamped to a small positive value for a bounded solve.
graph_edges=np.unique(np.sort(np.concatenate([tris[:,[0,1]],tris[:,[1,2]],tris[:,[2,0]]]),axis=1),axis=0)
edge_map={tuple(e):i for i,e in enumerate(graph_edges.tolist())}
a,c=graph_edges.T
conductance=np.zeros(len(graph_edges))
for k in range(3):
    i,j,h=tris[:,k],tris[:,(k+1)%3],tris[:,(k+2)%3]
    u=rest[i]-rest[h];v=rest[j]-rest[h]
    cot=np.sum(u*v,axis=1)/np.maximum(np.linalg.norm(np.cross(u,v),axis=1),1e-12)
    idx=np.array([edge_map[tuple(sorted(e))] for e in zip(i.tolist(),j.tolist())])
    np.add.at(conductance,idx,.5*cot)
conductance=np.maximum(conductance,.0001)
boundary=np.max(w0,axis=1)==1;unknown=np.where(~boundary)[0]
deg=np.bincount(a,weights=conductance,minlength=len(rest))+np.bincount(c,weights=conductance,minlength=len(rest))
def lap(v):
    return deg*v-np.bincount(a,weights=conductance*v[c],minlength=len(rest))-np.bincount(c,weights=conductance*v[a],minlength=len(rest))
def mat(v):
    full=np.zeros(len(rest));full[unknown]=v
    return lap(full)[unknown]
wc=np.zeros_like(w0);wc[boundary]=w0[boundary];iterations=[]
for channel in [1,2]:
    rhs=-lap(wc[:,channel])[unknown]
    v=w0[unknown,channel].copy();r=rhs-mat(v);zp=r/deg[unknown];p=zp.copy();rz=np.dot(r,zp)
    for it in range(2500):
        ap=mat(p);alpha=rz/np.dot(p,ap);v+=alpha*p;r-=alpha*ap
        if max(abs(r))<1e-8:break
        zp=r/deg[unknown];nrz=np.dot(r,zp);p=zp+(nrz/rz)*p;rz=nrz
    wc[unknown,channel]=np.maximum(0,v);iterations.append(it+1)
wc[:,0]=np.maximum(0,1-wc[:,1]-wc[:,2]);wc/=wc.sum(axis=1)[:,None];wc[boundary]=w0[boundary]
for power in [1.,1.25,1.5,1.75,2.]:
    w=wc**power;w/=w.sum(axis=1)[:,None]
    trial('mesh_cotangent_power_'+str(power),w)

_,label,w,records=best
apply(w);sc.frame_set(1)
b['r7_mesh_edit']='Four tangential relaxation iterations within guarded hip patch; 0.004 displacement cap, original face area 0.75..1.5 and normal cosine >=0.995.'
b['r7_weights']=label
sc['stage']='R7_HIP_TRIAL_B';sc['candidate_status']='EXPERIMENT; pending independent sweep and visual review'
bpy.context.preferences.filepaths.save_version=0
target=ROOT/'verification/S_ZERO_R7_HIP_TRIAL_B.blend';assert not target.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
np.savez_compressed(ROOT/'evidence/R7_TRIAL_B_ARRAYS.npz',rest=rest,weights=w)
shift=np.linalg.norm(rest-rest0,axis=1)
report={'blender':bpy.app.version_string,'trials':trials,'selected':label,'selected_frames':records,
 'vertex_count':len(rest),'moved_vertices':int((shift>0).sum()),'max_displacement':float(shift.max()),
 'mean_moved_displacement':float(shift[shift>0].mean()),'permitted_vertex_count':int(mask.sum()),
 'protected_outside_patch_exact':bool(np.array_equal(rest[~mask],rest0[~mask])),
 'changed_weight_vertices':int(np.any(abs(w-w0)>1e-7,axis=1).sum()),'rig_pivots_angles_keyframes_unchanged':True,
 'rest_relaxation_guards':relaxation_checks,'cotangent_solve_iterations':iterations,'file':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R7_TRIAL_B_SAVED',label,'moved',report['moved_vertices'],'max',report['max_displacement'],flush=True)
