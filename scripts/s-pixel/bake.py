"""Build directional drawings, reconstruct their registered parts and bake horizontal atlases."""
from pathlib import Path
import json, math, hashlib, argparse
import numpy as np
from PIL import Image
from artwork import *
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'public/s-pixel-lab/assets'
OUT.mkdir(exist_ok=True,parents=True)
ART=OUT/'drawings'
ART.mkdir(exist_ok=True)
NFRAMES=24
STRIDE=558.0
PERIOD=.72
SOURCE='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'

def indexed(a):
    im=Image.frombytes('P',(a.shape[1],a.shape[0]),a.tobytes())
    im.putpalette(RGB.flatten().tolist()+[0]*(768-RGB.size))
    im.info['transparency']=0
    return im

def end_raster(stations,center,colors):
    width=np.interp(Y,stations[0],stations[1],left=0,right=0)
    rel=np.abs(Z[None,:]-center[:,None])/np.maximum(width[:,None],.01)
    colors=np.array([KEY[k] for k in colors.split()])
    return np.where(rel<=1,colors[np.digitize(rel,[.28,.62,.86])],0).astype('u1')

def draw_planes(p):
    side=p['side']
    s=side>0
    valid=s.any(axis=0)
    stations=p['top']
    w=np.interp(X,*stations,left=0,right=0)
    cx=np.full(NX,p['offset'],dtype=float) if p['center'] is None else np.interp(X,*p['center'])
    # End-elevation centreline: paired vanes flare outward between root and tip.
    centre_end=np.full(NY,p['offset'],float)
    if p['center'] is not None:
        for j,row in enumerate(s):
            if row.any(): centre_end[j]=cx[row].mean()
    topcol,fc,bc=MATERIAL[p['mat']]
    front=end_raster(p['front'],centre_end,fc)
    back=end_raster(p['rear'],centre_end,bc)
    kind=p['mat']
    if p['name']=='neck':kind='neck'
    if p['name'].endswith(('0','1','2')) and p['name'].startswith(('near','far')):kind='limb'
    if kind=='device':kind='cue'
    front=paint_end(front,np.interp(Y,*p['front']),centre_end,kind,False)
    back=paint_end(back,np.interp(Y,*p['rear']),centre_end,kind,True)
    rel=np.abs(Z[:,None]-cx)/np.maximum(w,.01)
    topcols=[KEY[k] for k in topcol.split()]
    top=np.where((rel<=1)&valid,np.take(topcols,np.digitize(rel,[.19,.52,.83])),0).astype('u1')
    return side,top,front,back

def load_drawings():
    names=json.loads((ART/'parts.json').read_text())
    assert names==[p['name'] for p in PARTS]
    for p in PARTS:p['planes']=[]
    for i,k in enumerate(('side','top','front','rear')):
        with Image.open(ART/(k+'-parts.png')) as im:
            assert im.mode=='P'
            sheet=np.asarray(im)
        h=NZ if k=='top' else NY
        w=NX if k in ('side','top') else NZ
        for j,p in enumerate(PARTS):
            r,c=divmod(j,8)
            tile=sheet[r*h:(r+1)*h,c*w:(c+1)*w]
            p['planes'].append(tile if k=='top' else tile[::-1])

def reconstruct(p):
    side,top,front,back=p['planes']
    s=side>0
    valid=s.any(axis=0)
    lo=s.argmax(0)
    hi=len(Y)-1-s[::-1].argmax(0)
    mid=(lo+hi)*.5
    r=np.maximum((hi-lo+1)*.5,.55)
    a=np.abs(np.arange(NY)[:,None]-mid)/r
    stations=p['top']
    w=np.interp(X,*stations,left=0,right=0)
    cx=np.full(NX,p['offset'],dtype=float) if p['center'] is None else np.interp(X,*p['center'])
    rel=np.abs(Z[:,None]-cx)/np.maximum(w,.01)
    # Minor width differences in the two end elevations taper along the part.
    fmask=front>0; bmask=back>0
    start,end=np.nonzero(valid)[0][[0,-1]]
    weight=np.clip((np.arange(NX)-start)/max(end-start,1),0,1)
    def bounds(mask):
        return mask.argmax(1),NZ-1-mask[:,::-1].argmax(1)
    fl,fr=bounds(fmask); bl,br=bounds(bmask)
    left=fl[:,None]*(1-weight)+bl[:,None]*weight
    right=fr[:,None]*(1-weight)+br[:,None]*weight
    zz=np.arange(NZ)[:,None]
    mask=s[:,None,:] & (top>0) & (zz>=left[:,None,:]-.4) & (zz<=right[:,None,:]+.4)
    mask &= (a[:,None,:]**2.65+rel[None,:,:]**2.65)<=1.03
    # Each surface takes paint from the corresponding orthographic drawing.
    # Side clusters extend across the flank; the dorsal ridge and end caps have
    # separate paint. This keeps the face markings readable at oblique angles.
    vol=np.broadcast_to(side[:,None,:],mask.shape).copy()
    upper=(np.arange(NY)[:,None]>mid)
    dorsal=upper[:,None,:] & (a[:,None,:]>.72) & (rel<.72)
    vol=np.where(dorsal & (top>0),top,vol)
    endcaps=(weight<.13)|(weight>.90)
    caps=np.where(weight<.13,front[:,:,None],back[:,:,None])
    vol=np.where(endcaps & (rel<.72) & (caps>0),caps,vol)
    xx=np.arange(NX)
    first=mask.argmax(2)[:,:,None]
    last=NX-1-mask[:,:,::-1].argmax(2)[:,:,None]
    capzone=(rel<.68) & (a[:,None,:]<.88)
    if p['name'].startswith(('crest','tail','ear')):capzone &= False
    vol=np.where((xx<=first+1) & capzone & (front[:,:,None]>0),front[:,:,None],vol)
    vol=np.where((xx>=last-1) & capzone & (back[:,:,None]>0),back[:,:,None],vol)
    # The actual end pixels of the mask carry the head shield, throat facets,
    # and shoulder paint. At pure fore/aft angles these pixels are the portrait.
    if p['name'] in ('face','neck','nearShoulder','farShoulder','nearHip','farHip'):
        vol=np.where((xx==first) & (front[:,:,None]>0),front[:,:,None],vol)
        vol=np.where((xx==last) & (back[:,:,None]>0),back[:,:,None],vol)
    vol=np.where(mask,vol,0).astype('u1')
    if not vol.any(): raise ValueError(p['name'])
    h,z,x=np.nonzero(vol)
    box=(slice(h.min(),h.max()+1),slice(z.min(),z.max()+1),slice(x.min(),x.max()+1))
    p.update(vol=vol[box],box=box,planes=(side,top,front,back))
    return p

def rigid(src,dst,angle):
    c,s=math.cos(angle),math.sin(angle)
    m=np.array([[c,-s],[s,c]])
    return m,np.array(dst)-m@src

def between(a,b,c,d):
    # Stretch only along a bone; its painted transverse width stays fixed.
    v=b-a; u=d-c
    phi=math.atan2(u[1],u[0])-math.atan2(v[1],v[0])
    rotation=rigid(a,c,phi)[0]
    m=rotation@(np.eye(2)+(np.linalg.norm(u)/np.linalg.norm(v)-1)*np.outer(v,v)/np.dot(v,v))
    return m,c-m@a
def transform(tx,pt):return tx[0]@pt+tx[1]
def vec(x,y):return np.array([x,y],float)
def two_link(a,b,l1,l2,sign):
    v=b-a; d=np.linalg.norm(v); unit=v/d
    u=np.clip((d*d+l1*l1-l2*l2)/(2*d),-l1,l1)
    bend=math.sqrt(max(0,l1*l1-u*u))
    return a+unit*u+np.array([-unit[1],unit[0]])*bend*sign
BONES={'F':np.array([[287,283],[332,320],[353,360],[374,451],[353,502]],float),
       'H':np.array([[521,247],[579,326],[637,370],[676,453],[655,502]],float)}
PHASES={'nearF':.46,'farF':.32,'nearH':.06,'farH':.92}
DUTY=.30
def body_motion(t):
    theta=t*math.tau
    return rigid(vec(409,253),vec(409+2*math.sin(theta),248+6*math.cos(2*theta-.6)),.035*math.sin(theta+.1))
def rig(frame):
    idle=frame<0
    t=frame/NFRAMES
    theta=t*math.tau
    body=rigid(vec(0,0),vec(0,0),0) if idle else body_motion(t)
    records={}
    maps={p['name']:body for p in PARTS}
    for side in ('near','far'):
        for family in ('F','H'):
            name=side+family
            p=(t-PHASES[name])%1
            a,b,c,d,toe=BONES[family]
            contact=p<DUTY
            x0=277 if family=='F' else 550
            if idle:
                new_toe=toe.copy() if side=='near' else (vec(221,502) if family=='F' else vec(481,502))
                foot_angle=0
            elif contact:
                new_toe=vec(x0+(p-DUTY/2)*STRIDE,502)
                foot_angle=.26*max(0,(p/DUTY-.64)/.36)
            else:
                q=(p-DUTY)/(1-DUTY)
                # Cubic return has the same endpoint velocity as the support phase.
                ease=q*q*(3-2*q)
                dx=STRIDE*(DUTY*.5+(1-DUTY)*q-ease)
                height=(82 if family=='H' else 76)*math.sin(math.pi*q)**1.55
                new_toe=vec(x0+dx,502-height)
                foot_angle=.28*(1-q)+.87*math.sin(2*math.pi*q)*math.sin(math.pi*q)
            foot=rigid(toe,new_toe,foot_angle)
            ankle=transform(foot,d)
            root=transform(body,a)
            if idle:
                root+=vec(-8,2) if side=='far' else vec(0,0)
            else:
                root+=vec(8*math.sin(math.tau*p),3*math.cos(math.tau*p))
            if idle and side=='near':
                first,second=b,c
            else:
                if idle:
                    first=vec(298,329) if family=='F' else vec(489,325)
                else:
                    # Fore humerus trails the shoulder. The stifle folds forward during recovery.
                    if family=='F':
                        ang=math.radians(69+28*math.sin(math.tau*(p+.03)))
                    else:
                        ang=math.radians(86+36*math.sin(math.tau*(p-.18)))
                    first=root+np.linalg.norm(b-a)*vec(math.cos(ang),math.sin(ang))
                second=two_link(first,ankle,np.linalg.norm(c-b),np.linalg.norm(d-c),1 if family=='F' else -1)
            for j,(s0,s1,d0,d1) in enumerate(zip([a,b,c],[b,c,d],[root,first,second],[first,second,ankle])):
                maps[name+str(j)]=between(s0,s1,d0,d1)
            for suffix in ('ankle','inner','outer'):maps[name+suffix]=foot
            shift=root-transform(body,a)
            # The scapula slides over the rib cage; the upper thigh follows the femur.
            rest=math.atan2((b-a)[1],(b-a)[0])
            turn=math.atan2((first-root)[1],(first-root)[0])-rest
            shell=rigid(a,root,turn*(.30 if family=='F' else .76))
            maps[side+('Shoulder' if family=='F' else 'Hip')]=shell
            records[name]={'contact':bool(contact and not idle),'toe':new_toe.round(3).tolist()}
    if not idle:
        for part in PARTS:
            n=part['name']
            if n.startswith('tail'):
                # One shared hinge keeps pennons attached to the caudal stem.
                maps[n]=rigid(vec(525,222),transform(body,vec(525,222)),.035*math.sin(theta+.1)+.065*math.sin(theta-.9))
            if n in ('face','neck') or n.startswith(('crest','cue','ear')):
                maps[n]=rigid(vec(256,250),transform(body,vec(256,250)),.035*math.sin(theta+.1)-.022*math.sin(theta-.3))
    return maps,records

def posed(frame,parts=None):
    out=np.zeros((NY,NZ,NX),dtype='u1')
    maps,record=rig(frame)
    for p in PARTS if parts is None else parts:
        mat,delta=maps[p['name']]
        h,z,x=p['box']
        # Inverse-map every destination texel to prevent forward-splat holes.
        xx=[X[x.start]-SX,X[x.stop-1]+SX]
        yy=[Y[h.start]+SY,Y[h.stop-1]-SY]
        cs=np.array([mat@vec(i,j)+delta for i in xx for j in yy])
        xi=np.flatnonzero((X>=cs[:,0].min())&(X<=cs[:,0].max()))
        yi=np.flatnonzero((Y>=cs[:,1].min())&(Y<=cs[:,1].max()))
        if not len(xi) or not len(yi):continue
        ys,xs=np.meshgrid(Y[yi],X[xi],indexing='ij')
        local=np.linalg.inv(mat)@(np.stack([xs,ys]).reshape(2,-1)-delta[:,None])
        lx=np.rint((local[0]-X[0])/SX).astype(int).reshape(xs.shape)-x.start
        lh=np.rint((Y[0]-local[1])/SY).astype(int).reshape(xs.shape)-h.start
        vol=p['vol']
        valid=(lx>=0)&(lh>=0)&(lx<vol.shape[2])&(lh<vol.shape[0])
        pixels=vol[lh.clip(0,vol.shape[0]-1),:,lx.clip(0,vol.shape[2]-1)].transpose(0,2,1)
        dst=out[yi[0]:yi[-1]+1,z,xi[0]:xi[-1]+1]
        np.copyto(dst,pixels,where=(pixels>0)&valid[:,None,:])
    return out,record

def project(vol,axis,reverse):
    arr=np.moveaxis(vol,axis,0)
    if reverse:arr=arr[::-1]
    return np.take_along_axis(arr,(arr>0).argmax(0)[None],axis=0)[0]
def extract_drawings():
    # Unoccluded authored planes are retained as indexed PNGs for every part.
    # Front, rear and side are stored with the upright origin at the top.
    for i,k in enumerate(('side','top','front','rear')):
        planes=[p['planes'][i] for p in PARTS]
        h,w=planes[0].shape
        sheet=np.zeros((((len(planes)+7)//8)*h,w*8),dtype='u1')
        for j,pl in enumerate(planes):
            row,col=divmod(j,8)
            sheet[row*h:(row+1)*h,col*w:(col+1)*w]=pl if i==1 else pl[::-1]
        indexed(sheet).save(ART/(k+'-parts.png'),optimize=True)
    (ART/'parts.json').write_text(json.dumps([p['name'] for p in PARTS],indent=1))
def main():
    reference=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
    assert hashlib.sha256(reference.read_bytes()).hexdigest()==SOURCE
    parser=argparse.ArgumentParser()
    parser.add_argument('--from-drawings',action='store_true',help='Keep edited indexed source PNGs')
    if not parser.parse_args().from_drawings:
        for p in PARTS:p['planes']=draw_planes(p)
        extract_drawings()
    load_drawings()
    for p in PARTS:reconstruct(p)
    meta={'x0':X0,'z0':Z0*1.32,'sx':SX,'sz':SZ*1.32,'height':H,'nx':NX,'nz':NZ,'frames':NFRAMES,
          'stride':STRIDE,'period':PERIOD,'palette':['#'+v for v in PALETTE.values()],'poses':[]}
    meta['poses']=[None]*(NFRAMES+1)
    for f in [-1,*range(0,NFRAMES,2),*range(1,NFRAMES,2)]:
        vol,record=posed(f)
        entry={'name':'idle' if f<0 else f'run-{f:02}','feet':record,'stacks':{}}
        for count in (16,32,64,128):
            band=NY//count
            # Sample the centre plane of exactly N height bands; walls extend to
            # band edges. Crop transparent margins per tile, preserving origin.
            bands=vol.reshape(count,band,NZ,NX)
            layers=bands[:,band//2].copy()
            # A thin diagonal sweep can miss the midplane. Retain its footprint
            # over the band using the nearest painted sample at that x,z.
            for j in sorted(range(band),key=lambda j:abs(j+.5-band/2)):
                np.copyto(layers,bands[:,j],where=(layers==0)&(bands[:,j]>0))
            rects=[]; tiles=[]
            for layer in layers:
                z,x=np.nonzero(layer)
                if not len(x):
                    rects.append([0,0,0,0]); tiles.append(None);continue
                a,b,c,d=int(x.min()),int(z.min()),int(x.max()+1),int(z.max()+1)
                rects.append([a,b,c-a,d-b]);tiles.append(layer[b:d,a:c])
            aw=1024; u=v=line=0
            for rect in rects:
                w,h=rect[2:]
                if u+w>aw:u=0;v+=line;line=0
                rect.extend([u,v]);u+=w;line=max(line,h)
            atlas=np.zeros((v+line,aw),dtype='u1')
            for rect,tile in zip(rects,tiles):
                if tile is None:continue
                x,z,w,h,u,v=rect
                atlas[v:v+h,u:u+w]=tile
            path=f'stack-{count}/{entry["name"]}.png'
            (OUT/path).parent.mkdir(exist_ok=True)
            indexed(atlas).save(OUT/path,optimize=True)
            entry['stacks'][count]=rects
        if f<0:
            for name,axis,rev in [('side',1,True),('top',0,True),('front',2,False),('rear',2,True)]:
                plane=project(vol,axis,rev)
                if axis!=0:plane=plane[::-1]
                if name=='rear':plane=plane[:,::-1]
                indexed(plane.copy()).save(ART/(name+'.png'))
        meta['poses'][f+1]=entry
    (OUT/'manifest.json').write_text(json.dumps(meta,separators=(',',':')))
if __name__=='__main__':main()
