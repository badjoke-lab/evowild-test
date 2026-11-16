"""Read-only preservation gate for v3, including every prior animation."""
import hashlib,json,struct
from pathlib import Path
base=Path('public/models/evowild-s/review')
def load(p):
 r=p.read_bytes();n=struct.unpack_from('<I',r,12)[0];return r,json.loads(r[20:20+n]),r[28+n:]
v2,a,b2=load(base/'d3c-scapula-author-v2.glb');v3,b,b3=load(base/'d3c-scapula-author-v3.glb')
sha=lambda p:hashlib.sha256(p).hexdigest()
assert sha(v2)=='6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0'
assert sha((base/'d3c-scapula-author-v1.glb').read_bytes())=='963b52b0f82e58edb02423615415502f50e6245fa4f50a1606d192f0bae64a2d'
assert sha((base/'focus-contact-v3.glb').read_bytes())=='78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f'
for k in ['nodes','skins','meshes','materials','scenes','scene']:assert a.get(k)==b.get(k),k
assert b3[:len(b2)]==b2
assert b['animations'][1:1+len(a['animations'])]==a['animations']
assert b['accessors'][:len(a['accessors'])]==a['accessors']
assert b['bufferViews'][:len(a['bufferViews'])]==a['bufferViews']
assert len(b['skins'][0]['joints'])==23
print(json.dumps({'v2Sha256':sha(v2),'v3Sha256':sha(v3),'allOriginalGeometrySkinRestAndClipsPreserved':True,'joints':23,'clips':[x['name'] for x in b['animations']]},indent=2))
