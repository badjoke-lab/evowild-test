"""Summarize actual browser bone/mesh traces; no force or COM inference."""
import gzip,json,math
from pathlib import Path
p=Path('docs/2p5d/evidence/20261028-s-body-d2b')
def pitch(q):
 x,y,z,w=q;return math.degrees(math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)))
def body(frame):
 out={}
 for b in frame['body']:
  xyz=b['position'][:];xyz[2]-=frame['distance'];out[b['name']]={'relativePosition':xyz,'pitchDegrees':pitch(b['quaternion'])}
 pelvis=out['pelvis']['relativePosition'];chest=out['chest']['relativePosition'];out['trunkPitch']=math.degrees(math.atan2(chest[1]-pelvis[1],chest[2]-pelvis[2]));return out
reports=[]
for f in sorted(p.glob('*-trace.json.gz')):
 trace=json.loads(gzip.decompress(f.read_bytes()));frames=trace['frames'];rows=[body(x) for x in frames];ranges={}
 for name in ['pelvis','spine','chest','neck','head','tail']:
  ranges[name]={'relativePositionRange':[[min(r[name]['relativePosition'][i] for r in rows),max(r[name]['relativePosition'][i] for r in rows)] for i in range(3)],'pitchRange':[min(r[name]['pitchDegrees'] for r in rows),max(r[name]['pitchDegrees'] for r in rows)]}
 contacts=[]
 for foot in [2,3]:
  start=None
  for i,frame in enumerate(frames):
   l=frame['contact']['limbs'][foot];planted=l['stage'] in ['CONTACT','PUSH']
   if planted and start is None:start=i
   if not planted and start is not None:
    if start>0:
     before=rows[start];after=rows[i-1];contacts.append({'foot':l['name'],'startTime':frames[start]['t'],'liftTime':frame['t'],'pelvisDeltaRelative':[after['pelvis']['relativePosition'][j]-before['pelvis']['relativePosition'][j] for j in range(3)],'trunkPitchStart':before['trunkPitch'],'trunkPitchEnd':after['trunkPitch'],'kneeAngleStart':frames[start]['contact']['limbs'][foot]['jointAngles'][0],'kneeAngleEnd':frames[i-1]['contact']['limbs'][foot]['jointAngles'][0]})
    start=None
 reports.append({'trace':f.name,'samples':len(frames),'ranges':ranges,'completeHindSupportIntervals':contacts})
p.joinpath('body-summary.json').write_text(json.dumps(reports,indent=2)+'\n')
for r in reports:
 if 'steady-1-trace' in r['trace']:print(r['trace'],json.dumps(r['completeHindSupportIntervals']))
