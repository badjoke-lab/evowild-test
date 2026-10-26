"""Unit A: fit S hind chains to existing mesh; retain v1 chest/neck/front rig.
Python 3 + NumPy. No geometry edits or production manifest changes.
"""
import hashlib, json, struct
from pathlib import Path
import numpy as np
from inspect_s_glb_skin import read_glb, accessor

SOURCE=Path('public/models/evowild-s/review/focus-bind-repair-v1.glb')
OUTPUT=Path('public/models/evowild-s/review/focus-hind-fit-v2.glb')
REPORT=Path('docs/2p5d/evidence/20261026-s-hind-fit/asset-report.json')


def build():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='336161573b0ee22993b83dc1067ae2590237c023cf3c5d5e550b06c2ef0fab15'
    doc,binary=read_glb(SOURCE); skin=doc['skins'][0]
    names=[doc['nodes'][n]['name'] for n in skin['joints']]
    old=np.array([np.linalg.inv(m.reshape(4,4).T) for m in accessor(doc,binary,skin['inverseBindMatrices'])])
    new=old.copy(); attrs=doc['meshes'][0]['primitives'][0]['attributes']
    pos=accessor(doc,binary,attrs['POSITION']); ji=accessor(doc,binary,attrs['JOINTS_0']); we=accessor(doc,binary,attrs['WEIGHTS_0'])
    before_j=ji.copy();before_w=we.copy()
    untouched={i:accessor(doc,binary,i).tobytes() for k,i in attrs.items() if k not in ('JOINTS_0','WEIGHTS_0')}
    indices=doc['meshes'][0]['primitives'][0]['indices'];untouched[indices]=accessor(doc,binary,indices).tobytes()
    changes=[];local_changes={};landmarks={}
    parent={c:p for p,n in enumerate(doc['nodes']) for c in n.get('children',[])}
    for side,x in [('L',-.130),('R',.091)]:
        prefix='hind_'+side
        # Mesh-space section centers: thigh bulge -> forward knee -> rear hock
        # -> low toe. Fits the EXISTING sculpt, not imported animal proportions.
        targets=[(x,.035,-.500),(x,-.285,-.515),(x,-.490,-.735),(x,-.825,-.780)]
        chain=[prefix+'_upper',prefix+'_lower',prefix+'_foot']
        landmarks[prefix]={'hip':targets[0],'knee':targets[1],'hock':targets[2],'toe':targets[3]}
        for name,target in zip(chain,targets):
            i=names.index(name);new[i,:3,3]=target
        for name in chain:
            i=names.index(name);node_id=skin['joints'][i];node=doc['nodes'][node_id]
            parent_i=skin['joints'].index(parent[node_id]);local=np.linalg.inv(new[parent_i])@new[i]
            prev=np.array(node['translation']);node['translation']=local[:3,3].tolist()
            local_changes[node_id]=local[:3,3]-prev
            changes.append({'name':name,'old':old[i,:3,3].tolist(),'new':new[i,:3,3].tolist(),'offset':float(np.linalg.norm(new[i,:3,3]-old[i,:3,3]))})
        foot_i=names.index(chain[-1]);toe=new[foot_i].copy();toe[:3,3]=targets[3]
        local=np.linalg.inv(new[foot_i])@toe
        toe_node=len(doc['nodes']);doc['nodes'].append({'name':prefix+'_toe','translation':local[:3,3].tolist()})
        doc['nodes'][skin['joints'][foot_i]].setdefault('children',[]).append(toe_node)
        skin['joints'].append(toe_node);names.append(prefix+'_toe');new=np.concatenate([new,toe[None]])
    for anim in doc['animations']:
        for channel in anim['channels']:
            target=channel['target']
            if target['node'] in local_changes and target['path']=='translation':
                values=accessor(doc,binary,anim['samplers'][channel['sampler']]['output'])
                values[:]+=local_changes[target['node']]
    # Only vertices near the ipsilateral hind chain are reweighted. Distal
    # leg/sole weights become anatomical segments, not global nearest bones.
    affected=np.zeros(len(pos),dtype=bool)
    for side,x in [('L',-.130),('R',.091)]:
        prefix='hind_'+side; ids=[names.index(prefix+s) for s in ['_upper','_lower','_foot','_toe']]
        points=np.array(list(landmarks[prefix].values()));ends=np.vstack([points[1:],points[-1]+[0,0,.09]])
        distances=[]
        for a,b in zip(points,ends):
            ab=b-a;t=np.clip(((pos-a)@ab)/(ab@ab),0,1);distances.append(np.linalg.norm(pos-(a+t[:,None]*ab),axis=1))
        d=np.array(distances).T;near=d.min(axis=1)
        mask=(pos[:,1]<.08)&(pos[:,2]<-.30)&((pos[:,0]+.01945)*(x+.01945)>0)&(near<.18)
        blend=np.clip((.08-pos[:,1])/.18,0,1)*np.clip((.18-near)/.06,0,1)
        values=1/(d+.012)**4;values/=values.sum(axis=1,keepdims=True)
        for index in np.flatnonzero(mask):
            combined={}
            for b,w in zip(before_j[index],before_w[index]):combined[int(b)]=float(w)*(1-blend[index])
            for b,w in zip(ids,values[index]):combined[b]=combined.get(b,0)+float(w)*blend[index]
            top=sorted(combined.items(),key=lambda p:p[1],reverse=True)[:4];total=sum(w for _,w in top)
            ji[index]=[b for b,_ in top];we[index]=[w/total for _,w in top]
        affected|=mask
    # Appending the two inverse-bind matrices requires a new accessor; existing
    # mesh bytes and all non-hind animation payloads remain at original offsets.
    matrices=np.array([np.linalg.inv(m).T.reshape(16) for m in new],dtype='<f4').tobytes()
    for i,original in untouched.items():assert accessor(doc,binary,i).tobytes()==original
    # Release NumPy buffer views before resizing the binary bytearray.
    binary=bytearray(bytes(binary));binary+=b'\0'*((-len(binary))%4);offset=len(binary);binary.extend(matrices)
    doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(matrices)})
    doc['accessors'].append({'bufferView':len(doc['bufferViews'])-1,'componentType':5126,'count':len(new),'type':'MAT4'})
    skin['inverseBindMatrices']=len(doc['accessors'])-1;doc['buffers'][0]['byteLength']=len(binary)
    doc.setdefault('extras',{})['sHindFit']={'status':'REVISE','landmarks':landmarks,'footBoneRole':'hock; new toe joint controls distal foot'}
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
    hind_ids=[i for i,n in enumerate(names) if n.startswith('hind_')]
    old_hind=(before_w*np.isin(before_j,hind_ids)).sum(axis=1)
    protected=np.flatnonzero((old_hind==0)&~affected)
    report={'status':'REVISE','source':str(SOURCE),'output':str(OUTPUT),'outputSHA256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'geometryPreserved':True,'boneCount':len(new),'jointChanges':changes,'landmarksMeshSpace':landmarks,'affectedVertexCount':int(affected.sum()),'unchangedWeightsOutsideRegion':True,'protectedVertexCount':len(protected),'protectedProbeIndices':protected[::max(1,len(protected)//80)].tolist(),'note':'Landmarks are fitted to existing mesh sections. hind_*_foot now denotes hock; appended hind_*_toe is the distal joint. Sole contact is not solved in unit A.'}
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='protectedProbeIndices'},indent=2))

if __name__=='__main__':build()
