"""Record preserved support control, protected assets, limb bulk and live runs."""
import csv
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

root = Path('docs/evidence/p-rig-v4-20261014')
baseline = '6025245731c2484bfaab5e2817f06cc8e804716a'
old, new = [Path('public/concept/p-layered-'+v) for v in ['v3', 'v4']]
a, b = [json.loads((p/'atlas.json').read_text()) for p in [old, new]]
prior = (root/'v3-snapshot/p_layered.js').read_text()
current = Path('src/p_layered.js').read_text()
def digest(data): return hashlib.sha256(data).hexdigest()
def block(text, start, end): return text[text.index(start):text.index(end)]
controls = {}
for name, start, end in [
    ('gaitConstants', 'const TAU', 'const states'),
    ('laneConstraint', 'export function constrainPLayeredLane', 'function joint('),
    ('fixedBoneIK', 'function solve(', 'function segment('),
    ('groundProjection', 'function laneForY', 'export function drawPLayered'),
    ('stancePlanner', 'export function drawPLayered', '      const u=(local-DUTY)'),
    ('reachBodyAndIK', '    f.stance=stance;', '  const drawBody=')]:
    x, y = [block(t, start, end) for t in [prior, current]]
    assert x == y, name
    controls[name] = {'unchanged': True, 'sha256': digest(y.encode())}
for key in ['bones', 'body', 'frame']:
    assert a[key] == b[key], key
assert b['parts']['body']['jointCalibration'] == {
    'shoulder': a['parts']['body']['shoulder'], 'hip': a['parts']['body']['hip'],
    'width': a['parts']['body']['crop'][2]}
for name in ['fore-foot', 'hind-foot', 'fore-paw', 'hind-paw', 'fore-far-paw', 'hind-far-paw']:
    assert a['parts'][name] == b['parts'][name], name
    assert (old/a['parts'][name]['image']).read_bytes() == (new/b['parts'][name]['image']).read_bytes(), name
protected = {}
for path in subprocess.check_output(['git','ls-tree','-r','--name-only',baseline,'public'],text=True).splitlines():
    reference = subprocess.check_output(['git','show',baseline+':'+path])
    actual = Path(path).read_bytes()
    assert reference == actual, path
    protected[path] = digest(actual)

def section_width(part, directory, length):
    alpha = np.array(Image.open(directory/part['image']).convert('RGBA'))[:, :, 3]
    p, q = np.array(part['a']), np.array(part['b'])
    distance = np.linalg.norm(q-p)
    normal, mid = np.array([-(q-p)[1],(q-p)[0]])/distance, (p+q)/2
    offsets = []
    for offset in np.arange(-max(alpha.shape),max(alpha.shape),.5):
        x, y = np.rint(mid+normal*offset).astype(int)
        if 0 <= y < alpha.shape[0] and 0 <= x < alpha.shape[1] and alpha[y,x] > 128:
            offsets.append(offset)
    return (max(offsets)-min(offsets)+.5)*length/distance
anatomy = {kind:{version:{'boneLength':68,'alphaMidsectionWidth':section_width(atlas['parts'][kind+'-lower'],directory,68)}
                 for version,atlas,directory in [('v3',a,old),('v4',b,new)]} for kind in ['fore','hind']}
for kind in anatomy:
    assert anatomy[kind]['v4']['alphaMidsectionWidth'] >= anatomy[kind]['v3']['alphaMidsectionWidth']
(root/'control-and-asset-preservation.json').write_text(json.dumps({
    'baseline':baseline,'controlCode':controls,'physicalCalibrationUnchanged':True,
    'protectedExistingPublicFiles':protected,'lowerLegMeasurements':anatomy},indent=2)+'\n')

comparisons = []
maxima = []
with (root/'all-20-feet.csv').open('w', newline='') as stream:
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['run','version','runner/foot','stanceFrames','comparedIntervals','worldXDrift','worldLaneDrift'])
    for name in ['isolated-continuous','race-18-desktop','race-18-mobile']:
        versions = {}
        for version, directory in [('v3',root/'before'),('v4',root)]:
            data = json.loads((directory/f'{name}-trace.json').read_text())
            versions[version] = data['summary']
            for foot, values in data['summary']['allRenderedFrames']['contactFrames'].items():
                writer.writerow([name,version,foot,*[values[k] for k in ['stanceFrames','comparedIntervals','maxWorldXDrift','maxWorldLaneDrift']]])
            for runner in sorted({r['id'] for f in data['allRenderFrames'] for r in f['field']}):
                rows = [(f['time'],r) for f in data['allRenderFrames'] for r in f['field'] if r['id']==runner]
                maxima.append({'name':name,'version':version,'runner':runner,**{
                    key:dict(zip(['timeMs','value'],max([(t,abs(r[key])) for t,r in rows],key=lambda x:x[1])))
                    for key in ['bodyOffset','bodySink','laneLag']}})
        comparisons.append({'name':name,**versions})
        for key in ['maxBodyOffset','maxBodySink','maxLaneLag','maxReachError']:
            assert versions['v4']['allRenderedFrames'][key] <= versions['v3']['allRenderedFrames'][key]+1e-8, (name,key)
(root/'before-after-measurements.json').write_text(json.dumps(comparisons,indent=2)+'\n')
(root/'per-runner-maxima.json').write_text(json.dumps(maxima,indent=2)+'\n')
print(json.dumps({'protectedFiles':len(protected),'controls':len(controls),'lowerLegs':anatomy}))
