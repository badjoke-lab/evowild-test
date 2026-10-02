"""Experimental Vibe Gate A3a-v1: forelimb joint-rhythm refinement only.
Source: S-vibe-a2b-v1.blend.
Editable objects: S_forelimb_L and S_forelimb_R only.
Fore toes/feet, hindlimbs, core, accepted crest and all other geometry are hard-locked.
The final foot-root ring (station 6) is preserved exactly to maintain toe overlap/interface.
"""
import bpy, os, json, hashlib, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_reference_crest_v11']
foreL=bpy.data.objects['S_forelimb_L']
foreR=bpy.data.objects['S_forelimb_R']
editable={foreL.name,foreR.name}

for o in (foreL,foreR):
    assert len(o.data.vertices)==56, (o.name,len(o.data.vertices))

# Snapshot every non-editable mesh exactly.
fixed_before={}
for o in cage.objects:
    if o.type=='MESH' and o.name not in editable:
        fixed_before[o.name]=[v.co.copy() for v in o.data.vertices]

# Snapshot forelimb topology and foot-root ring.
fore_topology={}
foot_root_before={}
fore_source=[]
for o in (foreL,foreR):
    fore_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]
    foot_root_before[o.name]=[o.data.vertices[48+k].co.copy() for k in range(8)]
    centers=[]
    for s in range(7):
        pts=[o.data.vertices[s*8+k].co for k in range(8)]
        centers.append(tuple(sum((p for p in pts),Vector())/8.0))
    fore_source.append((o.name,centers))

# Target centerline and cross-sectional radii. Sign mirrors X only.
target_base=[
 # absX, Y, Z, lateral radius, sagittal radius
 (.115,-.030,.985,.068,.095),
 (.148, .035,.845,.056,.070),
 (.158, .125,.685,.040,.046),
 (.153,-.070,.515,.027,.038),
 (.150,-.220,.230,.018,.023),
 (.150,-.255,.105,.021,.020),
 # station 6 is preserved exactly, values here are centerline-only for tangent estimation
 (.150,-.268,.056,.031,.030),
]

def rebuild_partial(o,sign):
    centers=[Vector((sign*x,y,z)) for x,y,z,_,_ in target_base]
    # Replace stations 0..5 using the same 8-sided loft frame convention as the original builder.
    for i in range(6):
        c=centers[i]
        prev=centers[max(i-1,0)]
        nxt=centers[min(i+1,6)]
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

rebuild_partial(foreL,-1)
rebuild_partial(foreR,1)

# Exact foot-root ring preservation.
for o in (foreL,foreR):
    for k,co in enumerate(foot_root_before[o.name]):
        assert tuple(o.data.vertices[48+k].co)==tuple(co), f'foot root changed {o.name}:{k}'
    assert [tuple(p.vertices) for p in o.data.polygons]==fore_topology[o.name], f'topology changed {o.name}'

# All fixed geometry exact.
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
    for o in (foreL,foreR):
        for k in range(8):
            i=48+k
            h.update(o.name.encode());h.update(str(i).encode());h.update(repr(tuple(o.data.vertices[i].co)).encode())
    return h.hexdigest()

def station_centers(o):
    out=[]
    for s in range(7):
        pts=[o.data.vertices[s*8+k].co for k in range(8)]
        c=sum((p for p in pts),Vector())/8.0
        out.append([c.x,c.y,c.z])
    return out

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A3a-v1-forelimb-joint-rhythm',
 'source':'S-vibe-a2b-v1.blend',
 'decision':'REVIEW_PENDING',
 'editable':['S_forelimb_L','S_forelimb_R'],
 'single_hypothesis':'improve shoulder-elbow-wrist rhythm and proximal-to-distal taper',
 'hard_fixed':['complete core','accepted crest','both hindlimbs','all fore toes','all hind toes','tail','all non-forelimb meshes'],
 'foot_root_station_6_unchanged':True,
 'forelimb_topology_unchanged':True,
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'target_station_spec':target_base,
 'result_centers':{
   'L':station_centers(foreL),
   'R':station_centers(foreR)
 },
 'source_centers':dict(fore_source)
}
with open(os.path.join(OUT,'S-vibe-a3a-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a3a-v1.blend'),compress=True)
print('VIBE_A3A_V1_EDIT_COMPLETE',json.dumps(report))
