#!/usr/bin/env python3
"""Independent analytic intersection, source-integrity and gait sampling checks."""
from pathlib import Path
import importlib.util,json,hashlib,numpy as np
spec=importlib.util.spec_from_file_location('slices','scripts/stacking-slices.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
# Analytic unit cube tests catch wrong horizontal axis, holes and outside alpha.
v=np.array([[x,y,z] for x,y,z in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]],dtype=float)
s.IND=np.array([[0,1,2],[0,2,3],[4,6,5],[4,7,6],[0,4,5],[0,5,1],[3,2,6],[3,6,7],[0,3,7],[0,7,4],[1,5,6],[1,6,2]]);s.PPU=16
n=np.tile([0.,1.,0.],(8,1));img,origin,odd=s.cross(v,n,.5);assert odd==0;assert int((img[:,:,3]>0).sum())==256;assert img[0,0,3]==0;assert img[:,:,3].max()==255;assert s.cross(v,n,1.1)[0][:,:,3].sum()==0
A=Path('public/exp-sprite-stacking/assets');m=json.loads((A/'manifest.json').read_text());assert hashlib.sha256((A/'source.glb').read_bytes()).hexdigest()==m['sourceSha256'];assert hashlib.sha256((A/'reference.png').read_bytes()).hexdigest()==m['referenceSha256'];assert len(m['atlases'])==192
samples=json.loads((A/'motion-samples.json').read_text());assert len(samples)==48
feet=[]
for i in range(4):
 rows=[r['soles'][i] for r in samples];lo=min(r['minY'] for r in rows);hi=max(r['minY'] for r in rows);assert hi-lo>.3,'Four legs must articulate, not only torso bob';feet.append({'name':rows[0]['name'],'minSourceY':lo,'recoveryHeight':hi,'excursion':hi-lo})
quant=[]
for frames in [12,24,48]:
 slip=[]
 for foot in range(4):
  total=maxStep=0.;supportPairs=0;previous=None
  for j in range(241):
   phase=j/240;f=(int((phase%1)*frames)%frames)*(48//frames);sole=samples[f]['soles'][foot];points=np.array(sole['points']);points[:,2]+=m['stride']*phase
   if previous is not None and sole['minY']<.001 and previous[0]<.001:
    step=np.linalg.norm((points-previous[1])[:,[0,2]],axis=1).mean();total+=step;maxStep=max(maxStep,float(step));supportPairs+=1
   previous=(sole['minY'],points)
  slip.append({'foot':foot,'accumulatedSoleDisplacement':float(total),'maxStepDisplacement':maxStep,'supportPairs':supportPairs})
 quant.append({'frames':frames,'steps':240,'period':m['period'],'note':'Discrete source poses with continuous root travel. Real sole points, 1mm source plane band. Includes sample-hold drift and pose jumps; not IK anchor slip.','feet':slip})
result={'checks':['analytic 1m cube cross-section 256 opaque pixels','outside-plane empty','outside-solid alpha zero','source and reference immutable SHA256','192 atlas configurations','all four independent limbs >30cm recovery'],'feet':feet,'quantizedMotion':quant,'planeCenterGroundGapMeters':{str(n):m['height']/n/2 for n in [16,32,64,128]},'oddScanlinesTotal':sum(a['oddScanlines'] for a in m['atlases']),'material':m['materialNote']}
Path('public/exp-sprite-stacking/evidence/pipeline-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS analytic cross sections, immutable sources and all four actual soles')
