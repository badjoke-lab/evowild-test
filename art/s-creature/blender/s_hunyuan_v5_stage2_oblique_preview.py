"""One bounded, reversible Edit Mode proposal, starting at accepted Stage 1."""
import bpy, bmesh, numpy as np, json
from pathlib import Path
from collections import deque

out=Path(bpy.data.filepath).parent
assert Path(bpy.data.filepath).name=='S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend'
body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.data.name=='geometry_0')
mesh=body.data
x=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
assert np.array_equal(x,np.load(out/'STAGE1_EXPECTED_COORDS.npy'))
faces=np.array([p.vertices[:] for p in mesh.polygons])
neighbors=[set() for _ in x]
for e in mesh.edges:
 a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
delta=np.zeros_like(x)
patches=[]
# Lower the rear part of the upper contour, along the existing surface rather
# than projecting a plate. A second small inset clarifies lower chest/arm.
for side in (1,-1):
 for kind,point,rings,move in [
  ('upper_oblique',(.147,-.278,.091),7,(0,.003,-.007)),
  ('pectoral_inset',(.112,-.407,-.065),6,(-.003,0,0))]:
  p=np.array(point);p[0]=-.0355+side*(p[0]+.0355)
  seed=int(np.argmin(np.linalg.norm(x-p,axis=1)))
  dist={seed:0};q=deque([seed])
  while q:
   i=q.popleft()
   if dist[i]>=rings:continue
   for j in neighbors[i]:
    if j not in dist:dist[j]=dist[i]+1;q.append(j)
  ids=[]
  for i,d in dist.items():
   if not (-.48<x[i,1]<-.20 and -.15<x[i,2]<.15):continue
   t=1-d/rings;w=t*t*(3-2*t)
   v=np.array(move);v[0]*=side
   delta[i]+=w*v;ids.append(i)
  patches.append({'kind':kind,'side':side,'seed':seed,'seed_position':x[seed].tolist(),'rings':rings,'vertices':ids})
expected=x+delta
def geom(v):
 v=v.astype(np.float64);n=np.cross(v[faces[:,1]]-v[faces[:,0]],v[faces[:,2]]-v[faces[:,0]])
 return n,np.linalg.norm(n,axis=1)
n0,a0=geom(x);n1,a1=geom(expected)
v3=np.load(out.parent/'review-v4/V3_BASE_COORDS.npy');_,a3=geom(v3)
valid=(a0>1e-12)&(a1>1e-12)
flips=int(np.count_nonzero(np.sum(n0[valid]*n1[valid],axis=1)<=0))
degens=int(np.count_nonzero((a0>1e-12)&(a1<=1e-12)))
ratio=a1[a3>1e-12]/a3[a3>1e-12]
if flips or degens or ratio.min()<.3229:
 report={'status':'REJECTED_BEFORE_MESH_MUTATION','changed_vertices_proposed':int(np.count_nonzero(np.any(expected!=x,axis=1))),'new_reversed_faces':flips,'new_degenerate_faces':degens,'minimum_v3_area_ratio':float(ratio.min()),'maximum_move_proposed':float(np.linalg.norm(expected-x,axis=1).max()),'mesh_unchanged':True,'decision':'REVISE_HALT_STAGE2','patches':patches}
 (out/'STAGE2_REJECTED_PREFLIGHT.json').write_text(json.dumps(report,indent=2))
 np.savez_compressed(out/'STAGE2_REJECTED_PROPOSAL.npz',indices=np.where(np.any(expected!=x,axis=1))[0],coordinates=expected[np.any(expected!=x,axis=1)])
assert flips==degens==0,(flips,degens)
assert ratio.min()>=.3229,float(ratio.min())
changed=np.where(np.any(expected!=x,axis=1))[0]
backup=out/'STAGE2_BEFORE.npy';assert not backup.exists()
np.save(backup,x)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(mesh);bm.verts.ensure_lookup_table()
for i in changed:bm.verts[int(i)].co=expected[i]
bmesh.update_edit_mesh(mesh,loop_triangles=True,destructive=False)
bpy.ops.object.mode_set(mode='OBJECT')
actual=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
assert np.array_equal(actual,expected)
np.save(out/'STAGE2_PROPOSED_COORDS.npy',actual)
report={'status':'UNSAVED_PENDING_VISUAL','changed_vertices':len(changed),'maximum_move':float(np.linalg.norm(actual-x,axis=1).max()),'minimum_v3_area_ratio':float(ratio.min()),'new_reversed':flips,'new_degenerate':degens,'patches':patches}
(out/'STAGE2_OBLIQUE_PROPOSAL.json').write_text(json.dumps(report,indent=2))
print({k:v for k,v in report.items() if k!='patches'})
