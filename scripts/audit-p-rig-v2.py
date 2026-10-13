"""Actual raster/trace comparisons. No alteration of creature artwork."""
import hashlib, json, math, os, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
os.environ.setdefault('MPLCONFIGDIR', '/tmp/evowild-p-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path('docs/evidence/p-rig-v2-20261013')
oldroot = Path('docs/evidence/p-layered-20261012')
atlas = json.loads(Path('public/concept/p-layered/atlas.json').read_text())
before = json.loads(Path('work/p-rig-v2/before-assets/concept/p-layered/atlas.json').read_text())
results = json.loads((root/'run-validation.json').read_text())
assert len(results) == 3

def section_width(part, directory, length):
    alpha = np.array(Image.open(directory/part['image']).convert('RGBA'))[:, :, 3]
    a, b = np.array(part['a']), np.array(part['b'])
    distance = np.linalg.norm(b-a)
    normal = np.array([-(b-a)[1], (b-a)[0]])/distance
    mid = (a+b)/2
    offsets = []
    for offset in np.arange(-max(alpha.shape), max(alpha.shape), .5):
        x, y = np.rint(mid+normal*offset).astype(int)
        if 0 <= y < alpha.shape[0] and 0 <= x < alpha.shape[1] and alpha[y,x] > 128:
            offsets.append(offset)
    return (max(offsets)-min(offsets)+.5)*length/distance

shape = {'units':'416x320 rig source pixels', 'body':{}, 'lowerLegs':{}}
for label, manifest in [('before',before),('after',atlas)]:
    p = manifest['parts']['body']; width = manifest['body']['width']
    shape['body'][label] = {'width':width, 'height':width*p['crop'][3]/p['crop'][2],
      'shoulderHipSpan':abs(p['shoulder'][0]-p['hip'][0])*width/p['crop'][2]}
    directory = Path('work/p-rig-v2/before-assets/concept/p-layered') if label=='before' else Path('public/concept/p-layered')
    for kind in ['fore','hind']:
        length = (91 if kind=='fore' else 89) if label=='before' else atlas['bones'][kind][1]
        shape['lowerLegs'].setdefault(kind,{})[label]={'boneLength':length,
          'alphaMidsectionWidth':section_width(manifest['parts'][kind+'-lower'],directory,length)}

sheet = np.array(Image.open(root/'layered-12-phase.png').convert('RGBA'))
poses = json.loads((root/'phase-poses.json').read_text())
shape['phaseClearance'] = []
for i, pose in enumerate(poses):
    frame = sheet[i//4*320:(i//4+1)*320,i%4*416:(i%4+1)*416]
    bottom = int(np.nonzero(frame[:,:,3]>12)[0].max())
    shape['phaseClearance'].append({'phase':i+1,'flight':pose['flight'],'alphaBottom':bottom,'clearance':295-bottom})
shape['jointCheckLimit'] = 'Joint-comparison.png shows real raster crops at 4x. Organic covers hide cut ends, but black outline and material seams remain; not an automated seam-quality pass.'
(root/'anatomy-measurements.json').write_text(json.dumps(shape,indent=2)+'\n')

fig, axes = plt.subplots(1,2,figsize=(12,5.2))
fig.subplots_adjust(left=.07,right=.98,top=.86,bottom=.24,wspace=.26)
for ax, name in zip(axes,['race-18-desktop','race-18-mobile']):
    old = json.loads((oldroot/(name+'-trace.json')).read_text())
    new = json.loads((root/(name+'-trace.json')).read_text())
    for data, label, color in [(old,'c648a95 correction','#a75443'),(new,'Revised correction','#287d89')]:
        t=[(s['time']-data['samples'][0]['time'])/1000 for s in data['samples']]
        values=[max(r['bodyOffset'] for r in s['field']) for s in data['samples']]
        ax.plot(t,values,label=label,color=color)
    ax.set(title=name, xlabel='Time within capture (s)',ylabel='Maximum P body correction (rig px)',ylim=(0,185))
    ax.spines[['top','right']].set_visible(False);ax.legend(fontsize=9)
fig.text(.5,.045,'All 5 P runners. Revised loaded heave is reported separately; actual body-depth lag is also retained in traces.',ha='center',fontsize=9)
fig.savefig(root/'body-correction-comparison.png',dpi=150)

fig,ax=plt.subplots(figsize=(9,5))
fig.subplots_adjust(left=.10,right=.97,top=.88,bottom=.23)
labels=['Isolated','18 PC','18 mobile'];oldresults=json.loads((oldroot/'run-validation.json').read_text())[1:]
oldmeans=[r['soleRasterTravelPx']['mean'] for r in oldresults];newmeans=[r['soleRasterTravelPx']['mean'] for r in results]
xx=np.arange(3);ax.bar(xx-.18,oldmeans,.36,label='c648a95',color='#a75443');ax.bar(xx+.18,newmeans,.36,label='Revised',color='#287d89')
ax.set(xticks=xx,xticklabels=labels,ylabel='Sole raster world-position change / 33ms (CSS px)',title='Support foot raster; persistent foot and contact IDs')
ax.legend();ax.spines[['top','right']].set_visible(False)
fig.text(.5,.04,'The same foot painter, before scene occlusion. Raster quantization is distinct from world-anchor drift (0).',ha='center',fontsize=9)
fig.savefig(root/'foot-slip-comparison.png',dpi=150)

font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
comparison=Image.new('RGB',(824,929),'#e8eef0');draw=ImageDraw.Draw(comparison)
for column,(directory,label) in enumerate([(oldroot,'c648a95'),(root,'Revised')]):
    data=json.loads((directory/'race-18-mobile-trace.json').read_text())
    index=max(range(len(data['samples'])),key=lambda i:max(r['bodyOffset'] for r in data['samples'][i]['field']))
    runner=max(data['samples'][index]['field'],key=lambda r:r['bodyOffset'])
    output=root/('before-mobile-max-sink.png' if column==0 else 'after-mobile-max-sink.png')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(directory/'race-18-mobile.mp4'),'-vf',f'select=eq(n\\,{index*2})','-frames:v','1',str(output)],check=True)
    image=Image.open(output).convert('RGB');comparison.paste(image.crop((0,0,412,839)),(column*412,60))
    draw.text((column*412+8,8),f'{label}: P{runner["id"]:02} correction {runner["bodyOffset"]:.3f}',font=font,fill='#203844')
    draw.text((column*412+8,30),f'Actual video frame {index*2}; each capture maximum',font=font,fill='#203844')
comparison.save(root/'lane-change-comparison.png')

strip=Image.new('RGB',(1920,840),'#10212b');draw=ImageDraw.Draw(strip)
for j,i in enumerate(range(0,360,30)):
    frame=Image.open(Path('work/p-rig-v2/capture/isolated-continuous')/f'{i:04}.png').crop((360,190,840,450))
    strip.paste(frame,(j%4*480,j//4*280))
    draw.text((j%4*480+8,j//4*280+260),f'{i/60:.2f}s / actual frame {i}',font=font,fill='white')
strip.save(root/'actual-motion-filmstrip.png')
print(json.dumps(shape))
