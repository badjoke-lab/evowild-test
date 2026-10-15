import json,csv,math,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
root=Path('docs/evidence/p-rig-v5-20261015')
data=json.loads((root/'all-20-contact-validation.json').read_text())
with (root/'all-20-contact-summary.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['scene','version','foot','intervals','anchor_max_m','lane_anchor_max','sole_mean_px','sole_max_px','centroid_mean_px','centroid_max_px','vertical_residual_mean_px'])
 for case in data['results']:
  for v in case['versions']:
   for foot,m in v['byFoot'].items():w.writerow([case['name'],v['version'],foot,m['soles']['n'],m['anchors']['max'],m['lanes']['max'],m['soles']['mean'],m['soles']['max'],m['centroids']['mean'],m['centroids']['max'],m['verticalResiduals']['mean']])
poses=json.loads((root/'phase-poses.json').read_text());rows=[]
for p in poses:
 s=p['spine']['shoulder'];h=p['spine']['hip'];off=p['bodyOffset']
 rows.append({'phase':p['phase'],'shoulderX':s['x'],'shoulderY':s['y']+off,'hipX':h['x'],'hipY':h['y']+off,'shoulderHeight':296-s['y']-off,'hipHeight':296-h['y']-off,'torsoLength':math.hypot(s['x']-h['x'],s['y']-h['y']),'shoulderAboveHip':h['y']-s['y'],'chestAngle':p['spine']['chestAngle'],'pelvisAngle':p['spine']['pelvisAngle'],'loadBob':p['bob'],'reachCorrection':off,'flight':p['flight']})
with (root/'spine-phase-measurements.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
old={'shoulder':[50+755*316/1121,60+340*316/1121],'hip':[50+418*316/1121,60+364*316/1121]}
new={'shoulder':[250,146],'hip':[179,164]}
for v in [old,new]:
 v['torsoLength']=math.dist(v['shoulder'],v['hip']);v['shoulderHeight']=296-v['shoulder'][1];v['hipHeight']=296-v['hip'][1];v['foreBones']=[70,68];v['hindBones']=[70,68]
(root/'structure-comparison.json').write_text(json.dumps({'units':'416x320 rig pixels; neutral anatomical attachment points before load correction','v4':old,'v5':new,'v5Phases':rows},indent=2)+'\n')
sheet=Image.open(root/'layered-contact-sheet.png').convert('RGB');d=ImageDraw.Draw(sheet)
for i,r in enumerate(rows):
 x=i%4*416;y=i//4*360;s=(x+r['shoulderX'],y+r['shoulderY']);h=(x+r['hipX'],y+r['hipY']);d.line([h,s],fill='#00ccee',width=3)
 for pt in [s,h]:d.ellipse((pt[0]-4,pt[1]-4,pt[0]+4,pt[1]+4),fill='#ffff22')
 d.text((x+10,y+305),f"S-H height {r['shoulderAboveHip']:.1f} / length {r['torsoLength']:.1f}",fill='#152d3d')
sheet.save(root/'spine-phase-comparison.png')
# Zoom actual rendered chest, shoulder and pelvis, preserving pixels.
comp=Image.open(root/'canonical-old-new.png');comp.crop((0,90,2080,400)).resize((2080,620)).save(root/'fullbody-enlarged-comparison.png')
baseline=json.loads((root/'v4-baseline.json').read_text());mismatches=[]
for name,digest in baseline['sha256'].items():
 if name=='src/p_layered.js':continue
 if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:mismatches.append(name)
assert not mismatches,mismatches
(root/'protected-assets-validation.json').write_text(json.dumps({'baseline':baseline['fetchedHead'],'verifiedFiles':len(baseline['sha256'])-1,'mismatches':mismatches},indent=2)+'\n')
