from PIL import Image
import json, pathlib, shutil
root=pathlib.Path('.')
out=root/'public/concept/p-layered-v5';out.mkdir(exist_ok=True)
src=root/'docs/evidence/p-rig-v5-20261015/parts-source.png'
# Authored transparent source is preserved in evidence; only crop/pack here.
im=Image.open(src)
a=json.load(open('public/concept/p-layered-v4/atlas.json'))
for p in a['parts'].values():shutil.copy('public/concept/p-layered-v4/'+p['image'],out/p['image'])
del a['parts']['body'];(out/'body.png').unlink()
spec={'pelvis':([28,159,660,341],[515,180],.235),'lumbar':([703,182,393,285],[195,143],.245),'chest':([1111,12,650,493],[205,330],.255),'fore-upper':([493,488,377,371],[100,88],[290,304]),'fore-lower':([967,600,300,259],[72,57],[233,216])}
for name,(crop,pivot,last) in spec.items():
 x,y,w,h=crop;im.crop((x,y,x+w,y+h)).save(out/(name+'.png'))
 p={'crop':crop,'image':name+'.png'}
 if isinstance(last,list):p.update(a=pivot,b=last)
 else:p.update(pivot=pivot,scale=last)
 a['parts'][name]=p
 a['sources']=[str(src),'public/concept/p-layered-v4/atlas.json']
a['notes']='v5 experimental rigid chest, lumbar and pelvis. Uniform scale per authored part; unchanged 70/68 limb bones and v3 soles.'
a['rig']={'shoulder':[250,146],'hip':[179,164]}
(out/'atlas.json').write_text(json.dumps(a,indent=2)+'\n')
