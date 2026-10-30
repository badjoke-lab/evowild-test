"""D3-C: read-only anatomy feasibility audit of original review GLB.
No Blender dependency; all numeric values from actual glTF JSON/BIN/accessors.
"""
import json,struct,hashlib,sys
from pathlib import Path

path=Path(sys.argv[1] if len(sys.argv)>1 else "public/models/evowild-s/review/focus-contact-v3.glb")
raw=path.read_bytes()
assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
assert struct.unpack_from('<I',raw,8)[0]==len(raw)
size,tag=struct.unpack_from('<II',raw,12)
assert tag==0x4E4F534A
doc=json.loads(raw[20:20+size])
bin_start=20+size
bin_size,bin_tag=struct.unpack_from('<II',raw,bin_start)
assert bin_tag==0x004E4942
buffer=memoryview(raw)[bin_start+8:bin_start+8+bin_size]
nodes=doc['nodes']
parents={i:None for i in range(len(nodes))}
for i,node in enumerate(nodes):
 for child in node.get('children',[]):
  assert parents[child] is None, 'multiple parents'
  parents[child]=i

def accessor(num):
 a=doc['accessors'][num]
 v=doc['bufferViews'][a['bufferView']]
 ct=a['componentType']
 codes={5120:'b',5121:'B',5122:'h',5123:'H',5125:'I',5126:'f'}
 assert ct in codes
 widths={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
 n=widths[a['type']]
 fmt='<'+codes[ct]*n
 stride=v.get('byteStride',struct.calcsize(fmt))
 offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [struct.unpack_from(fmt,buffer,offset+i*stride) for i in range(a['count'])]

skin=doc['skins'][0]
joints=skin['joints']
jname={i:nodes[node].get('name','') for i,node in enumerate(joints)}
names=set(jname.values())
assert len(names)==len(joints)
attrs=doc['meshes'][0]['primitives'][0]['attributes']
weight_data=accessor(attrs['WEIGHTS_0'])
joint_data=accessor(attrs['JOINTS_0'])
pos=accessor(attrs['POSITION'])
assert len(pos)==len(joint_data)==len(weight_data)
weighted={i:{"sum":0.0,"max":0.0,"overPointOne":0,"overPointFive":0,"centerWeighted":[0.0,0.0,0.0],"min":[float('inf')]*3,"maxBox":[float('-inf')]*3} for i in range(len(joints))}
for point,inds,weights in zip(pos,joint_data,weight_data):
 for ji,w in zip(inds,weights):
  if w<=0:continue
  z=weighted[ji]
  z['sum']+=w
  z['max']=max(z['max'],w)
  for k in range(3):z['centerWeighted'][k]+=point[k]*w
  if w>.1:
   z['overPointOne']+=1
   for k in range(3):
    z['min'][k]=min(z['min'][k],point[k])
    z['maxBox'][k]=max(z['maxBox'][k],point[k])
  if w>.5:z['overPointFive']+=1

def parentchain(node_index):
 s=[]
 while node_index is not None:
  s.append(nodes[node_index].get('name',str(node_index)))
  node_index=parents[node_index]
 return s

animated={}
for animation in doc.get('animations',[]):
 for channel in animation.get('channels',[]):
  target=channel['target']
  key=nodes[target['node']].get('name',str(target['node']))
  animated.setdefault(key,[]).append(target['path'])
def measure(name):
 if name not in names:return None
 ji=next(i for i,z in jname.items() if z==name)
 nodeid=joints[ji];w=weighted[ji]
 summ=w['sum']
 return {
  'name':name,'parent':nodes[parents[nodeid]].get('name') if parents[nodeid] is not None else None,
  'children':[nodes[c].get('name') for c in nodes[nodeid].get('children',[])],
  'chainToRoot':parentchain(nodeid),
  'localTranslation':nodes[nodeid].get('translation',[0,0,0]),
  'animatedPaths':sorted(set(animated.get(name,[]))),
  'maxWeight':w['max'],'weightedVertexEquivalentCount':round(summ,2),
  'verticesAbovePointOne':w['overPointOne'],
  'verticesAbovePointFive':w['overPointFive'],
  'weightedCenter':[round(x/summ,6) for x in w['centerWeighted']] if summ else None,
  'weightedBounds':[[round(x,6) for x in w['min']],[round(x,6) for x in w['maxBox']]] if w['overPointOne'] else None
 }

fore=[f'fore_{side}_{part}' for side in ['L','R'] for part in ['upper','lower','foot']]
bodies=['root','pelvis','spine','chest','neck','head','tail']
present=[measure(n) for n in bodies+fore]
allnames=[jname[i] for i in range(len(joints))]
scapula=[n for n in allnames if any(x in n.lower() for x in ['shoulder','scapula','clavicle'])]
report={
 'asset':str(path),'sha256':hashlib.sha256(raw).hexdigest(),
 'vertices':len(pos),'skinnedJointCount':len(joints),
 'allSkinnedBoneNames':allnames,'standaloneShoulderBones':scapula,
 'tracked':present,'animations':[{"name":a.get('name'),"channels":len(a['channels'])} for a in doc.get('animations',[])],
 'foreIK':{"source":"src/s_contact_ik.js","behavior":"Per-frame twoBone(upper pivot,end,upperLength,lowerLength); rotate(upper,lower), set foot quaternion; no explicit scapula translation solver","overwrittenForeBoneNames":fore},
 'interpretation':"Stand-alone shoulder requires explicit skin influence and upstream control; parent chest rotation alone is not anatomical scapular glide. Presence/absence established by joints and weights; visual quality still requires WebGL frames."
}
out=Path('docs/2p5d/evidence/20261030-s-d3c-rig-feasibility')
out.mkdir(parents=True,exist_ok=True)
(out/'rig-inventory.json').write_text(json.dumps(report,indent=2)+'\n')
print('D3C_RIG_AUDIT',json.dumps({k:report[k] for k in ['sha256','vertices','skinnedJointCount','standaloneShoulderBones']}))
for name in bodies+fore:
 item=measure(name)
 if item: print('BONE',json.dumps({key:item[key] for key in ['name','parent','children','animatedPaths','weightedVertexEquivalentCount','verticesAbovePointOne']}))
