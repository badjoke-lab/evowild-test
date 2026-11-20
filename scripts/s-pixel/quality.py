"""Measure published atlas connectivity and the ground contact of painted toes."""
import json, math
import numpy as np
from scipy.ndimage import label
from PIL import Image
from bake import OUT,PARTS,load_drawings,reconstruct,posed,rig,STRIDE,NFRAMES,SX,SY,X,Z,NX,NZ,NY
EVIDENCE=OUT.parent/'evidence'
def quantiles(a):
    return dict(max=round(float(np.max(a)),3),median=round(float(np.median(a)),3),p95=round(float(np.percentile(a,95)),3))
def main():
    m=json.loads((OUT/'manifest.json').read_text())
    result={'unit':'source side drawing units; 3 per longitudinal texel','connectivity':{},'contact':{},'airborne_frames':[]}
    for count in [16,32,64,128]:
        frames=[]
        for p in m['poses']:
            layer=np.zeros((count,NZ,NX),bool)
            atlas=np.asarray(Image.open(OUT/f'stack-{count}'/(p['name']+'.png')))
            for j,(x,z,w,h,u,v) in enumerate(p['stacks'][str(count)]):
                layer[j,z:z+h,x:x+w]=atlas[v:v+h,u:u+w]!=0
            blobs,n=label(layer,np.ones((3,3,3),'u1'))
            sizes=np.bincount(blobs.ravel())[1:]
            frames.append({'pose':p['name'],'islands':int(n-1),'loose_texels':int(sizes.sum()-sizes.max()),'total':int(sizes.sum())})
        result['connectivity'][count]=frames
    result['rendered_clearance_128']=[round(next(i for i,r in enumerate(p['stacks']['128']) if r[2]>0)*SY,4) for p in m['poses'][1:]]
    load_drawings()
    for p in PARTS:reconstruct(p)
    # The sole centroid comes from actual rasterized lower-limb texels in the
    # lowest occupied band. Toe roll can move this centroid relative to its anchor.
    soles={}
    for f in range(NFRAMES):
        _,r=rig(f)
        if not any(v['contact'] for v in r.values()):result['airborne_frames'].append(f)
        for name,foot in r.items():
            if not foot['contact']:continue
            parts=[p for p in PARTS if p['name'].startswith(name) and p['name'][len(name):] in ('inner','outer','ankle')]
            vol,_=posed(f,parts)
            height=int(np.nonzero(vol.any(axis=(1,2)))[0][0])
            zz,xx=np.nonzero(vol[height])
            soles[(f,name)]=(float(X[xx].mean())-385,float(Z[zz].mean()*1.32),height*SY)
    for samples in [12,24]:
        # 8 substeps per held pose, including the next pose boundary. Track the
        # world-space centroid over each uninterrupted pair of support poses.
        for radius in [None,1750]:
            shifts=[];raw=[];gaps=[];inner=0
            def point(x,z,distance):
                if radius is None:return np.array([x-distance,z])
                a=distance/radius;c,s=math.cos(a),math.sin(a)
                return np.array([-radius*s+c*x-s*z,radius*c+s*x+c*z])
            for f in range(0,24,24//samples):
                for name in ['nearF','farF','nearH','farH']:
                    nextf=(f+24//samples)%24
                    if (f,name) not in soles or (nextf,name) not in soles:continue
                    x,z,h=soles[(f,name)];nx,nz,nh=soles[(nextf,name)]
                    start=point(x,z,0)
                    drift=STRIDE/samples
                    for sub in range(1,9):
                        d=drift*sub/8
                        if sub<8:
                            shifts.append(np.linalg.norm(point(x+d,z,d)-start))
                            raw.append(np.linalg.norm(point(x,z,d)-start))
                        else:
                            jump=np.linalg.norm(point(nx,nz,d)-start)
                            shifts.append(jump);raw.append(jump)
                        gaps.append(h);inner+=1
            result['contact'][f'{samples}-'+('straight' if radius is None else 'bend')]={'subsamples':inner,'corrected_displacement':quantiles(shifts),'uncorrected_displacement':quantiles(raw),'max_sole_floor_height':max(gaps)}
    (EVIDENCE/'quality.json').write_text(json.dumps(result,indent=1))
if __name__=='__main__':main()
