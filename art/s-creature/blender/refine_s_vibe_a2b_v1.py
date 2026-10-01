"""Experimental Vibe Gate A2b-v1: pelvis cross-sectional lightening only.
Source: S-vibe-a2a-v1.blend.
Editable: core rings 12-14 (vertex ids 96-119) only.
Y station positions are immutable. All earlier accepted geometry, crest,
tail, limbs, feet/toes, topology and vertex counts are hard-locked.
"""
import bpy, os, json, hashlib, math

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
crest=bpy.data.objects['S_reference_crest_v11']
mesh=core.data
assert len(mesh.vertices)==160

EDIT=set(range(96,120))
FIXED=set(range(160))-EDIT

core_before={i:mesh.vertices[i].co.copy() for i in range(160)}
crest_before=[v.co.copy() for v in crest.data.vertices]
appendage_before={}
for o in cage.objects:
    if o.type=='MESH' and o not in (core,crest):
        appendage_before[o.name]=[v.co.copy() for v in o.data.vertices]

poly_before=[tuple(p.vertices) for p in mesh.polygons]
vert_count_before=len(mesh.vertices)
poly_count_before=len(mesh.polygons)

targets={
 12:(1.130,0.880,0.105),
 13:(1.120,0.870,0.112),
 14:(1.060,0.930,0.078),
}

source_y={}
source_station={}
for s in targets:
    ring=[mesh.vertices[s*8+k].co.copy() for k in range(8)]
    y=sum(p.y for p in ring)/8.0
    source_y[s]=y
    source_station[s]={
      'y':y,
      'top':max(p.z for p in ring),
      'bottom':min(p.z for p in ring),
      'half_width':max(abs(p.x) for p in ring)
    }

for s,(top,bottom,width) in targets.items():
    y=source_y[s]
    mid=(top+bottom)/2.0
    half_h=(top-bottom)/2.0
    for k in range(8):
        a=k*math.tau/8.0
        mesh.vertices[s*8+k].co=(width*math.cos(a),y,mid+half_h*math.sin(a))
mesh.update()

for i in FIXED:
    assert tuple(mesh.vertices[i].co)==tuple(core_before[i]), f'fixed core changed {i}'
for s in targets:
    for k in range(8):
        i=s*8+k
        assert abs(mesh.vertices[i].co.y-core_before[i].y)<1e-9, f'Y changed {i}'
assert len(mesh.vertices)==vert_count_before
assert len(mesh.polygons)==poly_count_before
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before

assert len(crest.data.vertices)==len(crest_before)
for i,co in enumerate(crest_before):
    assert tuple(crest.data.vertices[i].co)==tuple(co), f'crest changed {i}'
for name,coords in appendage_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'appendage changed {name}:{i}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(FIXED):
        h.update(b'core'); h.update(str(i).encode()); h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for i,v in enumerate(crest.data.vertices):
        h.update(b'crest'); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    for name in sorted(appendage_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A2b-v1-pelvis-lightening',
 'source':'S-vibe-a2a-v1.blend',
 'decision':'REVIEW_PENDING',
 'editable':['core rings 12-14 / vertices 96-119 only'],
 'single_hypothesis':'raise/lighten pelvis ventral mass while preserving elevated hip',
 'longitudinal_y_change':False,
 'hard_fixed':['core rings 0-11','accepted crest S_reference_crest_v11','core rings 15-19','all limbs','all feet/toes','topology'],
 'source_stations':{str(k):v for k,v in source_station.items()},
 'target_stations':{str(k):{'y':source_y[k],'top':v[0],'bottom':v[1],'half_width':v[2]} for k,v in targets.items()},
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'crest_unchanged':True,
 'appendages_unchanged':True,
 'topology_unchanged':True,
 'vertex_count':len(mesh.vertices),
 'polygon_count':len(mesh.polygons)
}
with open(os.path.join(OUT,'S-vibe-a2b-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a2b-v1.blend'),compress=True)
print('VIBE_A2B_V1_EDIT_COMPLETE',json.dumps(report))
