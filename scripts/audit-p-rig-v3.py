"""Compare actual v2/v3 runs, protected control code, anatomy and material alpha."""
import hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image
root=Path('docs/evidence/p-rig-v3-20261013')
old=Path('public/concept/p-layered')
new=Path('public/concept/p-layered-v3')
a=json.loads((old/'atlas.json').read_text()); b=json.loads((new/'atlas.json').read_text())
prior=(root/'v2-snapshot/p_layered.js').read_text(); current=Path('src/p_layered.js').read_text()
def digest(data): return hashlib.sha256(data).hexdigest()
def block(text,start,end): return text[text.index(start):text.index(end)]
control={}
for name,start,end in [
 ('gaitConstants','const TAU','const states'),
 ('laneConstraint','export function constrainPLayeredLane','function joint('),
 ('bodyJointAndIK','function joint(','function segment('),
 ('groundProjection','function laneForY','export function drawPLayered'),
 ('entirePoseAndContactPlanner','export function drawPLayered','  const drawBody=')]:
 oldblock,newblock=block(prior,start,end),block(current,start,end)
 control[name]={'unchanged':oldblock==newblock,'sha256':digest(newblock.encode())}
 assert oldblock==newblock, name
for key in ['bones','body','frame']:
 assert a[key]==b[key], key
for key in ['body','fore-foot','hind-foot']:
 assert a['parts'][key]==b['parts'][key],key
 assert (old/a['parts'][key]['image']).read_bytes()==(new/b['parts'][key]['image']).read_bytes(), key
protected={}
for path in subprocess.check_output(['git','ls-tree','-r','--name-only','eaf0d9f','public'],text=True).splitlines():
 original=subprocess.check_output(['git','show','eaf0d9f:'+path]); actual=Path(path).read_bytes()
 assert original==actual,path
 protected[path]=digest(actual)

def section_width(part,directory,length):
 alpha=np.array(Image.open(directory/part['image']).convert('RGBA'))[:,:,3]
 p,q=np.array(part['a']),np.array(part['b']); distance=np.linalg.norm(q-p)
 normal=np.array([-(q-p)[1],(q-p)[0]])/distance; mid=(p+q)/2; offsets=[]
 for offset in np.arange(-max(alpha.shape),max(alpha.shape),.5):
  x,y=np.rint(mid+normal*offset).astype(int)
  if 0<=y<alpha.shape[0] and 0<=x<alpha.shape[1] and alpha[y,x]>128: offsets.append(offset)
 return (max(offsets)-min(offsets)+.5)*length/distance
anatomy={kind:{version:{'boneLength':manifest['bones'][kind][1],'alphaMidsectionWidth':section_width(manifest['parts'][kind+'-lower'],directory,manifest['bones'][kind][1])} for version,manifest,directory in [('v2',a,old),('v3',b,new)]} for kind in ['fore','hind']}
(root/'control-and-asset-preservation.json').write_text(json.dumps({'baseline':'eaf0d9f4bba027f6b72eba49f48d00d5d9d61225','controlCode':control,'physicalCalibrationUnchanged':True,'protectedExistingPublicFiles':protected,'lowerLegMeasurements':anatomy},indent=2)+'\n')
comparisons=[]
for name in ['isolated-continuous','race-18-desktop','race-18-mobile']:
 before=json.loads((root/'before'/f'{name}-trace.json').read_text()); after=json.loads((root/f'{name}-trace.json').read_text())
 x,y=before['allRenderFrames'],after['allRenderFrames']
 assert len(x)==len(y),(name,len(x),len(y))
 differences=[]
 for i,(u,v) in enumerate(zip(x,y)):
  if u!=v: differences.append(i)
 assert not differences,(name,differences[:10])
 comparisons.append({'name':name,'allRenderFrames':len(x),'differentControlFrames':len(differences),'v2':before['summary'],'v3':after['summary']})
(root/'before-after-measurements.json').write_text(json.dumps(comparisons,indent=2)+'\n')
print(json.dumps({'preservedControlBlocks':len(control),'protectedPublicFiles':len(protected),'lowerLegs':anatomy,'frames':[{'name':c['name'],'frames':c['allRenderFrames'],'different':c['differentControlFrames']} for c in comparisons]},indent=2))
