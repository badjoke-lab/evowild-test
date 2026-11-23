"""Use the exact v4 reference, mask threshold, regions and foot-patch rule."""
import json
from pathlib import Path
import sys
from scipy import ndimage
import numpy as np
from PIL import Image,ImageDraw

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'v3'))
import plates as p
out=p.ROOT/'public/s-pixel-lab/v4.1/evidence'
out.mkdir(exist_ok=True)
recipes=json.loads((p.CACHE/'recipes.json').read_text())

def foot_islands(ref, test):
    # At these views several feet can overlap. Count only separated patches
    # the reference actually resolves in the lower 18% (at least two pixels).
    a, b = p.opacity(ref), p.opacity(test)
    _, y, _, end = p.regions(a, 0)['feet']
    a, b = a[y:end], b[y:end]
    label, n = ndimage.label(a, np.ones((3, 3)))
    candidate, _ = ndimage.label(b, np.ones((3, 3)))
    seen, ref_count, matched_count = set(), 0, 0
    for idx in range(1, n+1):
        component = label == idx
        if component.sum() < 2:
            continue
        ref_count += 1
        overlaps = np.bincount(candidate[component])
        overlaps[0] = 0
        if overlaps.max() >= .5*component.sum():
            matched_count += 1
            seen.add(int(np.argmax(overlaps)))
    return [ref_count, matched_count, len(seen)]


results={}
for name in ['v4','v4.1']:
    method=name+'-lod-race'
    groups={}; feet=np.zeros(3,int); rows=[]
    for r in recipes:
        if r['group'] not in ('switch','gait'):continue
        ref=p.pixels('v3-stack',r['id']); test=p.pixels(method,r['id'])
        row={'id':r['id'],**p.metrics(ref,test,r['yaw'])};rows.append(row)
        groups.setdefault(r['group'],[]).append(row)
        if r.get('angle') in ('front','rear'):
            feet+=foot_islands(ref,test)
            groups.setdefault(r['angle'],[]).append(row)
        if r['group']=='switch' and 103<=r['span']<=113:groups.setdefault('fade',[]).append(row)
    results[name]={'summary':{k:p.summary(a) for k,a in groups.items()},'feet':feet.tolist(),'frames':rows}
    print(name,'crest',results[name]['summary']['switch']['crest'],'feet',feet,'gait',results[name]['summary']['gait']['feet'],flush=True)
(out/'quality.json').write_text(json.dumps(results,separators=(',',':'))+'\n')
def plate(keys,title,name):
    w=156+len(keys)*212
    im=Image.new('RGB',(w,600),p.PAPER);d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,61),fill=p.INK);p.text(d,(17,8),title,25,'white',True)
    for k,(key,caption) in enumerate(keys):
        x=151+k*212;p.text(d,(x+2,67),caption,16,bold=True)
        shots=[p.pixels(m,key) for m in ('v3-stack','v4-lod-race','v4.1-lod-race')]
        box=p.bounds(np.logical_or.reduce([p.opacity(a) for a in shots]))
        for j,a in enumerate(shots):p.panel(im,p.cut(a,box),(x,101+j*166,205,159))
    for j,label in enumerate(['128層原本','v4','v4.1']):p.text(d,(14,165+j*166),label,19,bold=True)
    im.save(out/name,optimize=True)
plate([(f'switch-{i}',f'{60+202*i/72:.0f} px') for i in [12,17,24,38,52,70]],'単一サンプル　遠景から近景への頭冠','lod.png')
plate([(f'pose-{i}-{key}',f'{label} · {i+1:02d}/24') for i,key,label in [(2,'front','正面'),(8,'front','正面'),(17,'front','正面'),(2,'rear','背面'),(8,'rear','背面'),(17,'rear','背面')]],'同じ走行位相で見る脚先','feet.png')

# Both surface rows use the race's single sample, including at specimen size.
with Image.open(p.ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png') as art:
    im=Image.new('RGB',(1410,792),p.PAPER)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,im.width,64),fill=p.INK)
    p.text(d,(18,6),'S型基準原画と同じ方位の形状',25,'white',True)
    p.text(d,(18,41),'同一列のレンダーは同じ倍率。上面の原画は尾部のみ。',14,p.GREEN)
    for j,label in enumerate(['基準原画','128層原本','v4 · 1 sample','v4.1 · 1 sample']):
        p.text(d,(9,168+j*172),label,16,bold=True)
    for col,(key,caption,_,crop) in enumerate(p.VIEWS):
        x=151+col*251
        p.text(d,(x+3,72),caption,16,bold=True)
        p.panel(im,art.crop(crop),(x,102,246,167))
        imgs=[p.pixels(k,'view-'+key) for k in ('v3-stack','v4-lod-race','v4.1-lod-race')]
        box=p.bounds(np.logical_or.reduce([p.opacity(a) for a in imgs]))
        for j,a in enumerate(imgs):
            p.panel(im,p.cut(a,box),(x,274+j*172,246,167))
    im.save(out/'original.png',optimize=True)
