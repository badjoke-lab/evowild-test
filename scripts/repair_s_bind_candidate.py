"""Isolated S bind/weight candidate. Original GLB and mesh attributes stay unchanged.
Run with Python 3 + NumPy. This is a review asset, never a production manifest update.
"""
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from inspect_s_glb_skin import read_glb, accessor, inspect

SOURCE = Path('public/models/evowild-s/focus-rigged-v5.glb')
OUTPUT = Path('public/models/evowild-s/review/focus-bind-repair-v1.glb')
REPORT = Path('docs/2p5d/evidence/20261026-s-bind-repair/asset-report.json')


def multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw*bx+ax*bw+ay*bz-az*by, aw*by-ax*bz+ay*bw+az*bx,
                     aw*bz+ax*by-ay*bx+az*bw, aw*bw-ax*bx-ay*by-az*bz])


def build():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'e879cae6835f405f93787b96dfbcc1858ff540dadaf12988d549d56d922362a2', 'Unexpected source: review alignment before rebuilding'
    doc, binary = read_glb(SOURCE)
    attrs = doc['meshes'][0]['primitives'][0]['attributes']
    preserved = {name: accessor(doc, binary, index).tobytes() for name, index in attrs.items()
                 if name not in ('JOINTS_0', 'WEIGHTS_0')}
    indices = doc['meshes'][0]['primitives'][0]['indices']
    original_indices = accessor(doc, binary, indices).tobytes()
    skin = doc['skins'][0]
    names = [doc['nodes'][index]['name'] for index in skin['joints']]
    ibm = accessor(doc, binary, skin['inverseBindMatrices'])
    bind = np.array([np.linalg.inv(m.reshape(4, 4).T) for m in ibm])
    # Source root is at mesh-bounds center. Rotate skeleton about that pivot,
    # not mesh vertices: Rx(+90deg), then Ry(180deg). +Y becomes up, head +Z.
    rotation = np.array([[-1., 0, 0], [0, 0, -1], [0, -1, 0]])
    pivot = bind[names.index('root'), :3, 3].copy()
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = pivot-rotation@pivot
    corrected = transform@bind
    for i, m in enumerate(corrected):
        ibm[i] = np.linalg.inv(m).T.reshape(16)
    root = skin['joints'][names.index('root')]
    node = doc['nodes'][root]
    root_origin = np.array(node['translation'])
    # Quaternion equivalent to the proper rotation above (det=+1, no mirror).
    q = np.array([0., 2**-.5, -2**-.5, 0.])
    node['rotation'] = multiply(q, node['rotation']).tolist()
    for animation in doc['animations']:
        for channel in animation['channels']:
            if channel['target']['node'] != root:
                continue
            values = accessor(doc, binary, animation['samplers'][channel['sampler']]['output'])
            if channel['target']['path'] == 'rotation':
                values[:] = [multiply(q, value) for value in values]
            elif channel['target']['path'] == 'translation':
                values[:] = (values-root_origin)@rotation.T+root_origin
    # Rebuild weights in the corrected mesh/bind coordinate space. Nearest
    # anatomical chain segments are a first candidate, not hand-painted approval.
    pos = accessor(doc, binary, attrs['POSITION'])
    joints = accessor(doc, binary, attrs['JOINTS_0'])
    weights = accessor(doc, binary, attrs['WEIGHTS_0'])
    head = {name: corrected[i, :3, 3] for i, name in enumerate(names)}
    ends = {'pelvis': 'spine', 'spine': 'chest', 'chest': 'neck', 'neck': 'head'}
    for leg in ['fore_L', 'fore_R', 'hind_L', 'hind_R']:
        ends[leg+'_upper'] = leg+'_lower'
        ends[leg+'_lower'] = leg+'_foot'
    distance = np.full((len(pos), len(names)), 100.)
    for i, name in enumerate(names):
        if name == 'root':
            continue
        a = head[name]
        if name in ends:
            b = head[ends[name]]
        elif name.endswith('_foot'):
            b = a+np.array([0, 0, .14])
        elif name == 'head':
            b = a+np.array([0, .1, .25])
        else:  # Tail points rearward from the pelvis.
            b = a+np.array([0, -.08, -.45])
        ab = b-a
        t = np.clip(((pos-a)@ab)/(ab@ab), 0, 1)
        distance[:, i] = np.linalg.norm(pos-(a+t[:, None]*ab), axis=1)
        if name.startswith(('fore_', 'hind_')):
            # Avoid weights crossing between contralateral narrow legs.
            wrong_side = (pos[:, 0]-pivot[0])*(a[0]-pivot[0]) < -.0005
            distance[wrong_side, i] += .5
    closest = np.argsort(distance, axis=1)[:, :4]
    d = np.take_along_axis(distance, closest, axis=1)
    w = 1/(d+.015)**4
    w /= w.sum(axis=1, keepdims=True)
    joints[:] = closest
    weights[:] = w
    # Byte-exact geometry invariants: no shape, topology, normal, UV edits.
    for name, original in preserved.items():
        assert accessor(doc, binary, attrs[name]).tobytes() == original, name
    assert accessor(doc, binary, indices).tobytes() == original_indices
    encoded = json.dumps(doc, separators=(',', ':')).encode()
    encoded += b' '*((-len(encoded)) % 4)
    binary += b'\0'*((-len(binary)) % 4)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(encoded)+len(binary))+
                       struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+
                       struct.pack('<II', len(binary), 0x004e4942)+binary)
    report = {'status': 'REVISE_ISOLATED_BIND_WEIGHT_CANDIDATE', 'source': str(SOURCE),
              'output': str(OUTPUT), 'sourceSHA256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'outputSHA256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              'preservedGeometrySHA256': {k: hashlib.sha256(v).hexdigest() for k, v in preserved.items()},
              'indicesSHA256': hashlib.sha256(original_indices).hexdigest(),
              'vertices': len(pos), 'rotationDeterminant': float(np.linalg.det(rotation)),
              'pivotMeshSpace': pivot.tolist(), 'bones': inspect(OUTPUT)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'bones'}, indent=2))


if __name__ == '__main__':
    build()
