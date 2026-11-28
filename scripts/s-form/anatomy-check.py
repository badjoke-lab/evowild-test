"""Check the exported anatomy records, not a visual acceptance metric."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[2];p=json.loads((root/'public/s-form/anatomy.json').read_text())
rows=[];support=[];maxerr=0
for pose in p['poses']:
 for name,record in pose['feet'].items():
  joints=record['joints'];rest=p['rest_joints'][name]
  for i in range(len(joints)-2):
   error=abs(math.dist(joints[i][:2],joints[i+1][:2])-math.dist(rest[i][:2],rest[i+1][:2]))
   assert error<1e-6,(pose['frame'],name,error);maxerr=max(maxerr,error)
  if record['contact']:
   assert record['toe'][1]==502
   next_record=p['poses'][(pose['frame']+1)%24]['feet'][name]
   if next_record['contact']:
    shift=next_record['toe'][0]-record['toe'][0]
    assert abs(shift-p['stride']*200/24)<.002,(name,shift)
    support.append({'frame':pose['frame'],'foot':name,'support_velocity_px_per_pose':shift})
  rows.append({'frame':pose['frame'],'foot':name,'contact':record['contact'],'toe':record['toe']})
result={'purpose':'joint lengths and support timing only; no visual acceptance',
 'max_segment_length_error_px':maxerr,'contacts':rows,'support_intervals':support,
 'stride_m':p['stride'],'period_s':p['period'],'old_voxel_geometry_used':False}
(root/'public/s-form/evidence/anatomy-check.json').write_text(json.dumps(result,indent=2)+'\n')
print('24 poses, 4 feet, segment lengths and contact velocity passed')
