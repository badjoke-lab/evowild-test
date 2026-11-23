"""Fit the existing surface LODs to the exterior faces of the frozen voxel poses."""
from pathlib import Path
import gzip
import hashlib
import json
import subprocess
import sys
import numpy as np
from scipy import ndimage

here = Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'v3'))
from surface import endpoint_locks
root = here.parents[2]/'public/s-pixel-lab'
source = root/'v3/assets/voxels'
meta = json.loads((source/'index.json').read_text())
index = json.loads((root/'v3/assets/runtime/index.json').read_text())
dest = root/'v4.1/assets'
dest.mkdir(parents=True,exist_ok=True)
step = np.asarray(meta['stepXYZ'], dtype=np.float32)
levels = {'fine':3200,'race':1180,'mid':820}


def exterior(solid):
    # A voxel occupies [i,i+1] on each axis, as in the 128-section reference.
    body = solid.transpose(2,0,1)
    corners = []
    for axis in range(3):
        tangents = np.roll(np.eye(3,dtype=int),-axis,axis=0)
        n,u,v = tangents
        padded = np.pad(body,1)
        for sign in (-1,1):
            offset = n*sign+1
            adjacent = padded[tuple(slice(a,a+l) for a,l in zip(offset,body.shape))]
            cell = np.argwhere(body & ~adjacent) + (n if sign>0 else 0)
            delta = [0*u,u,u+v,v] if sign>0 else [0*u,v,u+v,u]
            corners.append(cell[:,None,:]+np.asarray(delta)[None,:,:])
    positions, ids = np.unique(np.concatenate(corners).reshape(-1,3),axis=0,return_inverse=True)
    quads = ids.reshape(-1,4)
    return positions,quads[:,[0,1,2,0,2,3]].ravel().astype('<u4')


vertices, faces, poses = [], [], []
nv = ni = 0
for pose_id,pose in enumerate(meta['poses']):
    raw=gzip.decompress((source/pose['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==pose['sha256']
    solid=ndimage.binary_fill_holes(np.frombuffer(raw,'u1').reshape(meta['shape'])!=0)
    xyz, indices=exterior(solid)
    bounds=(xyz.min(axis=0),xyz.max(axis=0))
    locks=endpoint_locks(solid,xyz)
    # Keep supports across both crest branches and the lower feet in all LODs.
    y=xyz[:,1]; span=y.max()-y.min()
    for selected,pitch in [(y>y.max()-.24*span,8),(y<y.min()+.13*span,13)]:
        ids=np.flatnonzero(selected)
        for sign in (-1,1):
            order=np.argsort(sign*xyz[ids,2],kind='stable')
            _,first=np.unique(xyz[ids[order]]//pitch,axis=0,return_index=True)
            locks[ids[order[first]]]=1
    # Remove subvoxel staircase noise on the trunk and limbs before fitting.
    # Keep the original cube corners on the paired crest and sole endpoints.
    faces3=indices.reshape(-1,3)
    edges=np.unique(np.sort(np.concatenate((faces3[:,[0,1]],faces3[:,[1,2]],faces3[:,[2,0]])),axis=1),axis=0)
    edges=edges[(np.abs(xyz[edges[:,0]]-xyz[edges[:,1]]).sum(axis=1)==1)]
    start,end=np.concatenate((edges,edges[:,::-1])).T
    degree=np.maximum(1,np.bincount(start,minlength=len(xyz)))[:,None]
    smooth=xyz.astype(float)
    for weight in [0.48,-0.5]*8:
        total=np.column_stack([np.bincount(start,weights=smooth[end,k],minlength=len(xyz)) for k in range(3)])
        smooth+=weight*(total/degree-smooth)
    blend=np.clip((y.max()-.22*span-y)/(.13*span),0,1)
    blend[locks!=0]=0
    xyz=xyz+(smooth-xyz)*blend[:,None]
    world=(xyz*step).astype('<f4')
    data=subprocess.run(['node',str(here.parent/'v4/reduce.mjs'),str(len(xyz)),str(len(indices)),*map(str,levels.values())],
                        input=world.tobytes()+indices.tobytes()+locks.tobytes(),stdout=subprocess.PIPE,check=True).stdout
    data=np.frombuffer(data,'<u4'); start=0; parts={}
    for level in levels:
        count=int(data[start]); start+=1
        fitted=data[start:start+xyz.size].view('<f4').reshape(-1,3)/step; start+=xyz.size
        used,local=np.unique(data[start:start+count],return_inverse=True); start+=count
        # Clamp against the integer occupancy envelope captured BEFORE filtering.
        # Slightly negative sole coordinates would otherwise wrap to y=65535.
        assert np.isfinite(fitted[used]).all()
        scaled=np.rint(np.clip(fitted[used],*bounds)*index['quantization'])
        assert scaled.min()>=0 and scaled.max()<=np.iinfo(np.uint16).max
        coords=scaled.astype('<u2')
        assert (coords>=bounds[0]*index['quantization']).all() and (coords<=bounds[1]*index['quantization']).all()
        vertices.append(np.column_stack((coords,np.full(len(coords),pose_id,'<u2'))))
        faces.append((local+nv).astype('<u4')); parts[level]={'first':ni,'count':count}
        ni+=count;nv+=len(coords)
    assert start==len(data)
    poses.append(parts)
vb=np.concatenate(vertices).tobytes(); ib=np.concatenate(faces).tobytes()
index.update(poses=poses,vertexBytes=len(vb),indexBytes=len(ib))
(dest/'index.json').write_text(json.dumps(index,separators=(',',':'))+'\n')
(dest/'geometry.gz').write_bytes(gzip.compress(vb+ib,compresslevel=6,mtime=0))
