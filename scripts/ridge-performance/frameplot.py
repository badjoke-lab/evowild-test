"""Plot the 96 actual RAF intervals in each dense-field pixel trial."""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

work,out=map(Path,sys.argv[1:3])
fig,axes=plt.subplots(2,2,figsize=(11,6),sharex=True,sharey=True,layout='constrained')
for screen,axisrow in zip(('pc','phone'),axes):
    for camera,ax in zip(('race','follow'),axisrow):
        for build,color in [('before','#917c64'),('after','#096d88')]:
            data=json.loads((work/('accept-'+build)/f'{screen}-100-pixel-{camera}.json').read_text())
            ax.plot([s['elapsed_ms']/1000 for s in data['samples']],[s['interval_ms'] for s in data['samples']],
                    color=color,linewidth=1.25,label=build.title(),alpha=.87)
        ax.axhline(33.3,color='#8b3e39',linestyle='--',linewidth=1,label='33.3 ms')
        ax.set_title(('PC width' if screen=='pc' else 'Phone width')+' / '+camera.title(),loc='left',fontsize=11)
        ax.grid(axis='y',alpha=.24);ax.set_ylim(bottom=0)
        ax.spines[['top','right']].set_visible(False)
        if camera=='race':ax.set_ylabel('RAF interval (ms)')
        if screen=='phone':ax.set_xlabel('Race time (s)')
axes[0,0].legend(loc='upper left',ncols=3,fontsize=8)
fig.suptitle('Ridge Oval  /  100 S runners  /  Chromium SwiftShader',fontsize=15)
fig.savefig(out/'frame-times.png',dpi=130)
