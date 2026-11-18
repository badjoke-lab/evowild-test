"""Inspect GLB bind-space joints and skin weights (Python 3 + NumPy). No mutation."""
import json
import struct
import sys
from pathlib import Path
import numpy as np


def read_glb(path):
    data = Path(path).read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20+size]), bytearray(data[28+size:])


def accessor(doc, binary, index):
    item = doc['accessors'][index]
    view = doc['bufferViews'][item['bufferView']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[item['type']]
    dtype = {5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[item['componentType']]
    assert 'byteStride' not in view, 'Interleaved accessors need explicit handling'
    return np.frombuffer(binary, dtype=dtype, count=item['count']*width,
                         offset=view.get('byteOffset', 0)+item.get('byteOffset', 0)).reshape(-1, width)


def inspect(path):
    doc, binary = read_glb(path)
    skin = doc['skins'][0]
    matrices = accessor(doc, binary, skin['inverseBindMatrices'])
    attrs = doc['meshes'][0]['primitives'][0]['attributes']
    pos = accessor(doc, binary, attrs['POSITION'])
    joints = accessor(doc, binary, attrs['JOINTS_0'])
    weights = accessor(doc, binary, attrs['WEIGHTS_0'])
    report = []
    for index, node in enumerate(skin['joints']):
        bind = np.linalg.inv(matrices[index].reshape(4, 4).T)
        influence = (weights*(joints == index)).sum(axis=1)
        points = pos[influence > .1]
        report.append({
            'bone': doc['nodes'][node]['name'], 'bindHeadMeshSpace': bind[:3, 3].tolist(),
            'maxWeight': float(influence.max()),
            'weightedMeanMeshSpace': np.average(pos, axis=0, weights=influence).tolist() if influence.sum() else None,
            'weightedBounds': [points.min(axis=0).tolist(), points.max(axis=0).tolist()] if len(points) else None,
        })
    return report


if __name__ == '__main__':
    print(json.dumps(inspect(sys.argv[1]), indent=2))
