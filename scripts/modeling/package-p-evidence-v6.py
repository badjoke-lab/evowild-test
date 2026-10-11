"""Assemble actual GLB screenshots; no generated or modified reference artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json, hashlib
root=Path(__file__).resolve().parents[2]
dest=root/'docs/evidence/p-canonical-3d-v6-20261012'
scratch=root/'work/p-canonical-v6'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',23)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)

def sheet(name,title,items,columns=3,cell=(520,430)):
    w,h=cell;rows=(len(items)+columns-1)//columns
    im=Image.new('RGB',(columns*w,rows*h+84),'#e8edf0');d=ImageDraw.Draw(im)
    d.text((20,16),title,fill='#172831',font=font)
    d.text((20,50),'Actual reference + rendered GLBs / review candidate / production HOLD',fill='#45565e',font=small)
    for i,(label,file) in enumerate(items):
        x=(i%columns)*w;y=84+(i//columns)*h
        d.text((x+14,y+12),label,fill='#172831',font=font)
        pic=Image.open(file).convert('RGBA')
        # Scale only. Canonical pixels remain unretouched; the source is untouched.
        pic.thumbnail((w-24,h-60),Image.Resampling.LANCZOS)
        if file.name=='P.webp':pic=Image.open(file).convert('RGBA').resize((414,326),Image.Resampling.NEAREST)
        im.paste(pic,(x+(w-pic.width)//2,y+49+(h-60-pic.height)//2),pic)
    im.save(dest/name)

sheet('comparison-canonical-v5-v6.png','Canonical P / v5 / v6 muscle relief',[
 ('Canonical P - unchanged source',root/'public/concept/P.webp'),
 ('v5 / FRONT34',dest/'v5-FRONT34.png'),('v6 / FRONT34',dest/'FRONT34.png'),
 ('v6 / FRONT',dest/'FRONT.png'),('v5 / SIDE',dest/'v5-SIDE.png'),('v6 / SIDE',dest/'SIDE.png')])
sheet('five-views.png','P v6 / five real model views',[(v,dest/(v+'.png')) for v in ['SIDE','FRONT','FRONT34','REAR34','BACK']],3)
sheet('running-contact-sheet.png','P v6 / gait phases and cycle boundaries',[(v+' / frame '+str(f),dest/f'run-{v}-{f:02}.png') for v in ['SIDE','FRONT34'] for f in [0,6,12,18,23,24,47,48,71,72]],5,(400,340))
for view in ['SIDE','FRONT34']:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(scratch/f'run-frames/{view}-%03d.png'),'-frames:v','96','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',str(scratch/f'{view}.mp4')],check=True)
(scratch/'concat.txt').write_text("file 'SIDE.mp4'\nfile 'FRONT34.mp4'\n")
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(scratch/'concat.txt'),'-c','copy','-movflags','+faststart',str(dest/'running-review.mp4')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_read_frames:format=duration','-of','json',str(dest/'running-review.mp4')]))
assert float(probe['format']['duration'])>=6.39,probe
assert int(probe['streams'][0]['nb_read_frames'])==192,probe
(dest/'video-validation.json').write_text(json.dumps({'source':'96 separately evaluated GLB frames per view; no encoder frame-loop filter','cyclesPerView':4,'cycleSeconds':.8,**probe},indent=2)+'\n')
# Decode the delivered MP4 itself to verify more than just the input PNG sequence.
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(dest/'running-review.mp4'),'-vf','fps=5,scale=320:240,tile=8x4','-frames:v','1',str(dest/'video-decoded-contact-sheet.png')],check=True)
print('Packaged five views, canonical/v5/v6 comparison, 6.4s video, decoded video sheet')
