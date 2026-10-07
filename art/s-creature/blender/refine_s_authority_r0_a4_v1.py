"""Authority reset R0-A4 v1: replace generic three-toe feet with split racing feet.

Source: accepted output/S-authority-r0-a3-v2.blend
Body and all accepted A1/A2/A3 geometry are exact hard locks.
"""
import bpy,bmesh,os,json,hashlib,math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
AUTH_PATH=os.path.join(ROOT,'references','00_s_type_modeling_image_v1.png')
AUTH_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

assert os.path.getsize(AUTH_PATH)==1982782
assert sha256_file(AUTH_PATH)==AUTH_SHA

cage=bpy.data.collections['S_REBUILD_GATE_A']
body=bpy.data.objects['S_B2a_v5_continuous_body']
crest=bpy.data.objects['S_authority_r0_a1_v2_crest']

# Exact body lock.
body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

# Snapshot every non-toe mesh that must remain exact.
old_toes=sorted([o for o in cage.objects if o.type=='MESH' and '_toe_' in o.name],key=lambda o:o.name)
assert len(old_toes)==12,[o.name for o in old_toes]

fixed_mesh={}
fixed_topology={}
for o in cage.objects:
    if o.type=='MESH' and o!=body and o not in old_toes:
        fixed_mesh[o.name]=[v.co.copy() for v in o.data.vertices]
        fixed_topology[o.name]=[tuple(p.vertices) for p in o.data.polygons]

camera_before={}
for stem in ('SIDE','FRONT','FRONT34','REAR34','BACK'):
    o=bpy.data.objects['S_REBUILD_CAM_'+stem]
    camera_before[o.name]=tuple(tuple(row) for row in o.matrix_world)

old_toe_names=[o.name for o in old_toes]
for o in old_toes:
    bpy.data.objects.remove(o,do_unlink=True)

# Four foot attachment landmarks inherited from the locked donor.
FEET=[
 ('fore','L',-0.150,-0.268),
 ('fore','R', 0.150,-0.268),
 ('hind','L',-0.150, 0.970),
 ('hind','R', 0.150, 0.970),
]

def loft_blade(name,centers,widths,depths):
    """Closed 4-sided low-poly blade loft along a center path."""
    assert len(centers)==len(widths)==len(depths)>=2
    verts=[]; faces=[]; rings=[]
    C=[Vector(c) for c in centers]
    for i,c in enumerate(C):
        if i==0: tangent=C[1]-C[0]
        elif i==len(C)-1: tangent=C[-1]-C[-2]
        else: tangent=C[i+1]-C[i-1]
        if tangent.length==0: tangent=Vector((0,-1,0))
        tangent.normalize()

        lateral=Vector((1,0,0))
        lateral=lateral-tangent*lateral.dot(tangent)
        if lateral.length<1e-8: lateral=Vector((1,0,0))
        lateral.normalize()
        sagittal=tangent.cross(lateral)
        if sagittal.length<1e-8: sagittal=Vector((0,0,1))
        sagittal.normalize()

        ring=[]
        for sl,ss in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=c+lateral*(sl*widths[i])+sagittal*(ss*depths[i])
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring)

    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))

    m=bpy.data.meshes.new(name+'_mesh')
    m.from_pydata(verts,[],faces); m.update()
    o=bpy.data.objects.new(name,m); cage.objects.link(o)
    for p in m.polygons: p.use_smooth=False

    bm=bmesh.new(); bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    nm=[e for e in bm.edges if len(e.link_faces)!=2]
    bm.to_mesh(m); bm.free()
    assert not nm,name
    return o

new_objects=[]
foot_meta=[]

for family,side,x0,y0 in FEET:
    dominant_len=0.120 if family=='fore' else 0.112

    # Two dominant split prongs. Their roots sit close to the ankle and
    # diverge laterally toward the tips.
    prong_tips=[]
    for split,label in [(-1,'A'),(1,'B')]:
        centers=[
          (x0+split*0.010,y0-0.004,0.064),
          (x0+split*0.016,y0-dominant_len*0.48,0.034),
          (x0+split*0.024,y0-dominant_len,0.014),
        ]
        widths=[0.0105,0.0115,0.0065]
        depths=[0.0130,0.0140,0.0060]
        o=loft_blade(f'S_racing_foot_{family}_{side}_prong_{label}',centers,widths,depths)
        new_objects.append(o)
        prong_tips.append(Vector(centers[-1]))

    tip_sep=(prong_tips[0]-prong_tips[1]).length
    assert 0.040 <= tip_sep <= 0.060,tip_sep

    # Small rear stabilizer: deliberately short/subordinate.
    spur_len=0.042
    spur_centers=[
      (x0,y0+0.002,0.058),
      (x0,y0+spur_len*0.55,0.036),
      (x0,y0+spur_len,0.026),
    ]
    spur=loft_blade(
      f'S_racing_foot_{family}_{side}_rear_spur',
      spur_centers,[0.0090,0.0080,0.0045],[0.0100,0.0080,0.0040]
    )
    new_objects.append(spur)

    assert spur_len/dominant_len < 0.45
    foot_meta.append({
      'family':family,'side':side,'root':[x0,y0,0.060],
      'dominant_prong_length':dominant_len,
      'dominant_tip_separation':tip_sep,
      'dominant_min_z':0.014,
      'rear_spur_length':spur_len,
      'rear_spur_length_ratio':spur_len/dominant_len,
    })

assert len(new_objects)==12
assert not [o.name for o in cage.objects if '_toe_' in o.name]

# Body is bit-exact.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i,co in enumerate(body_before):
    assert tuple(body.data.vertices[i].co)==tuple(co),f'body changed {i}'

# Every retained mesh is bit-exact.
for name,coords in fixed_mesh.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords),name
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==tuple(co),f'fixed mesh changed {name}:{i}'
    assert [tuple(p.vertices) for p in o.data.polygons]==fixed_topology[name],name

for name,m in camera_before.items():
    assert tuple(tuple(row) for row in bpy.data.objects[name].matrix_world)==m,name

bm=bmesh.new(); bm.from_mesh(body.data)
assert len([e for e in bm.edges if len(e.link_faces)!=2])==0
bm.free()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'R0-A4-v1-authority-split-racing-feet',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'authority_sha256':AUTH_SHA,
 'source':'S-authority-r0-a3-v2.blend',
 'accepted_prior_gates':['R0-A1','R0-A2','R0-A3'],
 'output':'S-authority-r0-a4-v1.blend',
 'scope':'replace generic toe appendages with four split racing-foot assemblies only',
 'removed_generic_toes':old_toe_names,
 'removed_generic_toe_count':len(old_toe_names),
 'new_foot_object_count':len(new_objects),
 'new_foot_objects':[o.name for o in new_objects],
 'foot_meta':foot_meta,
 'dominant_prongs_per_foot':2,
 'rear_stabilizers_per_foot':1,
 'hard_fixed':['entire continuous body','accepted R0-A1/R0-A2/R0-A3 geometry','accepted crest','tail','body topology','review cameras','all non-toe retained meshes'],
 'body_geometry_unchanged':True,
 'body_topology_unchanged':True,
 'retained_meshes_unchanged':True,
 'crest_geometry_unchanged':True,
 'tail_geometry_unchanged':True,
 'camera_transforms_unchanged':True,
 'generic_toe_objects_remaining':0,
 'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A5 blocked pending R0-A4 review'
}

with open(os.path.join(OUT,'S-authority-r0-a4-v1-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a4-v1.blend'),compress=True)
print('S_AUTHORITY_R0_A4_V1_EDIT_COMPLETE',json.dumps(report))
