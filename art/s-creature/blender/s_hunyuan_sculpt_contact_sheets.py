"""Arrange actual Blender renders, with no image generation or retouching."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
root=Path.cwd();p=root/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/review-v1'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
def sheet(tags,name,cell_width=450):
 h=int(cell_width*.8);label=34
 im=Image.new('RGB',(cell_width*len(tags),(h+label)*2),(239,240,243));d=ImageDraw.Draw(im)
 for row,kind in enumerate(('BEFORE','AFTER')):
  for col,tag in enumerate(tags):
   source=Image.open(p/f'{kind}_{tag}.png').convert('RGB')
   source=source.resize((cell_width,h),Image.Resampling.LANCZOS)
   x=col*cell_width;y=row*(h+label)
   d.text((x+12,y+6),kind+' / '+tag,fill=(25,33,42),font=font)
   im.paste(source,(x,y+label))
 im.save(p/name)
sheet(['SIDE','FRONT','FRONT34','REAR34','BACK'],'FIVE_VIEW_BEFORE_AFTER.jpg')
sheet(['DETAIL_SIDE','DETAIL_FRONT','DETAIL_FRONT34'],'SHOULDER_CHEST_BEFORE_AFTER.jpg',640)
print('Contact sheets built from actual before/after Blender renders.')
