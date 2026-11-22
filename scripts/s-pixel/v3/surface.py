"""Build three paint-independent, indexed external surfaces for each S-01 pose.

vtkImageData describes samples at voxel *centres*. The half-cell origin and
one-cell air border are important for both toe contact and shell alignment.
Run from any directory with numpy, scipy and VTK 9 installed.
"""
import gzip
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
os.environ.setdefault('VTK_SMP_MAX_THREADS', '2')
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy

ASSETS = Path(__file__).resolve().parents[3] / 'public/s-pixel-lab/v3/assets'
SOURCE = ASSETS / 'voxels'
DEST = ASSETS / 'surface'
LEVELS = {'fine': 2600, 'race': 1400, 'mid': 650}
QUANTIZATION = 64


def extract_shell(solid, isovalue=.48):
    # Occupancy topology comes from the source even where the crest is one cell
    # thick. Limit the filtered field so every solid centre remains inside.
    # Storage in VTK's native x-fastest, then y, then z order.
    samples = np.pad(solid.transpose(1, 0, 2), 1).astype(np.float32)
    filtered = ndimage.gaussian_filter(samples, .6)
    field = np.clip(filtered, .61 * samples, .39 + .61 * samples)
    image = vtk.vtkImageData()
    image.SetDimensions(*field.shape[::-1])
    image.SetOrigin(-.5, -.5, -.5)
    image.GetPointData().SetScalars(numpy_to_vtk(field.ravel(), deep=True))
    surface = vtk.vtkFlyingEdges3D()
    surface.SetInputData(image)
    surface.SetValue(0, isovalue)
    surface.ComputeNormalsOff()
    surface.ComputeScalarsOff()
    surface.Update()
    return surface.GetOutput()


def endpoint_locks(solid, points):
    # At each end of the long and vertical axes, separate the terminal branches.
    # This finds the two crest ends and individual feet even during suspension.
    # Pin their boundary samples so an edge collapse cannot pull them inwards.
    xyz = solid.transpose(2, 0, 1)
    occupied = np.array(np.where(xyz))
    lo, hi = occupied.min(axis=1), occupied.max(axis=1)
    nearest = cKDTree(points)
    locked = np.zeros(len(points), dtype=np.uint8)
    for axis, sign, fraction in ((0, -1, .10), (0, 1, .12), (1, -1, .40), (1, 1, .16)):
        coords = np.arange(xyz.shape[axis]).reshape([xyz.shape[axis] if j == axis else 1 for j in range(3)])
        depth = (hi[axis] - lo[axis]) * fraction
        band = coords >= hi[axis] - depth if sign > 0 else coords <= lo[axis] + depth
        labels, components = ndimage.label(xyz & band, np.ones((3, 3, 3), dtype=bool))
        for i, bounds in enumerate(ndimage.find_objects(labels), 1):
            if bounds is None:
                continue
            cells = np.stack(np.where(labels[bounds] == i), axis=1) + [s.start for s in bounds]
            end = (cells[:, axis] * sign).max()
            cap = cells[cells[:, axis] * sign >= end - 1] + .5
            for direction in range(3):
                for side in (-1, 1):
                    # A genuine cap sample rather than the mean of disconnected
                    # cells keeps a forked toe or feather from pinching together.
                    point = cap[np.argmax(side * cap[:, direction])].copy()
                    point[direction] += .4 * side
                    locked[nearest.query(point)[1]] = 1
    return locked


def reduce_levels(surface, solid, steps):
    points = vtk_to_numpy(surface.GetPoints().GetData())
    faces = vtk_to_numpy(surface.GetPolys().GetConnectivityArray()).astype('<u4')
    locks = endpoint_locks(solid, points)
    # World-space scales keep lateral/vertical error comparable to length.
    positions = (points * np.asarray(steps, dtype=np.float32)).astype('<f4')
    result = subprocess.run(
        ['node', str(Path(__file__).with_name('simplify.mjs')), str(len(points)), str(len(faces)),
         *[str(n) for n in LEVELS.values()]],
        input=positions.tobytes() + faces.tobytes() + locks.tobytes(),
        stdout=subprocess.PIPE, check=True,
    )
    data = np.frombuffer(result.stdout, '<u4')
    levels = {}
    offset = 0
    for level in LEVELS:
        size = int(data[offset])
        levels[level] = data[offset + 1:offset + size + 1].reshape(-1, 3)
        offset += size + 1
    assert offset == len(data)
    return points, levels, int(locks.sum())


def save_mesh(points, triangles, name, source_shape):
    points = points.copy()
    # Quantization never extends a foot under the source ground plane.
    ny, nz, nx = source_shape
    np.clip(points, [0, 0, 0], [nx, ny, nz], out=points)
    points = np.rint(points * QUANTIZATION).astype('<u2')
    # VTK can split vertices at a shared point in the middle-distance LOD.
    # A single position stream and per-fragment paint allow welding all of them.
    used, triangle_local = np.unique(triangles, return_inverse=True)
    vertices, mapping = np.unique(points[used], axis=0, return_inverse=True)
    triangles = mapping[triangle_local.reshape(-1, 3)]
    nonzero = (triangles[:, 0] != triangles[:, 1]) & (triangles[:, 0] != triangles[:, 2]) & (triangles[:, 1] != triangles[:, 2])
    triangles = triangles[nonzero]
    if len(vertices) > 65535:
        raise ValueError('Surface exceeds 16-bit index capacity')
    with (DEST / name).open('wb') as output:
        output.write(vertices.tobytes())
        output.write(triangles.astype('<u2').tobytes())
    q = vertices[triangles].astype(np.float64) / QUANTIZATION
    volume = float(np.einsum('ij,ij->i', q[:, 0], np.cross(q[:, 1], q[:, 2])).sum() / 6)
    return {'file': name, 'vertices': len(vertices), 'indices': triangles.size, 'volumeInCells': round(volume, 2)}


def paint_extension(volume, name):
    # Move only lookup coordinates. Every stored nonzero value is copied from
    # an exposed source texel. At oblique angles a curved triangle can cross
    # several exposed voxel colours without any geometry split.
    solid = volume != 0
    boundary = solid & ~ndimage.binary_erosion(solid)
    indices = ndimage.distance_transform_edt(~boundary, return_distances=False, return_indices=True)
    paint = volume[tuple(indices)]
    reachable = ndimage.binary_dilation(solid, iterations=7)
    paint[~reachable] = 0
    with (DEST / name).open('wb') as output:
        with gzip.GzipFile(fileobj=output, filename='', mode='wb', mtime=0, compresslevel=6) as stream:
            stream.write(paint.tobytes())


def run():
    DEST.mkdir(exist_ok=True, parents=True)
    meta = json.loads((SOURCE / 'index.json').read_text())
    output = {'quantization': QUANTIZATION, 'levels': list(LEVELS), 'poses': []}
    for pose in meta['poses']:
        name = pose['name']
        raw = gzip.decompress((SOURCE / pose['file']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == pose['sha256']
        volume = np.frombuffer(raw, np.uint8).reshape(meta['shape'])
        solid = ndimage.binary_fill_holes(volume != 0)
        surface = extract_shell(solid)
        lods = {}
        points, levels, anchors = reduce_levels(surface, solid, meta['stepXYZ'])
        for level in LEVELS:
            lods[level] = save_mesh(points, levels[level], name + '-' + level + '.bin', volume.shape)
        for lod in lods.values():
            lod['volumeRatio'] = round(lod['volumeInCells'] / int(solid.sum()), 4)
            if not .82 < lod['volumeRatio'] < 1.12:
                raise ValueError(f"{name}: excessive volume change {lod}")
        paint = name + '.paint.gz'
        paint_extension(volume, paint)
        output['poses'].append({'name': name, 'paint': paint, 'levels': lods,
                                'sourceSha256': pose['sha256'], 'lockedVertices': anchors, 'contourTriangles': surface.GetNumberOfCells(),
                                'enclosedAirCells': int(solid.sum() - np.count_nonzero(volume))})
        print(name, [lod['indices'] // 3 for lod in lods.values()], flush=True)
    (DEST / 'index.json').write_text(json.dumps(output, indent=1) + '\n')


if __name__ == '__main__':
    run()
