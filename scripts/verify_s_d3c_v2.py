"""Read-only validation of the independent v2 asset against its immutable v1."""
import hashlib,json,struct
from pathlib import Path
base=Path('public/models/evowild-s/review')
def load(p):
 r=p.read_bytes();n=struct.unpack_from('<I',r,12)[0];return r,json.loads(r[20:20+n]),r[28+n:]
v1,a,b1=load(base/'d3c-scapula-author-v1.glb');v2,b,b2=load(base/'d3c-scapula-author-v2.glb')
assert hashlib.sha256(v1).hexdigest()=='963b52b0f82e58edb02423615415502f50e6245fa4f50a1606d192f0bae64a2d'
assert hashlib.sha256((base/'focus-contact-v3.glb').read_bytes()).hexdigest()=='78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f'
for k in ['nodes','skins','meshes','materials','scenes','scene']:assert a.get(k)==b.get(k),k
assert b2[:len(b1)]==b1
assert b['accessors'][:len(a['accessors'])]==a['accessors']
assert b['bufferViews'][:len(a['bufferViews'])]==a['bufferViews']
assert b['animations'][1]==a['animations'][0]
assert len(b['skins'][0]['joints'])==23
for anim in b['animations']:
 for c in anim['channels']:
  s=anim['samplers'][c['sampler']];i,o=b['accessors'][s['input']],b['accessors'][s['output']]
  assert o['count']==i['count']*(3 if s.get('interpolation')=='CUBICSPLINE' else 1)
print(json.dumps({'v1Sha256':hashlib.sha256(v1).hexdigest(),'v2Sha256':hashlib.sha256(v2).hexdigest(),'geometrySkinBindingsNodesMaterialsOriginalBytesUnchanged':True,'v1NativeClipPreserved':True,'joints':23,'clips':[x['name'] for x in b['animations']]},indent=2))
