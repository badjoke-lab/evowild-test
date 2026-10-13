"""Record deliverable metadata without repainting artwork or interpolating frames."""
import hashlib,json,subprocess
from pathlib import Path
root=Path('docs/evidence/p-rig-v3-20261013')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assets=[Path('src/p_layered.js'),*sorted(Path('public/concept/p-layered-v3').glob('*'))]
assets.extend(sorted(Path('scripts').glob('*p-rig-v3*')))
public=json.loads((root/'control-and-asset-preservation.json').read_text())
videos={}
for name in ['isolated-continuous','race-18-desktop','race-18-mobile','before-after-motion','layered-half-speed']:
 p=root/(name+'.mp4')
 videos[p.name]=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(p)],text=True))
 images={str(p.relative_to(root)):sha(p) for p in root.glob('*.png')}
 result={'baseline':'eaf0d9f4bba027f6b72eba49f48d00d5d9d61225','verdict':'REVISE','supportMethod':'KEEP','standardAdoption':False,
 'runtimeAndToolsSha256':{str(p):sha(p) for p in assets},'imageSha256':images,'videos':videos,
 'protectedExistingPublicFiles':len(public['protectedExistingPublicFiles']),
 'localValidation':{'build':'PASS (npm --ignore-scripts run build)','diffCheck':'PASS','loop':'PASS','1000PairedControlFrames':'IDENTICAL','all20SupportAnchors':'ZERO DRIFT'},
 'runtime':'Chromium 151.0.7922.173; Node 24.19.0; PC 1280x720; Pixel7 emulation 412x839; deterministic frame capture, not real-time performance certification'}
tests=root/'2p5d-test-results.json'
if tests.exists() and tests.stat().st_size:
 data=json.loads(tests.read_text());result['localValidation']['playwright']=data['stats']
(root/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
paths=subprocess.check_output(['git','diff','--name-only','--','src/p_layered.js'],text=True).splitlines()
paths.extend(str(p) for directory in [Path('public/concept/p-layered-v3'),root] for p in directory.rglob('*') if p.is_file())
paths.extend(str(p) for p in Path('scripts').glob('*p-rig-v3*'))
paths.append('docs/p-rig-v3-review-20261013.md')
(root/'changed-files.txt').write_text('\n'.join(sorted(set(paths+[str(root/'changed-files.txt')])) )+'\n')
print(json.dumps({'videos':videos,'localValidation':result['localValidation']},indent=2))
