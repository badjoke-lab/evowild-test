"""Crop real game frames for inspection and check the planted-foot transform."""
import gzip
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parents[2]
out=root/'public/race-integration/evidence'
captures, comparison=map(Path,sys.argv[1:3])
rows=json.loads((out/'quality-frames.json').read_text())
lab=root/'public/s-pixel-lab'
meta=json.loads((lab/'v3/assets/manifest.json').read_text())
geo=json.loads((lab/'v4.1/assets/index.json').read_text())
raw=gzip.decompress((lab/'v4.1/assets/geometry.gz').read_bytes())
vertices=np.frombuffer(raw[:geo['vertexBytes']],'<u2').reshape(-1,4)[:,:3]
coords=vertices/geo['quantization']*[meta['sx'],meta['height']/128,meta['sz']]+[meta['x0']-385,0,meta['z0']]
idx=np.frombuffer(raw[geo['vertexBytes']:],'<u4')
unit=.88*4.65/700
supports={}
for pose,levels in enumerate(geo['poses']):
    m=levels['fine']
    pts=coords[np.unique(idx[m['first']:m['first']+m['count']])]
    for foot in range(4):
        limb=pts[((pts[:,0]>=35)*2+(pts[:,2]<=0))==foot]
        # Choose the centroid of the lowest sole vertices in the fixed pose.
        supports[pose,foot]=limb[np.abs(limb[:,1]-limb[:,1].min())<.1].mean(axis=0)

def world(row,foot):
    a=row['actor'];x,y,z=supports[a['pose'],foot]
    weight=np.clip((y-54)/116,0,1)
    x+=a['fraction']*meta['stride']/24*(1-weight*weight*(3-2*weight))
    c,s=-np.cos(row['yaw']),np.sin(row['yaw'])
    return np.array(a['base'])+unit*np.array([c*x-s*z,y,s*x+c*z])

drift=[]; heights=[]
for old,new in zip(rows,rows[1:]):
    a,b=old['actor'],new['actor']
    if not a or not b or a['pose']!=b['pose']: continue
    for foot in range(4):
        if b['feet']&(1<<foot):
            one,two=world(old,foot),world(new,foot)
            drift.append(float(np.linalg.norm((two-one)[[0,2]])));heights.append(float(two[1]-.03))
summary={'frames':len(rows),'pose_count':len({r['actor']['pose'] for r in rows if r['actor']}),
         'lod':{},'contact_pairs_same_pose':len(drift),'sole_xz_drift_world_p95':float(np.percentile(drift,95)),
         'sole_xz_drift_world_max':max(drift),'sole_height_above_road_world_range':[min(heights),max(heights)],
         'world_body_length':unit*700}
for lod in ('sprite','transition','mid','race','fine'):
    arr=[r['actor']['span'] for r in rows if r['actor'] and r['actor']['lod']==lod and not r['pending']]
    summary['lod'][lod]={'count':len(arr),'span_px':[min(arr),max(arr)]}
(out/'quality.json').write_text(json.dumps(summary,indent=2)+'\n')

font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n): return ImageFont.truetype(font_path,n)
def plate(name,labels,images,cols,width,height,description):
    margin=10;nr=math.ceil(len(images)/cols)
    page=Image.new('RGB',(cols*width+2*margin,62+nr*(height+36)),(231,237,231))
    draw=ImageDraw.Draw(page);draw.rectangle((0,0,page.width,44),fill=(26,47,43))
    draw.text((margin,9),description,fill='white',font=font(18))
    for i,im in enumerate(images):
        x=margin+i%cols*width;y=55+i//cols*(height+36)
        im.thumbnail((width-8,height),Image.Resampling.LANCZOS)
        page.paste(im,(x,y));draw.text((x,y+height+3),labels[i],fill=(19,46,38),font=font(15))
    page.save(out/name,optimize=True)

labels=[];images=[]
for lod in ('sprite','transition','mid','race','fine'):
    choices=[(i,r) for i,r in enumerate(rows) if r['actor'] and r['actor']['lod']==lod and not r['pending']]
    i,r=choices[len(choices)//2]
    a=r['actor'];cx=(a['screen'][0]+1)*r['width']/2;cy=(1-a['screen'][1])*r['height']/2
    # 2x nearest-neighbour detail; identical zoom across panels, no scene changes.
    im=Image.open(captures/f'frame-{i}.png').convert('RGB')
    im=im.crop((int(cx)-120,int(cy)-150,int(cx)+120,int(cy)+150)).resize((480,600),Image.Resampling.NEAREST)
    images.append(im);labels.append(f"{lod} / {a['span']:.0f} px / pose {a['pose']}")
plate('lod-detail.png',labels,images,3,488,600,'Ridge Oval | Same runner, live game cameras | 2x nearest-neighbour crop')
labels=[];images=[]
for count,view in [(1,'follow'),(50,'race'),(100,'follow')]:
    for mode in ('classic','pixel'):
        images.append(Image.open(comparison/f's-{count}-{mode}-{view}.png').convert('RGB'))
        labels.append(f'{count} S   /   {view}   /   '+('v4.1' if mode=='pixel' else 'classic'))
plate('race-comparison.jpg',labels,images,2,516,307,'Matched simulation frames | Classic and S v4.1')
print(json.dumps(summary))
