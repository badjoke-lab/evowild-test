"""Check local triangle orientation and degeneracy against protected source."""
import bpy,numpy as np,json
from pathlib import Path
p=Path('art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012')
bpy.ops.wm.open_mainfile(filepath=str(p/'S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
a=np.array([v.co[:] for v in o.data.vertices]);f=np.array([v.vertices[:] for v in o.data.polygons])
bpy.ops.wm.open_mainfile(filepath=str(p/'review-v1/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1.blend'))
o=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V1'];b=np.array([v.co[:] for v in o.data.vertices])
assert np.array_equal(f,np.array([v.vertices[:] for v in o.data.polygons]))
na=np.cross(a[f[:,1]]-a[f[:,0]],a[f[:,2]]-a[f[:,0]]);nb=np.cross(b[f[:,1]]-b[f[:,0]],b[f[:,2]]-b[f[:,0]])
la=np.linalg.norm(na,axis=1);lb=np.linalg.norm(nb,axis=1);valid=(la>1e-12)&(lb>1e-12)
r={'nondegenerate_faces_with_reversed_normal':int((np.sum(na[valid]*nb[valid],axis=1)<0).sum()),'source_degenerate_faces':int((la<=1e-12).sum()),'sculpt_degenerate_faces':int((lb<=1e-12).sum())}
print('FACE_QUALITY',r);(p/'review-v1/FACE_QUALITY.json').write_text(json.dumps(r,indent=2)+'\n')
assert r['nondegenerate_faces_with_reversed_normal']==0
assert r['sculpt_degenerate_faces']==r['source_degenerate_faces']
