"""Build the three surface LODs from the pinned v3 occupancy. Paint stays shared."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage
from vtk.util.numpy_support import vtk_to_numpy

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'v3'))
import surface

dest = surface.ASSETS.parent.parent / 'v4/assets'
dest.mkdir(exist_ok=True, parents=True)
source = json.loads((surface.SOURCE / 'index.json').read_text())
index = json.loads((surface.ASSETS / 'runtime/index.json').read_text())
levels = {'fine': 3200, 'race': 930}
legacy = json.loads((surface.ASSETS / 'surface/index.json').read_text())


def feature_locks(solid, xyz):
    locks = surface.endpoint_locks(solid, xyz)
    # Preserve boundary points along both sides of each crest and foot, even
    # away from the terminal cap. One support per spatial cell and orientation.
    y = xyz[:, 1]
    lo, hi = y.min(), y.max()
    for mask, pitch in [(y > hi - .09 * (hi - lo), 10), (y < lo + .095 * (hi - lo), 12)]:
        ids = np.flatnonzero(mask)
        cells = (xyz[ids] / pitch).astype(int)
        # Separate left and right sides. Pin outward support on each flank.
        sign = np.sign(xyz[ids, 2] - xyz[:, 2].mean())
        order = np.argsort(-sign * xyz[ids, 2], kind='stable')
        _, first = np.unique(cells[order], axis=0, return_index=True)
        locks[ids[order[first]]] = 1
    return locks


vertices, indices, poses, detail = [], [], [], []
manifest = json.loads((surface.ASSETS / 'manifest.json').read_text())
nv = ni = 0
def pack_surface(q, local, pose_id, base):
    # Each pose has a paint margin in x/z. Safe to interpolate the atlas
    # coordinates in the vertex shader without crossing adjacent poses.
    lower = np.array(index['paintOriginYZX'])[[2, 1]] * index['quantization']
    upper = lower + np.array(index['paintSizeYZX'])[[2, 1]] * index['quantization']
    assert (q[:, [0,2]] >= lower).all() and (q[:, [0,2]] < upper).all()
    # V3 differentiates undeformed paint coordinates. Store the static face
    # lighting on the provoking vertex and the contact weight on every vertex.
    points = q.astype(float) / index['quantization'] * source['stepXYZ'] + source['originXYZ']
    feet = manifest['poses'][pose_id]['feet']
    contact = np.array([feet[k]['contact'] for k in ('nearF', 'farF', 'nearH', 'farH')])
    limb = 2*(points[:, 0]>=35).astype(int)+(points[:, 2]<=0)
    t = np.clip((points[:, 1]-54)/116, 0, 1)
    support = (1-t*t*(3-2*t))*contact[limb]
    tris = local.reshape(-1, 3)
    corners = points[tris]
    n = np.cross(corners[:, 1]-corners[:, 0], corners[:, 2]-corners[:, 0])
    w = np.abs(n)
    lighting = np.where(n>0, [0.89, 1.04, 1.0], [0.95, 0.78, 0.88])
    shade = (w*lighting).sum(axis=1)/np.maximum(w.sum(axis=1), 1e-10)
    attributes = np.zeros(tris.shape, dtype='u1')
    attributes[:, 2] = np.clip(np.rint((shade-.75)*800), 0, 255)
    keys = np.column_stack((local, attributes.ravel()))
    unique, remap = np.unique(keys, axis=0, return_inverse=True)
    pos = unique[:, 0]
    vertex = np.empty((len(pos), 4), '<u2')
    vertex[:, :3], vertex[:, 3] = q[pos], pose_id
    aux = np.column_stack((unique[:, 1:], np.rint(255*support[pos]))).astype('u1')
    detail.append(aux)
    vertices.append(vertex)
    indices.append((remap + base).astype('<u4'))
    return len(pos), len(remap)


for pose_id, pose in enumerate(source['poses']):
    raw = gzip.decompress((surface.SOURCE / pose['file']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == pose['sha256']
    volume = np.frombuffer(raw, 'u1').reshape(source['shape'])
    solid = ndimage.binary_fill_holes(volume != 0)
    # Preserve the unsmoothed high-resolution shell at portrait distance.
    # At race size, a broader occupancy interpolant avoids wasting triangles on
    # subpixel voxel steps. All three levels keep occupied / empty centres apart.
    parts = {}
    for level, budget in levels.items():
        fine = level == 'fine'
        shell = surface.extract_shell(solid, .48 if fine else .405)
        if not fine:
            smooth = surface.vtk.vtkWindowedSincPolyDataFilter()
            smooth.SetInputData(shell)
            smooth.SetNumberOfIterations(20)
            smooth.SetPassBand(.06)
            smooth.NormalizeCoordinatesOn()
            smooth.FeatureEdgeSmoothingOff()
            smooth.Update()
            shell = smooth.GetOutput()
        xyz = vtk_to_numpy(shell.GetPoints().GetData())
        faces = vtk_to_numpy(shell.GetPolys().GetConnectivityArray()).astype('<u4')
        locks = feature_locks(solid, xyz)
        positions = (xyz * np.array(source['stepXYZ'], dtype='f4')).astype('<f4')
        output = subprocess.run(['node', str(here / 'reduce.mjs'),
                                 str(len(xyz)), str(len(faces)), str(budget)],
                                input=positions.tobytes()+faces.tobytes()+locks.tobytes(),
                                capture_output=True, check=True)
        result = np.frombuffer(output.stdout, '<u4')
        offset = 0
        count = int(result[offset])
        offset += 1
        fit = result[offset:offset+xyz.size].view('<f4').reshape(-1, 3)/source['stepXYZ']
        offset += xyz.size
        used, local = np.unique(result[offset:offset+count], return_inverse=True)
        offset += count
        q = np.rint(np.clip(fit[used], xyz.min(axis=0).clip(0), xyz.max(axis=0)) * index['quantization']).astype('<u2')
        n, count = pack_surface(q, local, pose_id, nv)
        parts[level] = dict(first=ni, count=count)
        nv += n
        ni += count
        assert offset == len(result)
    # Preserve the v3 silhouette through the sprite handover. The candidate
    # midsize fit reduced crest overlap on the single-sample race framebuffer.
    mid = legacy['poses'][pose_id]['levels']['mid']
    raw = np.fromfile(surface.ASSETS/'surface'/mid['file'], dtype='<u2')
    end = mid['vertices']*3
    n, count = pack_surface(raw[:end].reshape(-1, 3), raw[end:], pose_id, nv)
    parts['mid'] = dict(first=ni, count=count)
    nv += n
    ni += count
    poses.append(parts)
    print(pose['name'], int(locks.sum()), [p['count']//3 for p in parts.values()], flush=True)

vb = np.concatenate(vertices).tobytes()
ib = np.concatenate(indices).tobytes()
index.update(poses=poses, vertexBytes=len(vb), indexBytes=len(ib))
(dest/'detail.gz').write_bytes(gzip.compress(np.concatenate(detail).tobytes(), compresslevel=6, mtime=0))
(dest/'geometry.gz').write_bytes(gzip.compress(vb+ib, compresslevel=6, mtime=0))
(dest/'index.json').write_text(json.dumps(index, separators=(',', ':'))+'\n')
