"""Lay out actual Blender pixels, preserving proportions and source hashes."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[3]
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',19)
BG=(234,240,246);INK=(20,35,50);sources={}
mode=sys.argv[1] if len(sys.argv)>1 else 'renders'
variant=sys.argv[2] if len(sys.argv)>2 else 'B';suffix='' if variant=='B' else variant;new='R8'+suffix
def paste(canvas,p,box,crop=None):
    im=Image.open(p).convert('RGB');sources[str(p.relative_to(REPO))]=hashlib.sha256(p.read_bytes()).hexdigest()
    if crop:im=im.crop(crop)
    im=ImageOps.contain(im,(box[2],box[3]),Image.Resampling.LANCZOS)
    canvas.paste(im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2))
def save(im,name):
    p=ROOT/'comparisons'/name;assert not p.exists();im.save(p)
if mode=='viewport':
    for kind,times in [('INTEGER',[float(i) for i in range(1,25)]),('HALF',[i+.5 for i in range(1,24)])]:
        im=Image.new('RGB',(1800,840),BG);d=ImageDraw.Draw(im)
        for index,t in enumerate(times):
            x=(index%6)*300;y=(index//6)*200
            d.text((x+8,y+5),new+' T%.2f'%t,font=font,fill=INK)
            paste(im,ROOT/'viewport'/(new+'_HIP_T%05.2f_SIDE.png'%t),(x+5,y+30,290,168))
        d.text((10,812),'Actual live Blender SOLID viewport. Surface palette is assessed in separate Cycles renders.',font=font,fill=INK)
        save(im,new+'_'+kind+'_FRAMES_VIEWPORT.png')
else:
    views=['SIDE','FRONT','FRONT34','REAR34','BACK']
    for small in [False,True]:
        cw,ch=(170,155) if small else (322,285)
        im=Image.new('RGB',(cw*5,ch*2+22),BG);d=ImageDraw.Draw(im)
        for row,label in enumerate(['R7',new]):
            for col,v in enumerate(views):
                x=col*cw;y=row*ch
                d.text((x+6,y+4),label+' '+v,font=font,fill=INK)
                paste(im,ROOT/'renders'/(label+'_static')/('F01_'+v+'.png'),(x+5,y+28,cw-10,128 if small else 250))
        save(im,'R7_'+new+'_STATIC_'+('128PX' if small else 'FIVE_VIEWS')+'.png')
    im=Image.new('RGB',(1610,650),BG);d=ImageDraw.Draw(im)
    for row,label in enumerate(['R7',new]):
        for col,f in enumerate([1,6,12,18,24]):
            x=col*322;y=row*310;d.text((x+8,y+5),label+' frame '+str(f),font=font,fill=INK)
            paste(im,ROOT/'renders'/(label+'_hip')/('F%02d_SIDE_HIP.png'%f),(x+5,y+30,312,270))
    d.text((10,622),'Matched Cycles renders from separately saved verification rigs. Same R7 bones, weights and keys.',font=font,fill=INK)
    save(im,'R7_'+new+'_SIDE_HIP_FIVE_POSES.png')
    im=Image.new('RGB',(1800,610),BG);d=ImageDraw.Draw(im)
    for row,label in enumerate(['R7',new]):
        for col,(f,v) in enumerate([(f,v) for v in ['REAR34_HIP','BACK_HIP'] for f in [1,12,24]]):
            x=col*300;y=row*295;d.text((x+6,y+5),label+' F'+str(f)+' '+v,font=font,fill=INK)
            paste(im,ROOT/'renders'/(label+'_hip')/('F%02d_%s.png'%(f,v)),(x+5,y+30,290,250))
    save(im,'R7_'+new+'_REAR_BACK_THREE_POSES.png')
    ref=REPO/'art/s-creature/references/00_s_type_modeling_image_v1.png'
    im=Image.new('RGB',(1500,610),BG);d=ImageDraw.Draw(im)
    d.text((10,10),'Canonical pelvis / different pose and projection',font=font,fill=INK)
    paste(im,ref,(10,48,480,445),(400,188,655,414))
    for col,label in enumerate(['R7',new],1):
        d.text((col*500+10,10),label+' neutral / SIDE_HIP',font=font,fill=INK)
        paste(im,ROOT/'renders'/(label+'_hip')/'F01_SIDE_HIP.png',(col*500+10,48,480,445))
    d.text((10,535),'R8: real local taper plus a cleaner surface boundary. Broad reference planes remain incomplete: REVISE.',font=font,fill=INK)
    d.text((10,566),'Reference and model poses/projections differ. This is a visual comparison, not a silhouette match score.',font=font,fill=INK)
    save(im,'REFERENCE_R7_'+new+'_PELVIS.png')
    im=Image.new('RGB',(1500,1280),BG);d=ImageDraw.Draw(im)
    for row,(title,path,crop) in enumerate([('Canonical S / side view',ref,(14,70,755,511)),
          ('R7 / neutral SIDE',ROOT/'renders/R7_static/F01_SIDE.png',None),(new+' / neutral SIDE',ROOT/('renders/'+new+'_static/F01_SIDE.png'),None)]):
        y=row*405;d.text((12,y+8),title,font=font,fill=INK);paste(im,path,(12,y+36,1450,355),crop)
    d.text((12,1235),'Unwarped images, proportional scaling only. Global silhouette differences and original leg staging remain visible.',font=font,fill=INK)
    save(im,'REFERENCE_R7_'+new+'_SIDE_SILHOUETTE.png')
out=ROOT/'evidence'/('COMPARISON_SOURCES_'+suffix+('_' if suffix else '')+mode+'.json');assert not out.exists()
out.write_text(json.dumps({'method':'Source pixels only; proportional resize, crop, placement and labels. No generative or deformation edits.',
 'reference_crop_pelvis':[400,188,655,414],'reference_crop_side':[14,70,755,511],'sources':sources},indent=2)+'\n')
print('COMPARISONS_CREATED',mode)
