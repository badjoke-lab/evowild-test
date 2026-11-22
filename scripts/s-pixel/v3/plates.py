"""Measure untouched, matched WebGL frames and assemble their comparison plates."""
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'public/s-pixel-lab/v3/evidence'
OUT.mkdir(parents=True,exist_ok=True)
CACHE=Path(sys.argv[1])
VIEWS=[('side','側面',400,(66,70,750,508)),('front','正面',185,(787,107,930,506)),
       ('rear','背面',185,(978,107,1110,506)),('top','上面',245,(1177,781,1430,851)),
       ('quarter','斜め45°',290,(1138,87,1430,504))]
PAPER='#f2f2ea'
PANEL='#dfe6e1'
INK='#223831'
GREEN='#9cd2b3'

def pixels(method,key):
    with Image.open(CACHE/method/(key+'.png')) as im:
        return np.array(im.convert('RGB'))

def opacity(im):
    return np.max(im,axis=2)>12

def bounds(mask):
    yy,xx=np.nonzero(mask)
    if not len(xx):
        raise ValueError('An expected runner disappeared entirely')
    return (int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))

def regions(mask,yaw):
    x,y,r,b=bounds(mask)
    h=b-y;w=r-x
    out={'body':(x,y,r,b),'crest':(x,y,r,y+max(1,round(h*.25))),
         'feet':(x,b-max(1,round(h*.18)),r,b)}
    cosine=math.cos(math.radians(yaw))
    if abs(cosine)>.55:
        side=max(1,round(w*.18))
        out['tail']=(r-side,y,r,b) if cosine>0 else (x,y,x+side,b)
    return out

def metrics(a,b,yaw):
    ma,mb=opacity(a),opacity(b)
    union=ma|mb
    data={}
    for name,(x,y,r,end) in regions(union,yaw).items():
        va,vb=ma[y:end,x:r],mb[y:end,x:r]
        both=va&vb
        u=va|vb
        data[name]={'iou':round(float(both.sum()/max(1,u.sum())),5),
                    'retained':round(float(both.sum()/max(1,va.sum())),5),
                    'reference_px':int(va.sum())}
    def centroid(mask):
        yy,xx=np.nonzero(mask)
        return np.array([xx.mean(),yy.mean()])
    delta=centroid(mb)-centroid(ma)
    data['centroid_dx_dy']=[round(float(v),4) for v in delta]
    data['rgb_mae']=round(float(np.abs(a.astype('i2')-b.astype('i2'))[union].mean()),3)
    return data

def percentile(values,q):
    return round(float(np.percentile(values,q)),5)

def summary(rows):
    if not rows:
        return {}
    out={}
    for region in ('body','crest','feet','tail'):
        present=[r[region] for r in rows if region in r and r[region]['reference_px']>0]
        if present:
            out[region]={'samples':len(present),'iou_median':percentile([q['iou'] for q in present],50),
                         'iou_min':min(q['iou'] for q in present),
                         'retained_min':min(q['retained'] for q in present)}
    out['rgb_mae_median']=percentile([r['rgb_mae'] for r in rows],50)
    out['max_centroid_offset_px']=round(max(np.linalg.norm(r['centroid_dx_dy']) for r in rows),4)
    return out

def font(n,bold=False):
    f=Path('/usr/share/fonts/opentype/noto')/('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')
    return ImageFont.truetype(str(f),n) if f.exists() else ImageFont.load_default(size=n)

def text(d,xy,s,size=16,color=INK,bold=False):
    d.text(xy,s,font=font(size,bold),fill=color)

def panel(sheet,img,box,bg=PANEL):
    x,y,w,h=box; im=ImageDraw.Draw(sheet);im.rectangle((x,y,x+w-1,y+h-1),fill=bg)
    scale=min((w-10)/img.width,(h-10)/img.height)
    copy=img.resize((max(1,round(img.width*scale)),max(1,round(img.height*scale))),Image.Resampling.NEAREST)
    sheet.paste(copy,(x+(w-copy.width)//2,y+(h-copy.height)//2),copy.getchannel('A') if copy.mode=='RGBA' else None)

def cut(pixels,box):
    img=Image.fromarray(pixels)
    img.putalpha(Image.fromarray((opacity(pixels)*255).astype('uint8')))
    return img.crop(box)

def view_plate():
    sheet=Image.new('RGB',(1548,991),PAPER);d=ImageDraw.Draw(sheet)
    d.rectangle((0,0,1548,80),fill=INK);text(d,(22,9),'EvoWild Run   /   Sprint Morph',34,'white',True)
    text(d,(23,56),'S–01    /    v2 → v3    /    同一カメラ・静止姿勢',15,GREEN)
    ref=Image.open(ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png')
    methods=['v2-stack','v3-stack','v3-surface']
    x=171; scores={}
    for key,caption,w,box in VIEWS:
        key_id='view-'+key
        text(d,(x,88),caption,20,bold=True)
        panel(sheet,ref.crop(box),(x,121,w,186),'#e5edf1')
        if key=='top':
            text(d,(x+5,282),'基準画は尾のみ',13)
        ims=[pixels(m,key_id) for m in methods]
        views_dir=OUT.parent/'assets/views'
        views_dir.mkdir(parents=True,exist_ok=True)
        cut(ims[-1],(0,0,ims[-1].shape[1],ims[-1].shape[0])).save(views_dir/(key+'.png'),optimize=True)
        box=bounds(np.logical_or.reduce([opacity(im) for im in ims]))
        for j,im in enumerate(ims):
            panel(sheet,cut(im,box),(x,314+j*207,w,199))
        score=metrics(ims[0],ims[2],{'side':0,'front':-90,'rear':90,'top':0,'quarter':-45}[key])
        scores[key]={'surface_vs_v2':score,'v3_stack_vs_v2':metrics(ims[0],ims[1],0)}
        text(d,(x,940),'IoU   '+format(score['body']['iou'],'.3f'),16)
        x+=w+13
    for y,title,subtitle in [(158,'基準画','原画'),(368,'v2','128層スタック'),(575,'v3','128層スタック'),(784,'v3','近景メッシュ')]:
        text(d,(22,y),title,27,bold=True);text(d,(22,y+40),subtitle,16)
    sheet.save(OUT/'comparison.png',optimize=True)
    return scores

def gait_plate():
    w,h=1548,1060
    sheet=Image.new('RGB',(w,h),PAPER);d=ImageDraw.Draw(sheet)
    d.rectangle((0,0,w,76),fill=INK);text(d,(20,8),'S–01    /    四足走行 24 ポーズ',30,'white',True)
    text(d,(21,52),'上からv2積層・v3精細メッシュ・v3自動LOD。側面・同時刻・投影幅156 px。',14,GREEN)
    all_ims=[]
    for phase in range(24):
        all_ims.append([pixels(m,'pose-'+str(phase)+'-side') for m in ['v2-stack','v3-surface','v3-lod']])
    common=bounds(np.logical_or.reduce([opacity(im) for pair in all_ims for im in pair]))
    for phase,pair in enumerate(all_ims):
        x=10+(phase%6)*257;y=83+(phase//6)*242
        text(d,(x+1,y+1),f'{phase+1:02d}',13)
        for j,im in enumerate(pair):
            panel(sheet,cut(im,common),(x+24,y+2+j*76,223,74))
    sheet.save(OUT/'gait-24.png',optimize=True)

def switch_plate(rows):
    sheet=Image.new('RGB',(1330,482),PAPER);d=ImageDraw.Draw(sheet)
    d.rectangle((0,0,1330,71),fill=INK)
    text(d,(20,8),'S–01    /    走行中のズーム',29,'white',True)
    text(d,(22,49),'表面と足先を同じ位相で比較。列は広角から近景への順。',13,GREEN)
    text(d,(14,183),'積層',20,bold=True);text(d,(14,350),'距離LOD',16,bold=True)
    pool=[rows[i] for i in [0,11,23,36,50,72]]
    for i,r in enumerate(pool):
        span=r['span'];key=r['id']
        ims=[pixels(m,key) for m in ('v3-stack','v3-lod')]
        box=bounds(np.logical_or.reduce([opacity(im) for im in ims]))
        x=95+i*204
        text(d,(x,85),format(span,'.0f')+' px',18,bold=True)
        for j,im in enumerate(ims):
            panel(sheet,cut(im,box),(x,119+j*166,195,156))
        text(d,(x,447),'IoU  '+format(r['body']['iou'],'.3f'),14)
    sheet.save(OUT/'lod-study.png',optimize=True)

def temporal(method):
    tallies={k:[0,0] for k in ('crest','feet','body')}
    files=[f'turn-{i}' for i in range(180)]
    def mask(i):
        return opacity(pixels(method,files[i%180]))
    before,at=mask(-1),mask(0)
    for i in range(180):
        after=mask(i+1)
        transient=(before==after)&(before!=at)
        union=before|at|after
        for key,(x,y,r,b) in regions(union,-180+i*2).items():
            if key in tallies:
                tallies[key][0]+=int(transient[y:b,x:r].sum())
                tallies[key][1]+=int(union[y:b,x:r].sum())
        before,at=at,after
    return {k:{'single_frame_reversal':n,'sampled_union':d,'fraction':round(n/d,6)} for k,(n,d) in tallies.items()}

def main():
    recipes=json.loads((CACHE/'recipes.json').read_text())
    categories={}
    for group,reference,candidate in [('gait','v2-stack','v3-surface'),('gait_lod','v2-stack','v3-lod'),('switch','v3-stack','v3-lod'),
                                       ('cut','v3-stack','v3-lod')]:
        rows=[]
        for r in recipes:
            if r['group']!=group.split('_')[0]:
                continue
            key=r['id']
            row={**r,**metrics(pixels(reference,key),pixels(candidate,key),r['yaw'])}
            rows.append(row)
        categories[group]={'summary':summary(rows),'frames':rows}
    switch=categories['switch'];draws=json.loads((CACHE/'v3-lod/draws.json').read_text())
    for row in switch['frames']:
        row['mix']=draws[row['id']]['mix']
    d=np.array([r['centroid_dx_dy'] for r in switch['frames']])
    switch['max_extra_centroid_motion_px']=round(float(np.linalg.norm(np.diff(d,axis=0),axis=1).max()),4)
    report={'raster':[512,320],'mask_threshold':'max(R,G,B)>12; floor and shadow disabled',
            'regions':'crest = upper 25% in image coordinates; feet = bottom 18%; tail = distal 18% along lateral projection when isolated from head; some oblique views include other body parts.',
            'views':view_plate(),**categories,
            'turntable_flicker':{'sampling':'180 views 2° steps, fixed idle stance, span 156 px, elevation 12°; indicator counts a covered/clear reversal lasting exactly one frame within each region.',
                                'v2-stack':temporal('v2-stack'),'v3-surface':temporal('v3-surface'),'v3-lod':temporal('v3-lod')}}
    gait_plate()
    switch_plate(switch['frames'])
    (OUT/'appearance.json').write_text(json.dumps(report,indent=1))
    print('gait',categories['gait']['summary'],'LOD',switch['summary'])

if __name__=='__main__':
    main()
