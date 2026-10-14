"""Edit-mode adjacent-surface relaxation at the plate/chest/arm transitions."""
import bpy, bmesh, numpy as np, json
from pathlib import Path
OUT = Path(bpy.data.filepath).resolve().parent
body = bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
mesh = body.data
before = np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
base = np.load(OUT/'V3_BASE_COORDS.npy')
faces = np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
x,y,z = before.T
def ease(a,b,v):
    t=np.clip((v-a)/(b-a),0,1)
    return t*t*(3-2*t)
w=(ease(-.57,-.49,y)*(1-ease(-.16,-.075,y))*ease(-.38,-.31,z)*(1-ease(.10,.17,z))*ease(.04,.09,np.abs(x+.03588832542300224)))
edges = np.array([e.vertices[:] for e in mesh.edges],dtype=int)
src = np.r_[edges[:,0],edges[:,1]]
dst = np.r_[edges[:,1],edges[:,0]]
degree = np.bincount(src,minlength=len(before))
points=before.copy()
# Taubin's neighboring-vertex relaxation avoids volume loss from repeated
# one-way smoothing. The only support is the local shoulder/chest surface.
for _ in range(12):
    for factor in (.45,-.47):
        avg=np.zeros_like(points)
        np.add.at(avg,src,points[dst])
        avg/=np.maximum(degree,1)[:,None]
        points+=(avg-points)*(factor*w)[:,None]
def normals(p):
    n=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]])
    return n,np.linalg.norm(n,axis=1)
nb,ab=normals(base)
n0,a0=normals(before)
valid=(ab>1e-12)&(a0>1e-12)
factor=1.
for _ in range(16):
    proposal=(before+(points-before)*factor).astype(np.float32).astype(np.float64)
    n,a=normals(proposal)
    if not np.any(valid&((np.sum(nb*n,axis=1)<=0)|(np.sum(n0*n,axis=1)<=0)|(a<ab*.25)|(a<a0*.25))):
        break
    factor*=.8
else:
    raise RuntimeError('Transition relaxation failed orientation gate')
changed=np.any(proposal!=before,axis=1)
np.save(OUT/'relax_BEFORE.npy',before)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT')
bm=bmesh.from_edit_mesh(mesh)
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v.select_set(bool(changed[v.index]))
    if changed[v.index]:v.co=proposal[v.index]
bmesh.update_edit_mesh(mesh,loop_triangles=True,destructive=False)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.update()
np.save(OUT/'relax_AFTER.npy',proposal)
report=dict(stage='transition_relax',mode='EDIT',method='12 paired neighboring-vertex Taubin relaxation passes, local feathered ROI',gaussian=False,changed_vertices=int(changed.sum()),max_move=float(np.linalg.norm(proposal-before,axis=1).max()),factor=factor,new_flipped_faces=0,new_degenerate_faces=0)
(OUT/'relax_EDIT_LOG.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
