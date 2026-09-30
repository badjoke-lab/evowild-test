"""Rebuild the anterior thorax as a Dirichlet surface patch, preserving X/topology.

Reads v11. Neck and forelimb/scapular surface collars are immutable boundaries.
The patch interior is reconstructed from its boundary, rather than adding another
small displacement to the previous wrinkles. No remeshing or modifiers are used.
"""
import bpy, json, os, hashlib
import numpy as np
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
source=bpy.data.collections['S_EDITABLE_SOURCE']
body=next(o for o in bpy.data.collections['S_MODEL'].objects if o.type=='MESH')
me=body.data
orig=np.array([v.co[:] for v in me.vertices],dtype=np.float64)
edges=np.array([e.vertices[:] for e in me.edges],dtype=np.int64)
polygons=[tuple(p.vertices) for p in me.polygons]
other={o.name:[v.co.copy() for v in o.data.vertices] for o in bpy.data.objects if o.type=='MESH' and o!=body}
dg=bpy.context.evaluated_depsgraph_get()
def bvhs(prefixes):
 result=[]
 for o in source.objects:
  if o.type!='MESH' or not o.name.startswith(prefixes):continue
  eo=o.evaluated_get(dg);m=eo.to_mesh()
  try:result.append(BVHTree.FromPolygons([eo.matrix_world@v.co for v in m.vertices],[tuple(p.vertices) for p in m.polygons]))
  finally:eo.to_mesh_clear()
 assert result
 return result
root_bvhs=bvhs(('Forelimb','Scapular_keel'))
neck_bvhs=bvhs(('Neck_integrated_keel',))
mask=(np.abs(orig[:,0])<.32)&(orig[:,1]>-1.13)&(orig[:,1]<-.20)&(orig[:,2]>1.70)&(orig[:,2]<2.32)
protected=[]
for i in np.flatnonzero(mask):
 pw=body.matrix_world@me.vertices[int(i)].co
 dr=min(b.find_nearest(pw)[3] for b in root_bvhs)
 dn=min(b.find_nearest(pw)[3] for b in neck_bvhs)
 if dr<=.065 or (dn<=.045 and (orig[i,2]>=2.24 or orig[i,1]<=-1.04)):
  mask[i]=False;protected.append(int(i))
active=np.flatnonzero(mask)
assert len(active)>0
idx=np.full(len(orig),-1,dtype=np.int64);idx[active]=np.arange(len(active))
directed=np.concatenate((edges,edges[:,::-1]));directed=directed[mask[directed[:,0]]]
i=idx[directed[:,0]];j=idx[directed[:,1]]
degree=np.bincount(i,minlength=len(active)).astype(np.float64)
inside=j>=0
rows=i[inside];cols=j[inside]
rhs=np.zeros((len(active),2))
np.add.at(rhs,i[~inside],orig[directed[~inside,1],1:])
def matvec(q):return degree*q-np.bincount(rows,weights=q[cols],minlength=len(active))
def solve(b,x):
 x=x.copy();r=b-matvec(x);z=r/degree;p=z.copy();rz=np.dot(r,z)
 for iteration in range(3000):
  ap=matvec(p);den=np.dot(p,ap)
  if den<=0:raise RuntimeError('Nonpositive patch operator')
  alpha=rz/den;x+=alpha*p;r-=alpha*ap
  if np.max(np.abs(r))<1e-10:return x,iteration+1,float(np.max(np.abs(r)))
  z=r/degree;next_rz=np.dot(r,z);p=z+(next_rz/rz)*p;rz=next_rz
 raise RuntimeError('Patch solve failed to converge')
new=orig.copy();iterations=[];residuals=[]
for axis in (1,2):
 new[active,axis],it,res=solve(rhs[:,axis-1],orig[active,axis]);iterations.append(it);residuals.append(res)
for vi in active:me.vertices[int(vi)].co=(orig[vi,0],new[vi,1],new[vi,2])
me.update()
actual=np.array([v.co[:] for v in me.vertices])
delta=np.linalg.norm(actual-orig,axis=1)
assert np.array_equal(actual[:,0],orig[:,0]),'X changed'
assert np.array_equal(actual[~mask],orig[~mask]),'Scope escaped'
assert len(me.vertices)==len(orig) and [tuple(p.vertices) for p in me.polygons]==polygons
assert np.array_equal(np.array([e.vertices[:] for e in me.edges]),edges)
for name,coords in other.items():
 assert all(v.co==p for v,p in zip(bpy.data.objects[name].data.vertices,coords)),name+' changed'
assert np.isfinite(actual).all() and delta.max()<.20
report=dict(input='S-blockout-v11.blend',output='S-blockout-v12.blend',method='Dirichlet harmonic reconstruction of anterior thorax Y/Z from fixed boundary',active_vertices=len(active),changed_vertices=int((delta>0).sum()),total_vertices=len(orig),max_displacement=float(delta.max()),solver_iterations=iterations,solver_residuals=residuals,target_bounds=dict(abs_x_lt=.32,y=[-1.13,-.20],z=[1.70,2.32]),protected_surface_collars=dict(forelimb_scapular=.065,neck=.045,neck_collar_application='z >= 2.24 or y <= -1.04; chest-side junction rebuilt with X fixed'),all_non_active_vertices_position_unchanged=True,lateral_x_unchanged=True,topology_unchanged=True,vertex_count_unchanged=True,other_meshes_unchanged=True,neck_width_reduction_preserved=True,forelimb_and_scapular_roots_protected=True,coordinate_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),accepted=False)
body.name='S_organism_blockout_v12'
bpy.context.scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-blockout-v12.blend'),compress=True)
with open(os.path.join(OUT,'thorax-v12-validation.json'),'w') as f:json.dump(report,f,indent=2)
hp=os.path.join(ROOT,'HANDOFF_STATE.json')
if os.path.exists(hp):
 state=json.load(open(hp));state.update(stage='S-blockout-v12',current_stage='v12 anterior thorax locally rebuilt; review pending',current_model_file='output/S-blockout-v12.blend',next_action='Review v12 front/front34/side against reference 01. No other regions authorized.',blockers=[],accepted=False)
 with open(hp,'w') as f:json.dump(state,f,ensure_ascii=False,indent=2)
cp=os.path.join(ROOT,'CHECKPOINT.md')
if os.path.exists(cp):
 s=open(cp).read();ls=[]
 for line in s.splitlines():
  if line.startswith('current_stage:'):line='current_stage: v12 anterior thorax locally rebuilt; review pending'
  elif line.startswith('current_model_file:'):line='current_model_file: output/S-blockout-v12.blend'
  elif line.startswith('next_action:'):line='next_action: Review v12 chest transition only; no other regions authorized.'
  ls.append(line)
 with open(cp,'w') as f:f.write('\n'.join(ls)+'\n\nreview_status_v12: local thorax reconstruction; visual review pending\n- Reconstructed anterior thorax from fixed boundary; all X, neck, forelimb roots, scapular outer ridge, topology and vertex count preserved.\n')
print('S_V12',json.dumps(report))
