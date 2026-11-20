"""Extend depth off silhouette to guide the inverse lookup at adjacent view angles.
Coverage and colour remain exactly those of the original 4-sample capture.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
root=Path(__file__).resolve().parents[3]/'public/s-pixel-lab/v2/assets/angles'
index=json.loads((root/'index.json').read_text())
palette=json.loads((root.parent/'manifest.json').read_text())['palette']
rgb=np.array([tuple(bytes.fromhex(c[1:])) for c in palette])
shades=[.95,.89,.78,1.04,.88,1.,1.,1.]
lookup=np.clip(np.rint(rgb[np.arange(144)//8]*np.array(shades)[np.arange(144)%8,None]),0,255).astype('u1')
for bank in index['angles']:
    for page,(file,_,_) in enumerate(bank['files']):
        im=np.array(Image.open(root/file).convert('RGB'))
        for pg,u,v,w,h,_,_ in bank['rects']:
            if page!=pg:continue
            tile=im[v:v+h,u:u+w]
            missing=tile[:,:,2]==0
            nearest=distance_transform_edt(missing,return_distances=False,return_indices=True)
            tile[:,:,1]=tile[:,:,1][tuple(nearest)]
        base=Path(file).stem
        color=base+'-paint.png';depth=base+'-depth.png'
        rgba=np.dstack([lookup[im[:,:,0]],im[:,:,2]])
        Image.fromarray(rgba).save(root/color,compress_level=6)
        Image.fromarray(im[:,:,1]).save(root/depth,compress_level=6)
        bank['files'][page]=[color,im.shape[1],im.shape[0],depth]
        (root/file).unlink()
(root/'index.json').write_text(json.dumps(index,separators=(',',':')))
