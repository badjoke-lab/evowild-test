"""Experimental Vibe Gate A3b-v1: hindlimb joint-rhythm refinement only.
Source: S-vibe-a3a-v1.blend.
Editable objects: S_hindlimb_L and S_hindlimb_R only.
Accepted forelimbs, all feet/toes, core, crest and all other geometry are hard-locked.
Final foot-root ring (station 7) is preserved exactly.
"""
import bpy, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
hindL=bpy.data.objects['S_hindlimb_L']
hindR=bpy.data.objects['S_hindlimb_R']
editable={hindL.name,hindR.name}

for o in (hindL,hindR):
    assert len(o.data.vertices)==64, (o.name,len(o.data.vertices))

fixed_before={}
for o in cage.objects:
    if o.type=='MESH' and o.name not in editable:
        fixed_before[o.name]=[v.co.copy() for v in o.data.vertices]

hind_topology={}
foot_root_before={}
source_centers={}
for o in (hindL,hindR):
    hind_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]
    foot_root_before[o.name]=[o.data.vertices[56+k].co.copy() for k in range(8)]
    cc=[]
    for s in range(8):
        pts=[o.data.vertices[s*8+k].co for k in range(8)]
        cc.append(list(sum((p for p in pts),Vector())/8.0))
    source_centers[o.name]=cc

target_base=[
 (.109,.815,.982,.072,.110),
 (.145,.745,.850,.064,.086),
 (.164,.630,.720,.041,.050),
 (.164,.825,.565,.033,.050),
 (.158,1.050,.315,.022,.032),
 (.153,1.055,.220,.019,.025),
 (.150,.985,.087,.023,.021),
 (.150,.970,.053,.031,.030), # station 7 preserved exactly; center only used for tangent
]

def rebuild_partial(o,sign):
    centers=[Vector((sign*x,y,z)) for x,y,z,_,_ in target_base]
    for i in range(7):
        c=centers[i]
        prev=centers[max(i-1,0)]
        nxt=centers[min(i+1,7)]
        tangent=nxt-prev
        if tangent.length==0:
            tangent=Vector((0,0,-1))
        tangent.normalize()
        lateral=Vector((1,0,0))
        lateral=(lateral-tangent*lateral.dot(tangent))
        if lateral.length==0:
            lateral=Vector((1,0,0))
        lateral.normalize()
        sagittal=tangent.cross(lateral)
        if sagittal.length==0:
            sagittal=Vector((0,1,0))
        sagittal.normalize()
        wx=target_base[i][3]; wy=target_base[i][4]
        for k in range(8):
            a=k*math.tau/8.0
            p=c+lateral*(wx*math.cos(a))+sagittal*(wy*math.sin(a))
            o.data.vertices[i*8+k].co=p
    o.data.update()

rebuild_partial(hindL,-1)
rebuild_partial(hindR,1)

for o in (hindL,hindR):
    for k,co in enumerate(foot_root_before[o.name]):
        assert tuple(o.data.vertices[56+k].co)==tuple(co), f'foot root changed {o.name}:{k}'
    assert [tuple(p.vertices) for p in o.data.polygons]==hind_topology[o.name], f'topology changed {o.name}'

for name,coords in fixed_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords), name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'fixed changed {name}:{i}'

def fixed_hash():
    h=hashlib.sha256()
    for name in sorted(fixed_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
    for o in (hindL,hindR):
        for k in range(8):
            i=56+k
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(o.data.vertices[i].co)).encode())
    return h.hexdigest()

def station_centers(o):
    out=[]
    for s in range(8):
        pts=[o.data.vertices[s*8+k].co for k in range(8)]
        c=sum((p for p in pts),Vector())/8.0
        out.append([c.x,c.y,c.z])
    return out

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A3b-v1-hindlimb-joint-rhythm',
 'source':'S-vibe-a3a-v1.blend',
 'decision':'REVIEW_PENDING',
 'editable':['S_hindlimb_L','S_hindlimb_R'],
 'single_hypothesis':'make hip-knee-hock rhythm distinct from forelimb while reducing oversized proximal cone',
 'hard_fixed':['complete core','accepted crest','accepted forelimbs','all fore toes','all hind toes','tail','all non-hindlimb meshes'],
 'foot_root_station_7_unchanged':True,
 'hindlimb_topology_unchanged':True,
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'target_station_spec':target_base,
 'result_centers':{'L':station_centers(hindL),'R':station_centers(hindR)},
 'source_centers':source_centers
}
with open(os.path.join(OUT,'S-vibe-a3b-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a3b-v1.blend'),compress=True)
print('VIBE_A3B_V1_EDIT_COMPLETE',json.dumps(report))
