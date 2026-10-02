"""Experimental Vibe Gate A4-v2: tail stem/tip correction only.
Source: S-vibe-a4-v1.blend.
Editable: core rings 15-19 / vertices 120-159 only.
Preserve the shortened A4-v1 length while reducing stem mass and lifting/tapering the tip.
"""
import bpy, os, json, hashlib, math

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
assert len(mesh.vertices)==160

EDIT=set(range(120,160))
FIXED=set(range(160))-EDIT
core_before={i:mesh.vertices[i].co.copy() for i in range(160)}
other_before={}
for o in cage.objects:
    if o.type=='MESH' and o!=core:
        other_before[o.name]=[v.co.copy() for v in o.data.vertices]
poly_before=[tuple(p.vertices) for p in mesh.polygons]

targets={
 15:(1.15,1.015,0.930,0.045),
 16:(1.29,1.025,0.955,0.035),
 17:(1.43,1.030,0.965,0.028),
 18:(1.55,1.070,0.965,0.030),
 19:(1.66,1.090,1.020,0.006),
}

source_station={}
for s in targets:
    ring=[mesh.vertices[s*8+k].co.copy() for k in range(8)]
    source_station[s]={
      'y':sum(p.y for p in ring)/8.0,
      'top':max(p.z for p in ring),
      'bottom':min(p.z for p in ring),
      'half_width':max(abs(p.x) for p in ring)
    }

for s,(y,top,bottom,width) in targets.items():
    mid=(top+bottom)/2.0
    half_h=(top-bottom)/2.0
    for k in range(8):
        a=k*math.tau/8.0
        mesh.vertices[s*8+k].co=(width*math.cos(a),y,mid+half_h*math.sin(a))
mesh.update()

for i in FIXED:
    assert tuple(mesh.vertices[i].co)==tuple(core_before[i]), f'fixed core changed {i}'
assert [tuple(p.vertices) for p in mesh.polygons]==poly_before
for name,coords in other_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co), f'other changed {name}:{i}'

def fixed_hash():
    h=hashlib.sha256()
    for i in sorted(FIXED):
        h.update(b'core');h.update(str(i).encode());h.update(repr(tuple(mesh.vertices[i].co)).encode())
    for name in sorted(other_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode());h.update(str(i).encode());h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A4-v2-tail-stem-tip',
 'source':'S-vibe-a4-v1.blend',
 'decision':'REVIEW_PENDING',
 'editable':['core rings 15-19 / vertices 120-159 only'],
 'single_hypothesis':'thin A4-v1 stem and progressively lift/taper terminal blade while preserving shortened length',
 'hard_fixed':['core rings 0-14','accepted crest','accepted limbs','all feet/toes','topology'],
 'source_stations':{str(k):v for k,v in source_station.items()},
 'target_stations':{str(k):{'y':v[0],'top':v[1],'bottom':v[2],'half_width':v[3]} for k,v in targets.items()},
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'other_meshes_unchanged':True,
 'topology_unchanged':True
}
with open(os.path.join(OUT,'S-vibe-a4-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a4-v2.blend'),compress=True)
print('VIBE_A4_V2_EDIT_COMPLETE',json.dumps(report))
