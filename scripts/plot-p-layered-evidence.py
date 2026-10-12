"""Plots from actual browser traces; contact sheets only crop/scale source art."""
import json
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/evowild-p-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

root=Path('docs/evidence/p-layered-20261012')
results=json.loads((root/'run-validation.json').read_text())
fig,ax=plt.subplots(figsize=(10,5.2))
fig.subplots_adjust(left=.10,right=.98,top=.90,bottom=.23)
names=['Old: held-frame\nground-band proxy','New: isolated\npainted sole','New: 18 runners PC\npainted sole','New: 18 runners mobile\npainted sole']
means=[r['anchorOrLegacyBandTravelPx' if i==0 else 'soleRasterTravelPx']['mean'] for i,r in enumerate(results)]
bars=ax.bar(names,means,color=['#a75d4a','#287d89','#287d89','#287d89'])
ax.bar_label(bars,fmt='%.3f px',padding=4)
ax.set(ylabel='World-position change / sampled support interval (CSS px)',ylim=(0,8.3),title='Actual image measurements at 30 Hz, fixed browser clock')
ax.spines[['right','top']].set_visible(False)
fig.text(.5,.005,'Old proxy has no persistent toe identity. New sole masks use the runtime foot painter, before scene occlusion.',ha='center',fontsize=9)
fig.savefig(root/'foot-slip-comparison.png',dpi=160)

old=Image.open(root/'before-12-phase.webp').convert('RGBA')
new=Image.open(root/'layered-12-phase.png').convert('RGBA')
out=Image.new('RGB',(7*238,450),'#e8eef0');d=ImageDraw.Draw(out)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for row,im in enumerate([old,new]):
    for col,i in enumerate([5,6,7,8,9,11,0]):
        frame=im.crop((i%4*416,i//4*320,i%4*416+416,i//4*320+320))
        frame.thumbnail((238,184),Image.Resampling.LANCZOS)
        out.paste(frame,(col*238,row*225+28),frame)
        d.text((col*238+8,row*225+8),f'{"OLD" if row==0 else "NEW"} phase {i+1:02}',fill='#203844',font=font)
out.save(root/'transition-comparison.png')

# Actual scene frames cover more than three continuous cycles.
strip=Image.new('RGB',(4*480,3*280),'#10212b');d=ImageDraw.Draw(strip)
for j,i in enumerate(range(0,360,30)):
    frame=Image.open(Path('work/p-layered/capture/layered-isolated')/f'{i:04}.png').crop((360,190,840,450))
    strip.paste(frame,(j%4*480,j//4*280))
    d.text((j%4*480+10,j//4*280+260),f'{i/60:.2f}s / actual browser frame {i}',fill='white',font=font)
strip.save(root/'actual-motion-filmstrip.png')
