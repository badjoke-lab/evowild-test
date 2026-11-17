"""Author independent D3-C v3: staggered fold then fore extension, without rebuilding v1/v2.
The base/native clip and all geometry/skin/bind buffers remain immutable.
Full pose clip is GLTF-playable; the review adapter adds sole IK at runtime.
"""
from pathlib import Path
import copy,hashlib,json,math,struct
SOURCE=Path('public/models/evowild-s/review/d3c-scapula-author-v2.glb')
DEST=SOURCE.with_name('d3c-scapula-author-v3.glb')
OUT=Path('docs/2p5d/evidence/20261117-s-d3c-v3')
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()=='6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0'
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=bytearray(raw[28+n:]);original_animations=copy.deepcopy(doc['animations']);base=copy.deepcopy(next(a for a in doc['animations'] if a['name']=='EvoWild_S_Run_V5'));nodes=doc['nodes'];ids={x.get('name'):i for i,x in enumerate(nodes)}
width={'SCALAR':1,'VEC3':3,'VEC4':4}
def read(a):
 a=doc['accessors'][a];v=doc['bufferViews'][a['bufferView']];fmt='<'+str(width[a['type']])+'f';size=struct.calcsize(fmt)
 return [struct.unpack_from(fmt,binary,v.get('byteOffset',0)+a.get('byteOffset',0)+i*v.get('byteStride',size)) for i in range(a['count'])]
def append(values,kind):
 while len(binary)%4:binary.append(0)
 b=b''.join(struct.pack('<'+'f'*width[kind],*v) for v in values);offset=len(binary);binary.extend(b)
 doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(b)})
 a={'bufferView':len(doc['bufferViews'])-1,'componentType':5126,'count':len(values),'type':kind}
 if kind=='SCALAR':a.update(min=[min(v[0] for v in values)],max=[max(v[0] for v in values)])
 doc['accessors'].append(a);return len(doc['accessors'])-1
D=max(max(v[0] for v in read(s['input'])) for s in base['samplers']);N=241
track={}
for c in base['channels']:
 s=base['samplers'][c['sampler']];track[(c['target']['node'],c['target']['path'])]=([v[0] for v in read(s['input'])],read(s['output']))
def quat(angle):return (math.sin(angle/2),0.,0.,math.cos(angle/2))
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def norm(q):
 d=math.sqrt(sum(x*x for x in q));return tuple(x/d for x in q)
def sample(node,path,t):
 if (node,path) not in track:return tuple(nodes[node].get(path,{'rotation':[0,0,0,1],'translation':[0,0,0]}[path]))
 times,values=track[(node,path)];j=0
 while j+1<len(times) and times[j+1]<t:j+=1
 if t<=times[0]:return values[0]
 if j+1==len(times):return values[-1]
 u=(t-times[j])/(times[j+1]-times[j]);a,b=values[j:j+2]
 if path=='rotation':
  dot=sum(x*y for x,y in zip(a,b));b=tuple(-x for x in b) if dot<0 else b;dot=abs(dot)
  if dot<.9995:
   theta=math.acos(min(1,dot));return tuple((math.sin((1-u)*theta)*x+math.sin(u*theta)*y)/math.sin(theta) for x,y in zip(a,b))
 return norm(tuple(x+(y-x)*u for x,y in zip(a,b))) if path=='rotation' else tuple(x+(y-x)*u for x,y in zip(a,b))
def pulse(p,a,b):
 if not a<p<b:return 0.
 return math.sin(math.pi*(p-a)/(b-a))**4
def delta(name,path,p):
 if 'scapula' in name or name.startswith('fore_'):
  off=.64 if '_L_' in name else .72;u=(p-off)%1;sw=max(0,(u-.17)/.83)
  glide=math.cos(2*math.pi*(u+.05))
  if path=='translation':return (0.,.045*glide,-.012*pulse(u,0,.22))
  if name.endswith('scapula'):
   # Absolute shoulder rotation includes smooth v1 pose, avoiding its old
   # LINEAR-key velocity corner at .75. The original clip is still retained.
   deg=8.5*math.sin(2*math.pi*(p-off+.19))+10*glide
  elif name.endswith('upper'):
   # Advance the upper arm as the earlier fold opens; trailing arm follows.
   deg=18*pulse(sw,0,.90) if '_L_' in name else 18*pulse(sw,.22,1)
  else:
   # Same stance timing, distinct airborne recovery windows. Both have zero
   # position/slope at their boundaries. No extra lift or larger rotation.
   deg=(-20*pulse(sw,0,.70)+14*pulse(sw,.32,.88)) if '_L_' in name else -14*pulse(sw,.08,.78)
 else:
  push=pulse(p,.10,.52);load=pulse(p,.59,.99)
  deg={'pelvis':-4.0*push,'spine':2.4*push-2.5*load,'chest':1.5*push+6*load,'neck':-1*push-3.2*load,'head':-.5*push-1.3*load,'tail':2.0*pulse(p,.20,.64)}[name]
 return quat(math.radians(deg))
changes=[(f'fore_{s}_scapula',p) for s in 'LR' for p in ['translation','rotation']]+[(f'fore_{s}_{b}','rotation') for s in 'LR' for b in ['upper','lower']]+[(b,'rotation') for b in ['pelvis','spine','chest','neck','head','tail']]
times=append([(D*i/(N-1),) for i in range(N)],'SCALAR');add={'name':'D3C_V3_Drive_Pose','samplers':[],'channels':[]};auth=copy.deepcopy(base);auth['name']='EvoWild_S_D3C_V3';report=[]
for name,path in changes:
 node=ids[name];kind='VEC4' if path=='rotation' else 'VEC3';values=[delta(name,path,i/(N-1)) for i in range(N)];packed=[];h=1e-5
 for i,v in enumerate(values):
  p=i/(N-1);a=delta(name,path,(p-h)%1);b=delta(name,path,(p+h)%1);dv=tuple((y-x)/(2*h*D) for x,y in zip(a,b));packed.extend([dv,v,dv])
 add['samplers'].append({'input':times,'output':append(packed,kind),'interpolation':'CUBICSPLINE'});add['channels'].append({'sampler':len(add['samplers'])-1,'target':{'node':node,'path':path}})
 full=[]
 for i,v in enumerate(values):
  old=sample(node,path,D*i/(N-1));full.append(v if name.endswith('scapula') and path=='rotation' else mul(old,v) if path=='rotation' else tuple(x+y for x,y in zip(old,v)))
 sampler={'input':times,'output':append(full,kind),'interpolation':'LINEAR'};c=next((c for c in auth['channels'] if c['target']=={'node':node,'path':path}),None);auth['samplers'].append(sampler)
 if c:c['sampler']=len(auth['samplers'])-1
 else:auth['channels'].append({'sampler':len(auth['samplers'])-1,'target':{'node':node,'path':path}})
 report.append({'bone':name,'path':path,'range':[min(v[k] for v in values) for k in range(len(values[0]))]+[max(v[k] for v in values) for k in range(len(values[0]))]})
# New coverage found a v2 native body tangent corner at .72, even at constant
# speed. Store a narrow C1 bridge in THIS candidate, not in D2-D/D3-B or v2.
# Runtime applies only its difference from the native pose, retaining load pose.
join={'name':'D3C_V3_Native_Join','samplers':[],'channels':[]}
join_phases=[.712,.728];join_times=append([(p*D,) for p in join_phases],'SCALAR')
body_names={'root','pelvis','spine','chest','neck','head','tail','EvoWild_S_Armature_V3'}
for channel in base['channels']:
 node=channel['target']['node'];path=channel['target']['path']
 if nodes[node].get('name') not in body_names:continue
 kind='VEC4' if path=='rotation' else 'VEC3';packed=[];h=1e-5
 for p in join_phases:
  value=sample(node,path,p*D);left=sample(node,path,(p-h)*D);right=sample(node,path,(p+h)*D)
  derivative=tuple((b-a)/(2*h*D) for a,b in zip(left,right));packed.extend([derivative,value,derivative])
 join['samplers'].append({'input':join_times,'output':append(packed,kind),'interpolation':'CUBICSPLINE'})
 join['channels'].append({'sampler':len(join['samplers'])-1,'target':channel['target']})
doc['animations']=[auth,*original_animations,add,join];doc.setdefault('extras',{})['d3cV3']={'sourceSha256':hashlib.sha256(raw).hexdigest(),'authoring':'stagger fore fold then humerus extension; preserve v2 support poses except local native tangent bridge .712-.728; original 23-joint rest/skin' ,'status':'REVISE_REVIEW_ONLY','poseClip':'D3C_V3_Drive_Pose','absoluteScapulaRotation':True,'nativeJoin':join_phases}
doc['buffers'][0]['byteLength']=len(binary);data=json.dumps(doc,separators=(',',':')).encode();data+=b' '*((-len(data))%4);binary+=b'\0'*((-len(binary))%4)
out=struct.pack('<III',0x46546c67,2,28+len(data)+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary
DEST.write_bytes(out);assert SOURCE.read_bytes()==raw;OUT.mkdir(parents=True,exist_ok=True)
(OUT/'author-report.json').write_text(json.dumps({'source':str(SOURCE),'sourceSha256':hashlib.sha256(raw).hexdigest(),'candidate':str(DEST),'candidateSha256':hashlib.sha256(out).hexdigest(),'joints':len(doc['skins'][0]['joints']),'duration':D,'clips':[a['name'] for a in doc['animations']],'geometrySkinBindBuffersPreserved':True,'authoredChannels':report},indent=2)+'\n')
print('AUTHORED_V3',DEST,len(out),hashlib.sha256(out).hexdigest())
