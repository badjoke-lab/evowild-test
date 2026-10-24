import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert not bpy.data.is_dirty and not bpy.data.filepath, 'Preserve any unexpected open document first'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'protected/S_ZERO_R8C_RIG_PROTECTED.blend'),load_ui=False)
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];r=np.array([v.co[:] for v in b.data.vertices]);x,y,z=r.T
rows=[]
for a,c in [(1.25,1.4),(1.4,1.6),(1.6,1.8),(1.8,1.98)]:
 mask=(x>.4)&(x<1.25)&(z>a)&(z<c)&(y<-.23)
 rows.append({'z':[a,c],'count':int(mask.sum()),'bounds':[r[mask].min(axis=0).tolist(),r[mask].max(axis=0).tolist()],'outer_y_quantiles':np.quantile(abs(y[mask]),[.5,.75,.9,.99]).tolist()})
print(json.dumps({'file':bpy.data.filepath,'materials':[ma.name for ma in b.data.materials],'hip_samples':rows}))
