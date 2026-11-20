"""Revise only the crest backbone and the lateral stride of the four existing limbs."""
from pathlib import Path
import sys, json, hashlib
import numpy as np
from scipy.ndimage import label
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bake as source
from artwork import SX,SY,SZ,X0,Z0,GROUND,NY,NX,NZ,PARTS,KEY

DEST=source.OUT.parent/'v2/assets'
EVIDENCE=DEST.parent/'evidence'
LIMBS=('nearF','farF','nearH','farH')
def in_limb(name):
    return next((leg for leg in LIMBS if name.startswith(leg)),None)

def restore_spine(volume,part,transform):
    # Follow the existing drawn strip even where its needle is narrower than one
    # dorsal texel. Shared face cells connect steps in x, y and depth after posing.
    side=part['planes'][0]
    columns=np.flatnonzero(side.any(0))
    centers=np.array([np.mean(np.flatnonzero(side[:,i])) for i in columns])
    path=np.linspace(columns[0],columns[-1],4*(columns[-1]-columns[0])+1)
    xx=X0+(path+.5)*SX
    yy=GROUND-(np.interp(path,columns,centers)+.5)*SY
    zz=np.full(len(path),part['offset']) if part['center'] is None else np.interp(xx,*part['center'])
    mat,delta=transform
    px,py=mat@np.array([xx,yy])+delta[:,None]
    coords=np.stack([np.rint((GROUND-py)/SY-.5),np.rint((zz-Z0)/SZ-.5),np.rint((px-X0)/SX-.5)],1).astype(int)
    prev=coords[0].copy()
    for i,point in enumerate(coords):
        col=round(path[i]);ys=np.flatnonzero(side[:,col])
        color=side[ys[len(ys)//2],col] if len(ys) else KEY['steel']
        # Keep the already painted surface intact. Extend only missing core cells.
        for axis in (2,0,1):
            prev[axis]=point[axis]
            at=tuple(prev)
            if volume[at]==0:volume[at]=color

def shift_limb(volume,name,frame):
    sign=1 if name.startswith('near') else -1
    h=(np.arange(NY)+.5)*SY
    u=np.clip((230-h)/150,0,1)
    weight=u*u*(3-2*u)
    # Fore feet travel inside the hind tracks as on the front elevation.
    extra=-3.5 if name.endswith('F') else 5.0
    if frame>=0:
        phase=(frame/24-source.PHASES[name])%1
        if phase>source.DUTY:
            swing=np.sin(np.pi*(phase-source.DUTY)/(1-source.DUTY))**2
            extra+=(-1.5 if name.endswith('F') else 3.0)*swing
    shifts=np.rint(sign*extra*weight/SZ).astype(int)
    for shift in np.unique(shifts):
        if shift:volume[shifts==shift]=np.roll(volume[shifts==shift],shift,axis=1)
    return volume

def write_stack(vol,divisions,path):
    band=NY//divisions
    planes=vol.reshape(divisions,band,NZ,NX)
    slices=planes[:,band//2].copy()
    for j in sorted(range(band),key=lambda k:abs(k+.5-band/2)):
        np.copyto(slices,planes[:,j],where=(slices==0)&(planes[:,j]>0))
    coords=[];u=v=line=0
    for layer in slices:
        z,x=np.nonzero(layer)
        left,top,w,h=(int(x.min()),int(z.min()),int(np.ptp(x)+1),int(np.ptp(z)+1)) if len(x) else (0,0,0,0)
        if u+w>1024:u=0;v+=line;line=0
        coords.append([left,top,w,h,u,v]);u+=w;line=max(line,h)
    atlas=np.zeros((v+line,1024),'u1')
    for layer,(x,z,w,h,u,v) in zip(slices,coords):atlas[v:v+h,u:u+w]=layer[z:z+h,x:x+w]
    path.parent.mkdir(exist_ok=True)
    source.indexed(atlas).save(path,optimize=True)
    return coords

def visible_legs(limbs):
    # Front and rear are exact orthographic ray tests through the lower legs.
    # Compare each labelled limb's visible area to its isolated projection.
    masks=np.stack([v[:44]!=0 for v in limbs.values()])
    out={}
    for view,rev in [('front',False),('rear',True)]:
        rays=masks[:,:,:,::-1] if rev else masks
        support=rays.any(-1)
        depths=np.where(support,rays.argmax(-1),NX)
        owner=depths.argmin(0)
        out[view]=[round(float(((owner==i)&support[i]).sum()/support[i].sum()),4) for i in range(4)]
    return out
def run():
    assert hashlib.sha256((source.ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png').read_bytes()).hexdigest()==source.SOURCE
    source.load_drawings()
    for part in PARTS:source.reconstruct(part)
    manifest=json.loads((source.OUT/'manifest.json').read_text())
    results=[]
    for f,pose in enumerate(manifest['poses'],-1):
        revised=np.zeros((NY,NZ,NX),dtype=np.uint8)
        maps,_=source.rig(f)
        # Recompose in the original painter order so intersecting limbs and hide
        # keep the v1 colour ownership. Separately track the actual four limbs.
        oldlegs={k:np.zeros_like(revised) for k in LIMBS}
        legs={k:np.zeros_like(revised) for k in LIMBS}
        oldcrest=np.zeros_like(revised);crest=np.zeros_like(revised)
        for part in PARTS:
            n=part['name'];v,_=source.posed(f,[part]);leg=in_limb(n)
            if leg:
                np.copyto(oldlegs[leg],v,where=v!=0);shift_limb(v,leg,f);np.copyto(legs[leg],v,where=v!=0)
            if n.startswith('crest'):
                np.copyto(oldcrest,v,where=v!=0);restore_spine(v,part,maps[n]);np.copyto(crest,v,where=v!=0)
            np.copyto(revised,v,where=v!=0)
        def pieces(c):return int(label(c>0)[1])
        results.append({'pose':pose['name'],'v1_crest_components_6':pieces(oldcrest),'v2_crest_components_6':pieces(crest),'v1_legs':visible_legs(oldlegs),'v2_legs':visible_legs(legs)})
        for n in (64,128):
            pose['stacks'][str(n)]=write_stack(revised,n,DEST/f'stack-{n}'/(pose['name']+'.png'))
        for n in ('16','32'):del pose['stacks'][n]
    (DEST/'manifest.json').write_text(json.dumps(manifest,separators=(',',':')))
    (EVIDENCE/'morphology.json').write_text(json.dumps(results,indent=1))
if __name__=='__main__':run()
