"""D3-C: independently author a pair of real scapula skin joints, animation.
Source review GLB never changes; experimental output only. Stdlib only.
"""
from pathlib import Path
import copy, hashlib, json, math, struct

SOURCE=Path("public/models/evowild-s/review/focus-contact-v3.glb")
DEST=Path("public/models/evowild-s/review/d3c-scapula-author-v1.glb")
REPORT=Path("docs/2p5d/evidence/20261030-s-d3c-scapula-v1/author-report.json")
SOURCE_SHA="78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f"
raw=SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA,"unexpected original rig"
magic,ver,size=struct.unpack_from("<III",raw,0)
assert magic==0x46546c67 and ver==2 and size==len(raw)
jsonlen,tag=struct.unpack_from("<II",raw,12)
assert tag==0x4e4f534a
doc=json.loads(raw[20:20+jsonlen])
pos=20+jsonlen
binlen,bintag=struct.unpack_from("<II",raw,pos)
assert bintag==0x004e4942
binary=bytearray(raw[pos+8:pos+8+binlen])
assert len(binary)==binlen
orig=copy.deepcopy(doc)
nodes=doc["nodes"]
skin=doc["skins"][0]
jointids=skin["joints"]
original_joint_count=len(jointids)
names=[nodes[i]["name"] for i in jointids]
assert original_joint_count==21 and names.count("chest")==1
skinidx={name:names.index(name) for name in names}
chestidx=skinidx["chest"]
mesh=doc["meshes"][0]
attrs=mesh["primitives"][0]["attributes"]
ctformat={5120:"b",5121:"B",5122:"h",5123:"H",5125:"I",5126:"f"}
widths={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}

def location(a):
 a=doc["accessors"][a]
 v=doc["bufferViews"][a["bufferView"]]
 assert not a.get("sparse"),"sparse accessor not supported"
 fmt="<"+ctformat[a["componentType"]]*widths[a["type"]]
 stride=v.get("byteStride",struct.calcsize(fmt))
 base=v.get("byteOffset",0)+a.get("byteOffset",0)
 return a,fmt,stride,base

def getall(n):
 a,fmt,stride,base=location(n)
 return [struct.unpack_from(fmt,binary,base+i*stride) for i in range(a["count"])]

def writeall(n,values):
 a,fmt,stride,base=location(n)
 assert len(values)==a["count"]
 for i,v in enumerate(values):
  struct.pack_into(fmt,binary,base+i*stride,*v)

def append_floats(items,kind):
 num=widths[kind]
 assert all(len(x)==num for x in items)
 data=b"".join(struct.pack("<"+"f"*num,*x) for x in items)
 while len(binary)%4:binary.append(0)
 offset=len(binary);binary.extend(data)
 vid=len(doc["bufferViews"])
 doc["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(data)})
 aid=len(doc["accessors"])
 doc["accessors"].append({"bufferView":vid,"componentType":5126,"count":len(items),"type":kind})
 return aid

def mm(a,b):
 return tuple(sum(a[k*4+r]*b[c*4+k] for k in range(4)) for c in range(4) for r in range(4))

ibm=getall(skin["inverseBindMatrices"])
assert len(ibm)==original_joint_count
positions=getall(attrs["POSITION"])
joints=getall(attrs["JOINTS_0"])
weights=getall(attrs["WEIGHTS_0"])
assert len(positions)==len(joints)==len(weights)==38813
weights_orig=tuple(tuple(w) for w in weights)
joints_orig=tuple(tuple(j) for j in joints)
assert doc["accessors"][attrs["WEIGHTS_0"]]["componentType"]==5126
assert doc["accessors"][attrs["JOINTS_0"]]["componentType"] in (5121,5123)
assert len(doc["animations"])==1
anim=doc["animations"][0]
assert anim["name"]=="EvoWild_S_Run_V5"
shoulder={}
changed_translation_channels=[]
new_mat=[]
for side,phase in (("L",.64),("R",.72)):
 uppername=f"fore_{side}_upper";upperid=jointids[skinidx[uppername]]
 chestid=jointids[chestidx]
 p=nodes[upperid]["translation"][:]
 assert len(p)==3
 assert upperid in nodes[chestid]["children"]
 # New scapula at the *existing* anatomical upper-arm pivot, below chest.
 # Moving the original upper translation to zero preserves all bind world poses.
 scap_id=len(nodes)
 nodes.append({"name":f"fore_{side}_scapula","translation":p,"children":[upperid]})
 nodes[chestid]["children"]=[
  scap_id if x==upperid else x for x in nodes[chestid]["children"]
 ]
 nodes[upperid]["translation"]=[0.,0.,0.]
 # Existing animation translation output is absolute relative to chest.
 # Shift its keys by the same p, preserving original animated world transforms.
 for channel in anim["channels"]:
  if channel["target"]["node"]!=upperid or channel["target"]["path"]!="translation":continue
  sampler=anim["samplers"][channel["sampler"]]
  assert sampler.get("interpolation","LINEAR") in ("LINEAR","STEP")
  output=sampler["output"]
  a,_,_,_=location(output)
  assert a["type"]=="VEC3" and a["componentType"]==5126
  v=getall(output)
  writeall(output,[(x[0]-p[0],x[1]-p[1],x[2]-p[2]) for x in v])
  changed_translation_channels.append(uppername)
 # Inverse bind of new shoulder: inv(T(p)) * chest inverse bind.
 trans=[1.,0.,0.,0., 0.,1.,0.,0., 0.,0.,1.,0., -p[0],-p[1],-p[2],1.]
 new_mat.append(mm(trans,ibm[chestidx]))
 jointids.append(scap_id)
 shoulder[side]={"jointId":scap_id,"skinIndex":len(jointids)-1,"parent":"chest",
                 "child":uppername,"pivotLocalChest":p,"phase":phase}

# Select proximal region using original upper influences and real mesh geometry.
# Crucial: transfer only CHEST weight to scapula. At neutral scapula rotation
# both have identical skinning transforms for every native frame.
stats={}
new_w=[list(w) for w in weights]
new_j=[list(j) for j in joints]
for side in ("L","R"):
 info=shoulder[side]
 upper_idx=skinidx[f"fore_{side}_upper"]
 proximal=[(v,weights[i][k]) for i,v in enumerate(positions) for k,j in enumerate(joints[i])
           if j==upper_idx and weights[i][k]>.07 and v[1]>-.16]
 assert len(proximal)>50,("no upper proximal points",side,len(proximal))
 total=sum(w for _,w in proximal)
 center=[sum(v[k]*w for v,w in proximal)/total for k in range(3)]
 radius=.25
 count=0
 transferred=0.
 maxtransfer=0.
 for i,v in enumerate(positions):
  oldchest=sum(new_w[i][k] for k,j in enumerate(new_j[i]) if j==chestidx)
  if oldchest<.015:continue
  dist=math.dist(v,center)
  if dist>=radius:continue
  shape=(1-dist/radius)**2
  take=oldchest*.68*shape
  if take<.0003:continue
  old={int(j):float(w) for j,w in zip(new_j[i],new_w[i]) if w>0}
  old[chestidx]-=take
  old[info["skinIndex"]]=old.get(info["skinIndex"],0)+take
  four=sorted(old.items(),key=lambda kv:kv[1],reverse=True)[:4]
  denom=sum(w for _,w in four)
  if info["skinIndex"] not in [ji for ji,_ in four]:continue
  four=[(j,w/denom) for j,w in four]
  new_j[i]=[j for j,_ in four]+[0]*(4-len(four))
  new_w[i]=[w for _,w in four]+[0.]*(4-len(four))
  count+=1;transferred+=take;maxtransfer=max(maxtransfer,take)
 assert count>20,("shoulder region unexpectedly empty",side,count)
 stats[side]={"proximalUpperCount":len(proximal),"meshCenter":center,
              "influenceRadius":radius,"affectedVertices":count,
              "transferredChestWeight":transferred,"maxIndividualTransfer":maxtransfer}
writeall(attrs["JOINTS_0"],new_j)
writeall(attrs["WEIGHTS_0"],new_w)
assert all(abs(sum(w)-1)<.001 for w in new_w)

# Native cycle duration as defined by actual original clip times.
timeends=[]
for channel in anim["channels"]:
 sampler=anim["samplers"][channel["sampler"]]
 t=getall(sampler["input"])
 timeends.append(max(x[0] for x in t))
duration=max(timeends)
assert duration>.05
N=97
times=[(duration*i/(N-1),) for i in range(N)]
input_access=append_floats(times,"SCALAR")
for side in ("L","R"):
 info=shoulder[side]
 phase=info["phase"]
 qs=[]
 for i in range(N):
  u=i/(N-1)
  # Phase-locked scapular protraction as fore swing finishes and retract
  # through support. No root bouncing, no animation of lower limb or foot.
  theta=math.radians(8.5)*math.sin(2*math.pi*(u-phase+.19))
  # Three.js and glTF quaternion XYZW (rotation around local X).
  qs.append((math.sin(theta/2),0.,0.,math.cos(theta/2)))
 out_access=append_floats(qs,"VEC4")
 sampler_id=len(anim["samplers"])
 anim["samplers"].append({"input":input_access,"output":out_access,"interpolation":"LINEAR"})
 anim["channels"].append({"sampler":sampler_id,
                        "target":{"node":info["jointId"],"path":"rotation"}})

skin["inverseBindMatrices"]=append_floats(list(ibm)+new_mat,"MAT4")
doc["buffers"][0]["byteLength"]=len(binary)
doc.setdefault("extras",{})["d3cScapula"]={
 "status":"experimental_visual_REVISE","sourceSha256":SOURCE_SHA,
 "notes":"Separate shoulder pivots and chest-only local weight transfer; no topology/mesh positions altered",
 "shoulder":shoulder,"weightStats":stats
}
encoded=json.dumps(doc,separators=(",",":"),ensure_ascii=False).encode()
encoded+=b" "*((-len(encoded))%4)
binary+=b"\0"*((-len(binary))%4)
out=struct.pack("<III",0x46546c67,2,28+len(encoded)+len(binary))
out+=struct.pack("<II",len(encoded),0x4e4f534a)+encoded
out+=struct.pack("<II",len(binary),0x004e4942)+bytes(binary)
DEST.parent.mkdir(parents=True,exist_ok=True)
DEST.write_bytes(out)

# GLB topology / positions / joint parent chain expectations, source immutable.
assert SOURCE.read_bytes()==raw
assert getall(attrs["POSITION"])==positions
assert len(doc["skins"][0]["joints"])==23
assert len(anim["channels"])==len(orig["animations"][0]["channels"])+2
report={"source":str(SOURCE),"sourceSha256":SOURCE_SHA,"candidate":str(DEST),
        "candidateSha256":hashlib.sha256(out).hexdigest(),"status":"REVISE_REVIEW_ONLY",
        "originalVertices":len(positions),"originalSkinnedJoints":original_joint_count,
        "newSkinnedJoints":len(jointids),"animationChannels":len(anim["channels"]),
        "nativeUpperTranslationAdjusted":changed_translation_channels,
        "scapula":shoulder,"weights":stats,
        "originalPositionAccessorUnchanged":True,
        "originalIndicesAccessorUnchanged":True,
        "originalGLBUnchanged":True,
        "requiresActualVisualAndContactTests":True}
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(report,indent=2)+"\n")
print("D3C_RIG_BUILT",json.dumps(report))
