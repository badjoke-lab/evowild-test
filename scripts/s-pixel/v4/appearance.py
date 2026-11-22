"""Summarize matched, unscaled browser readbacks against the v3 128-section reference."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent/'v3'))
import plates as p   # v3 metrics, masks, original-art crops and recipe cache
out = p.ROOT/'public/s-pixel-lab/v4/evidence'
recipes = json.loads((p.CACHE/'recipes.json').read_text())
report = {}
methods = ['v3-lod', 'v4-lod', 'v3-lod-race', 'v4-lod-race']


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


for method in methods:
    groups = {}
    rows = []
    toes = np.zeros(3, int)
    for r in recipes:
        if r['group'] == 'turn':
            continue
        ref, test = (p.pixels(k, r['id']) for k in ['v3-stack', method])
        values = p.metrics(ref, test, r['yaw'])
        row = dict(id=r['id'], **values)
        rows.append(row)
        groups.setdefault(r['group'], []).append(row)
        if r.get('angle') in ['front','rear'] and r['group']=='gait':
            toes += foot_islands(ref,test)
            groups.setdefault(r['angle'], []).append(row)
        if r['group']=='switch' and 103 <= r['span'] <= 113:
            groups.setdefault('fade', []).append(row)
    delta = np.array([q['centroid_dx_dy'] for q in groups['switch']])
    report[method] = {'summary':{k:p.summary(v) for k,v in groups.items()},
                      'switch_max_excess_centroid_motion_px':round(float(np.linalg.norm(np.diff(delta,axis=0),axis=1).max()),4),
                      'front_rear_foot_patches':dict(zip(['reference','half_covered','distinct'],map(int,toes))),
                      'orbit':p.temporal(method),'frames':rows}

(out/'appearance.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
labels=['128層原本','v3','v4']
def plate(name,title,subtitle,cases,original=False):
    column=254
    w=155+len(cases)*column
    rows=4 if original else 3
    im=Image.new('RGB',(w,104+rows*172),p.PAPER)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,66),fill=p.INK);p.text(d,(18,5),title,25,'white',True)
    p.text(d,(19,43),subtitle,14,p.GREEN)
    art=Image.open(p.ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png')
    for j,word in enumerate((['基準原画'] if original else [])+labels):
        p.text(d,(13,170+172*j),word,18,bold=True)
    for i,(key,title,crop) in enumerate(cases):
        x=151+column*i
        p.text(d,(x+3,72),title,16,bold=True)
        imgs=[p.pixels(k,key) for k in ('v3-stack','v3-lod','v4-lod')]
        box=p.bounds(np.logical_or.reduce([p.opacity(a) for a in imgs]))
        if original:
            p.panel(im,art.crop(crop),(x,102,column-5,167))
        for j,a in enumerate(imgs):
            p.panel(im,p.cut(a,box),(x,102+(j+int(original))*172,column-5,167))
    im.save(out/name,optimize=True)
plate('original.png','S–01　原画と同一視点の標本','最上位基準画像からの切り出し。上面の原画は尾部のみ。各列内でレンダーの拡大率を統一。',
      [('view-'+k,caption,box) for k,caption,_,box in p.VIEWS],True)
plate('legs.png','正面・背面の接地と脚先','位相は 24 姿勢の通し番号。投影幅 156 px。画像を最近傍拡大。',
      [(f'pose-{i}-{k}',f'{name}　{i+1:02d}/24',None) for i,k,name in
       [(1,'front','正面'),(5,'front','正面'),(12,'front','正面'),(5,'rear','背面'),(12,'rear','背面'),(18,'rear','背面')]])
plate('transition.png','遠景から近景への輪郭','各列で原本・v3・v4 の時刻と視点を一致。列の中央付近がスプライトとメッシュの移行帯。',
      [(f'switch-{i}',f'{(60+202*i/72):.0f} px',None) for i in (10,15,16,18,19,25)])
views = out.parent/'assets/views'
views.mkdir(exist_ok=True)
for key,*_ in p.VIEWS:
    image = p.pixels('v4-lod','view-'+key)
    p.cut(image,(0,0,image.shape[1],image.shape[0])).save(views/(key+'.png'),optimize=True)
for m in methods:
    print(m,report[m]['summary']['gait']['body']['iou_median'],report[m]['front_rear_foot_patches'])
