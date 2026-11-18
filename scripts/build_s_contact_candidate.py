"""B2: immutable v2 geometry/rest rig, distal sole weights for contact IK.
Animation is applied by isolated src/s_contact_ik.js, NOT a production clip.
"""
import hashlib,json,struct
from pathlib import Path
import numpy as np
from inspect_s_glb_skin import read_glb,accessor
source=Path('public/models/evowild-s/review/focus-hind-fit-v2.glb')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='efa804ea4c3e2a2d272918e6982da12a365f1759140f50fa6d3f586c5fd2bede'
d,b=read_glb(source);a=d['meshes'][0]['primitives'][0]['attributes'];p=accessor(d,b,a['POSITION']);j=accessor(d,b,a['JOINTS_0']);w=accessor(d,b,a['WEIGHTS_0']);oldj=j.copy();oldw=w.copy();names=[d['nodes'][i]['name'] for i in d['skins'][0]['joints']];changed=[]
for prefix in ['fore_L','fore_R','hind_L','hind_R']:
 bone=names.index(prefix+('_toe' if prefix.startswith('hind') else '_foot'))
 mask=(p[:,1]<-.70)&((p[:,0]<-.01945) if prefix.endswith('L') else (p[:,0]>-.01945))&((p[:,2]>.1) if prefix.startswith('fore') else (p[:,2]<-.6))
 for i in np.flatnonzero(mask):
  blend=float(np.clip((-.70-p[i,1])/.08,0,1));weights={int(k):float(v)*(1-blend) for k,v in zip(oldj[i],oldw[i])};weights[bone]=weights.get(bone,0)+blend
  top=sorted(weights.items(),key=lambda kv:kv[1],reverse=True)[:4];top+= [(0,0)]*(4-len(top));total=sum(v for _,v in top);j[i]=[k for k,_ in top];w[i]=[v/total for _,v in top]
 changed.extend(np.flatnonzero(mask).tolist())
d.setdefault('extras',{})['sContactCandidate']={'status':'REVISE','runtimeController':'src/s_contact_ik.js','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'groundY':0,'geometryAndRestRigUnchanged':True}
encoded=json.dumps(d,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
out=Path('public/models/evowild-s/review/focus-contact-v3.glb');out.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(b))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(b),0x004e4942)+b)
report={'source':str(source),'candidate':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changedWeightVertices':len(set(changed)),'positionNormalIndexAndRestRigUnchanged':True,'controller':'src/s_contact_ik.js','status':'REVISE'}
reportpath=Path('docs/2p5d/evidence/20261026-s-contact-b2/asset-report.json');reportpath.parent.mkdir(parents=True,exist_ok=True);reportpath.write_text(json.dumps(report,indent=2)+'\n');print(report)
