"""Compare the same integrated game states and publish the unaggregated measurements."""
import csv
import json
import math
import sys
import zipfile
from pathlib import Path
from statistics import mean

import numpy as np
from PIL import Image, ImageDraw, ImageFont

work, out = map(Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
ids = [f'{screen}-{count}-{look}-{camera}' for screen in ('pc','phone')
       for count in (18,50,100) for look in ('classic','pixel') for camera in ('race','follow')]

def load(folder, key):
    return json.loads((work/folder/(key+'.json')).read_text())

def write_csv(file, rows):
    with (out/file).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0]); writer.writeheader();writer.writerows(rows)

def image(kind, folder, stem):
    with Image.open(work/folder/kind/(stem+'.png')) as source:
        return np.array(source.convert('RGB'),dtype=np.int16)

def p95(values):
    return sorted(values)[math.ceil(len(values)*.95)-1]

def state(row):
    return {k:v for k,v in row.items() if k not in ('interval_ms','lod','streaming','atlas_errors')}

timing=[]; costs=[]; quality=[]; summary=[]; tails=[]
with zipfile.ZipFile(out/'raw.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as raw:
    for key in ids:
        screen,count,look,camera=key.split('-')
        before,after=[load('accept-'+v,key) for v in ('before','after')]
        probes=[load('measured-'+v,key) for v in ('before','after')]
        assert before['raster']==after['raster'] and before['antialias']==after['antialias']
        assert all(state(a)==state(b) and a['lod']==b['lod'] for a,b in zip(before['samples'],after['samples']))
        for version,trial,rows in zip(('before','after'),(before,after),probes):
            assert len(rows)==7 and len(trial['samples'])==96
            peer=load('accept-'+version,key.replace('-'+look+'-','-'+('classic' if look=='pixel' else 'pixel')+'-'))
            assert all(state(a)==state(b) for a,b in zip(trial['samples'],peer['samples']))
            for group in ('accept','measured'):
                raw.write(work/(group+'-'+version)/(key+'.json'),group+'-'+version+'/'+key+'.json')
            frame=[s['interval_ms'] for s in trial['samples']]
            stats=dict(id=key,build=version,screen=screen,count=count,look=look,camera=camera)
            rate=1000/mean(frame)
            timing.append(dict(**stats,width=trial['raster'][0],height=trial['raster'][1],aa=trial['antialias'],
                               samples=len(frame),mean_ms=round(mean(frame),2),fps=round(rate,2),p95_ms=round(p95(frame),2),
                               streaming_frames=sum(s['streaming'] for s in trial['samples']),pass_both=rate>=30 and p95(frame)<=33.3))
            for i,t in enumerate(frame):
                if t>=p95(frame):
                    a=trial['samples'][i]
                    tails.append(dict(**stats,frame=i+25,interval_ms=round(t,2),rank=a['rank'],streaming=a['streaming'],
                                      **{k:(a['lod'] or {}).get(k,'') for k in ('fine','race','mid','transition','sprite','outside')}))
            def avg(bucket,field):
                return round(mean(r[bucket].get(field,0) for r in rows),3)
            native=['ground','course','sceneOther','otherMorph','classicS']
            cpu=lambda k: avg('cpu',k)
            gpu=lambda k: avg('gpu',k)
            costs.append(dict(**stats,states=len(rows),cpu_simulation_and_rank_ms=round(cpu('simulation')-cpu('classicSPose'),3),
                cpu_s_rig_ms=cpu('classicSPose'),cpu_s_travel_ms=cpu('sTravel'),cpu_s_pose_lod_ms=cpu('sLod'),cpu_camera_ms=cpu('camera'),
                cpu_submit_three_setup_ms=round(cpu('three')-sum(map(cpu,native)),3),
                **{'cpu_submit_'+k+'_ms':cpu(k) for k in native+['pixelMesh','sprite']},
                cpu_pixel_other_ms=round(cpu('pixel')-cpu('pixelMesh')-cpu('sprite')-cpu('sLod'),3),cpu_ui_ms=cpu('ui'),
                cpu_gpu_sync_read_ms=cpu('wait'),**{'gpu_'+k+'_ms':gpu(k) for k in ['clearAndSetup',*native,'pixelMesh','sprite']},
                **{'draws_'+k:avg('calls',k) for k in [*native,'pixelMesh','sprite']},
                s_triangles=avg('triangles','pixelMesh'),sprite_triangles=avg('triangles','sprite')))
        same=0;worst=0;total=actor_changes=color_changes=0;loss=0
        for a,b in zip(*probes):
            for k in ('frame','aa','size','state_sha','actors_sha','lod','pixel_ids','nativeVisible','streaming'):
                assert a[k]==b[k],(key,a['frame'],k)
            assert not a['streaming']
            stem=key+'-'+str(a['frame']); metrics={}
            for kind in ('frames','actors'):
                x=image(kind,'measured-before',stem);y=image(kind,'measured-after',stem)
                delta=np.abs(x-y);d=delta.max(2);maxdelta=int(d.max())
                metrics.update({kind+'_changed_px':int(np.count_nonzero(d)),kind+'_max_channel_delta':maxdelta,kind+'_mae':round(float(delta.mean()),6)})
                if kind=='actors':
                    mask_diff=np.any(x!=0,axis=2)^np.any(y!=0,axis=2)
                    loss+=int(mask_diff.sum());metrics['actor_mask_changed_px']=int(mask_diff.sum());actor_changes+=int(np.count_nonzero(d));same+=int(maxdelta==0)
                else:
                    worst=max(worst,maxdelta);total+=d.size;color_changes+=int(np.count_nonzero(d))
            quality.append(dict(id=key,frame=a['frame'],visible_runners=len(set(a['nativeVisible'])|set(a['pixel_ids'])),
                        s_triangles_before=a['triangles'].get('pixelMesh',0),s_triangles_after=b['triangles'].get('pixelMesh',0),**metrics))
        summary.append(dict(id=key,state_pairs=7,actor_identical=same,actor_changed=actor_changes,mask_changed=loss,
                            max_channel=worst,total_pixels=total,changed_rgb_pixels=color_changes))
write_csv('performance.csv',timing);write_csv('cpu-gpu.csv',costs);write_csv('quality.csv',quality);write_csv('tails.csv',tails)
(out/'checks.json').write_text(json.dumps(summary,indent=1)+'\n')

# Full-raster paired screenshots and a lossless nearest-neighbour crop of the pack.
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
def plate(name, entries, crop=None):
    cols=2; tiles=[]
    for label,folder,stem in entries:
        im=Image.open(work/('measured-'+folder)/'frames'/(stem+'.png')).convert('RGB')
        if crop: im=im.crop(crop).resize(((crop[2]-crop[0])*2,(crop[3]-crop[1])*2),Image.Resampling.NEAREST)
        tiles.append((label,im))
    w,h=tiles[0][1].size
    dest=Image.new('RGB',(cols*w,(len(tiles)//cols)*(h+36)),(20,32,39));draw=ImageDraw.Draw(dest)
    for i,(label,im) in enumerate(tiles):
        x=i%cols*w;y=i//cols*(h+36);draw.text((x+10,y+5),label,font=font,fill='white');dest.paste(im,(x,y+36))
    dest.save(out/name)
plate('race-pc.png',[(f'{v.title()}  /  {look}  /  100 S  /  Race',v,'pc-100-'+look+'-race-73')
                     for look in ('classic','pixel') for v in ('before','after')])
plate('follow-phone.png',[(f'{v.title()}  /  {look}  /  18 mixed  /  Follow',v,'phone-18-'+look+'-follow-89')
                          for look in ('classic','pixel') for v in ('before','after')])
plate('pack-detail.png',[(f'{v.title()}  /  100 S  /  {cam}',v,'pc-100-pixel-'+cam+'-73')
                         for cam in ('race','follow') for v in ('before','after')],(220,150,540,365))
