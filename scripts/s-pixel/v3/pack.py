"""Pack immutable pose geometry and its indexed 3D paint into two downloads."""
import gzip
import json
from pathlib import Path
import numpy as np

assets = Path(__file__).resolve().parents[3] / 'public/s-pixel-lab/v3/assets'
surface = assets / 'surface'
runtime = assets / 'runtime'
runtime.mkdir(exist_ok=True)
source = json.loads((surface / 'index.json').read_text())
volume = json.loads((assets / 'voxels/index.json').read_text())
shape = tuple(volume['shape'])
lo = np.array(shape)
hi = np.zeros(3, dtype=int)
paints = []
vertices, indices, poses = [], [], []
vertex_offset = index_offset = 0
for pose_id, pose in enumerate(source['poses']):
    name = pose['name']
    paint = np.frombuffer(gzip.decompress((surface / (name+'.paint.gz')).read_bytes()), np.uint8).reshape(shape)
    paints.append(paint)
    for axis in range(3):
        occupied = np.where(paint.any(axis=tuple(i for i in range(3) if i != axis)))[0]
        lo[axis] = min(lo[axis], occupied.min())
        hi[axis] = max(hi[axis], occupied.max()+1)
    levels = {}
    for level in source['levels']:
        mesh = pose['levels'][level]
        data = np.fromfile(surface / mesh['file'], dtype='<u2')
        n, count = mesh['vertices'], mesh['indices']
        assert data.size == n*3+count and data[n*3:].max()<n
        vert = np.empty((n,4),dtype='<u2'); vert[:,:3]=data[:n*3].reshape(-1,3); vert[:,3]=pose_id
        vertices.append(vert); indices.append(data[n*3:].astype('<u4')+vertex_offset)
        levels[level]={'first':index_offset,'count':count}
        vertex_offset+=n; index_offset+=count
    poses.append(levels)
vertices=np.concatenate(vertices).tobytes(); indices=np.concatenate(indices).astype('<u4').tobytes()
(runtime/'geometry.gz').write_bytes(gzip.compress(vertices+indices,compresslevel=6,mtime=0))
region=tuple(slice(int(a),int(b)) for a,b in zip(lo,hi))
(runtime/'paint.gz').write_bytes(gzip.compress(b''.join(p[region].tobytes() for p in paints),compresslevel=6,mtime=0))
(runtime/'index.json').write_text(json.dumps({'poses':poses,'quantization':source['quantization'],'vertexBytes':len(vertices),'indexBytes':len(indices),'paintOriginYZX':lo.tolist(),'paintSizeYZX':(hi-lo).tolist()},separators=(',',':')))
print('Packed',len(poses),'poses;',vertex_offset,'vertices;',index_offset//3,'triangles;', (hi-lo).tolist(),'texture cells per pose')
