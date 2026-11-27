"""Verify all fixed-state pairs and compare each isolated candidate with HEAD."""
import csv
import json
import math
import sys
import zipfile
from pathlib import Path
from statistics import mean
import numpy as np
from PIL import Image, ImageDraw, ImageFont

work,out=map(Path,sys.argv[1:3]);out.mkdir(parents=True,exist_ok=True)
keys=sorted(p.stem for p in (work/'profile-base').glob('*.json'))
assert len(keys)==24
quality=[];gpu=[];rates=[]
def data(folder,key):return json.loads((work/folder/(key+'.json')).read_text())
def csvwrite(name,rows):
    with (out/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0],lineterminator='\n');w.writeheader();w.writerows(rows)
for mode in ('base','group','color','both'):
    for key in keys:
        samples=data('profile-'+mode,key);base=data('profile-base',key)
        assert len(samples)==len(base)==7
        for a,b in zip(samples,base):
            for field in ('frame','size','aa','state_sha','actors_sha','pixel_ids','nativeVisible','lod','streaming'):
                assert a[field]==b[field],(mode,key,a['frame'],field)
            assert not a['streaming']
            stem=key+'-'+str(a['frame'])+'.png';measure={}
            for kind in ('frames','actors'):
                x=np.asarray(Image.open(work/('profile-base')/kind/stem).convert('RGB'),dtype=np.int16)
                y=np.asarray(Image.open(work/('profile-'+mode)/kind/stem).convert('RGB'),dtype=np.int16)
                d=np.abs(x-y)
                measure[kind+'_max_channel']=int(d.max())
                measure[kind+'_changed_pixels']=int(d.any(2).sum())
                if kind=='actors':measure['mask_changed_pixels']=int((x.any(2)^y.any(2)).sum())
            quality.append(dict(mode=mode,case=key,frame=a['frame'],**measure))
        avg=lambda section,name:mean(r[section].get(name,0) for r in samples)
        oldtri=mean(r['triangles'].get('pixelMesh',0) for r in base);tri=avg('triangles','pixelMesh')
        gpu.append(dict(mode=mode,case=key,states=7,mesh_gpu_ms=round(avg('gpu','pixelMesh'),3),
            total_gpu_ms=round(mean(sum(r['gpu'].values()) for r in samples),3),
            cpu_pose_lod_ms=round(avg('cpu','sLod'),3),cpu_submit_mesh_ms=round(avg('cpu','pixelMesh'),3),
            cpu_pixel_ms=round(avg('cpu','pixel'),3),wait_ms=round(avg('cpu','wait'),3),
            draws=round(avg('calls','pixelMesh'),3),triangles=round(tri,3),
            triangle_reduction_pct=round((1-tri/oldtri)*100,3) if oldtri else 0,
            eligible_faces=(samples[0].get('surface') or {}).get('eligible',0),
            total_faces=(samples[0].get('surface') or {}).get('total',0),
            groups_rejected_back=round(mean((r.get('surface') or {}).get('groupBack',0) for r in samples),2),
            groups_rejected_outside=round(mean((r.get('surface') or {}).get('groupOutside',0) for r in samples),2)))
        if '-classic-' in key:continue
        trial=data('accept-'+mode,key);reference=data('accept-base',key)
        assert len(trial['samples'])==96
        for x,y in zip(trial['samples'],reference['samples']):
            assert {k:v for k,v in x.items() if k!='interval_ms'}=={k:v for k,v in y.items() if k!='interval_ms'},(mode,key)
        intervals=[s['interval_ms'] for s in trial['samples']]
        rates.append(dict(mode=mode,case=key,fps=round(1000/mean(intervals),3),
            mean_ms=round(mean(intervals),3),p95_ms=round(sorted(intervals)[91],3),frames=96,streaming_frames=sum(s['streaming'] for s in trial['samples'])))
csvwrite('quality.csv',quality);csvwrite('gpu.csv',gpu);csvwrite('performance.csv',rates)
verdict={}
for mode in ('group','color','both'):
    comparisons=[]
    for row in (r for r in rates if r['mode']==mode):
        before=next(r for r in rates if r['mode']=='base' and r['case']==row['case'])
        g=next(r for r in gpu if r['mode']==mode and r['case']==row['case'])
        gb=next(r for r in gpu if r['mode']=='base' and r['case']==row['case'])
        comparisons.append(dict(case=row['case'],gpu_improved=g['mesh_gpu_ms']<gb['mesh_gpu_ms'],p95_improved=row['p95_ms']<before['p95_ms']))
    q=[r for r in quality if r['mode']==mode]
    verdict[mode]=dict(pairs=len(q),mask_difference=sum(r['mask_changed_pixels'] for r in q),
        max_rgb_difference=max(max(r['actors_max_channel'],r['frames_max_channel']) for r in q),
        gpu_improved=sum(r['gpu_improved'] for r in comparisons),p95_improved=sum(r['p95_improved'] for r in comparisons),
        both_improved=sum(r['gpu_improved'] and r['p95_improved'] for r in comparisons),cases=comparisons)
(out/'summary.json').write_text(json.dumps(verdict,indent=2)+'\n')
with zipfile.ZipFile(out/'raw.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for group in ('profile','accept'):
        for mode in ('base','group','color','both'):
            for p in sorted((work/(group+'-'+mode)).glob('*.json')):z.write(p,group+'-'+mode+'/'+p.name)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for cam in ('race','follow'):
    for count in (50,100):
        stem=f'pc-{count}-pixel-{cam}-73.png';imgs=[]
        for mode in ('base','group','color','both'):
            im=Image.open(work/('profile-'+mode)/'frames'/stem).convert('RGB')
            base=np.asarray(Image.open(work/'profile-base/frames'/stem).convert('RGB'),dtype=np.int16)
            delta=np.abs(np.asarray(im,dtype=np.int16)-base).max(2)
            diff=Image.fromarray(np.stack((np.minimum(delta*64,255),np.zeros_like(delta),np.zeros_like(delta)),2).astype('uint8'))
            imgs.append((mode,im,diff))
        w,h=imgs[0][1].size;canvas=Image.new('RGB',(w*2,(h+30)*4),(15,28,35));d=ImageDraw.Draw(canvas)
        for i,(mode,im,diff) in enumerate(imgs):
            y=i*(h+30);d.text((8,y+5),f'{mode} / {count} S / {cam} / frame 73',font=font,fill='white')
            d.text((w+8,y+5),'RGB difference x64',font=font,fill='white')
            canvas.paste(im,(0,y+30));canvas.paste(diff,(w,y+30))
        canvas.save(out/f'{cam}-{count}-difference.png')
print(json.dumps(verdict,indent=1))
