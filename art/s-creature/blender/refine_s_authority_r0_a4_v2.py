"""Authority reset R0-A4 v2: integrated split racing feet.

Source: accepted output/S-authority-r0-a3-v2.blend.
R0-A4 v1 is review evidence only and is not geometry input.

Replace 12 generic toe meshes with, per foot:
- 1 proximal base/cuff,
- 2 dominant split blades,
- 1 short rear stabilizer.

Entire continuous body and accepted A1/A2/A3 geometry remain bit-exact.
"""
import bpy,bmesh,os,json,hashlib
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

body_before=[v.co.copy() for v in body.data.vertices]
body_topology=[tuple(p.vertices) for p in body.data.polygons]
body_count=len(body.data.vertices)

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

FEET=[
 ('fore','L',-0.150,-0.268),
 ('fore','R', 0.150,-0.268),
 ('hind','L',-0.150, 0.970),
 ('hind','R', 0.150, 0.970),
]

def loft_blade(name,centers,widths,depths):
    assert len(centers)==len(widths)==len(depths)>=2
    C=[Vector(c) for c in centers]
    verts=[]; faces=[]; rings=[]
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
    dominant_len=0.165 if family=='fore' else 0.155

    # Integrated proximal base/cuff: visually substantial and low,
    # overlapping the ankle endpoint and feeding the split pair.
    base_centers=[
      (x0, y0+0.006, 0.078),
      (x0, y0-0.022, 0.056),
      (x0, y0-0.052, 0.040),
    ]
    base=loft_blade(
      f'S_racing_foot_v2_{family}_{side}_base',
      base_centers,
      [0.021,0.027,0.030],
      [0.018,0.022,0.019]
    )
    new_objects.append(base)

    prong_tips=[]
    for split,label in [(-1,'A'),(1,'B')]:
        centers=[
          (x0+split*0.012, y0-0.030, 0.050),
          (x0+split*0.021, y0-dominant_len*0.50, 0.028),
          (x0+split*0.032, y0-dominant_len, 0.012),
        ]
        o=loft_blade(
          f'S_racing_foot_v2_{family}_{side}_prong_{label}',
          centers,
          [0.0145,0.0175,0.0080],
          [0.0200,0.0220,0.0075]
        )
        new_objects.append(o)
        prong_tips.append(Vector(centers[-1]))

    tip_sep=(prong_tips[0]-prong_tips[1]).length
    assert 0.058 <= tip_sep <= 0.074,tip_sep

    spur_len=0.048
    spur=loft_blade(
      f'S_racing_foot_v2_{family}_{side}_rear_spur',
      [
        (x0,y0+0.004,0.061),
        (x0,y0+spur_len*0.55,0.038),
        (x0,y0+spur_len,0.024),
      ],
      [0.0105,0.0090,0.0045],
      [0.0120,0.0090,0.0040]
    )
    new_objects.append(spur)

    ratio=spur_len/dominant_len
    assert ratio < 0.33,ratio

    foot_meta.append({
      'family':family,'side':side,
      'attachment':[x0,y0,0.060],
      'base_length':0.058,
      'dominant_prong_length':dominant_len,
      'dominant_tip_separation':tip_sep,
      'dominant_tip_min_z':0.012,
      'rear_spur_length':spur_len,
      'rear_spur_length_ratio':ratio
    })

assert len(new_objects)==16
assert not [o.name for o in cage.objects if '_toe_' in o.name]

# Entire body remains exact.
assert len(body.data.vertices)==body_count
assert [tuple(p.vertices) for p in body.data.polygons]==body_topology
for i,co in enumerate(body_before):
    assert tuple(body.data.vertices[i].co)==tuple(co),f'body changed {i}'

# Every retained mesh remains exact.
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
 'gate':'R0-A4-v2-authority-integrated-split-racing-feet',
 'status':'REVIEW_PENDING',
 'decision':'REVIEW_PENDING',
 'authority_image':'references/00_s_type_modeling_image_v1.png',
 'authority_sha256':AUTH_SHA,
 'source':'S-authority-r0-a3-v2.blend',
 'source_role':'accepted R0-A3 source; R0-A4 v1 not used as geometry input',
 'accepted_prior_gates':['R0-A1','R0-A2','R0-A3'],
 'output':'S-authority-r0-a4-v2.blend',
 'scope':'replace generic toe appendages with integrated split racing feet only',
 'removed_generic_toes':old_toe_names,
 'removed_generic_toe_count':len(old_toe_names),
 'new_foot_object_count':len(new_objects),
 'new_foot_objects':[o.name for o in new_objects],
 'foot_meta':foot_meta,
 'objects_per_foot':4,
 'dominant_prongs_per_foot':2,
 'base_objects_per_foot':1,
 'rear_stabilizers_per_foot':1,
 'hard_fixed':['entire continuous body','accepted R0-A1/R0-A2/R0-A3 geometry','crest','tail','body topology','review cameras','all retained non-toe meshes'],
 'body_geometry_unchanged':True,
 'body_topology_unchanged':True,
 'retained_meshes_unchanged':True,
 'crest_geometry_unchanged':True,
 'tail_geometry_unchanged':True,
 'camera_transforms_unchanged':True,
 'generic_toe_objects_remaining':0,
 'v1_review':'S_AUTHORITY_R0_A4_V1_REVIEW.md',
 'stop_rule':'render SIDE/FRONT/FRONT34/REAR34/BACK and STOP; R0-A5 blocked pending R0-A4 v2 review'
}

with open(os.path.join(OUT,'S-authority-r0-a4-v2-validation.json'),'w') as f:
    json.dump(report,f,indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-authority-r0-a4-v2.blend'),compress=True)
print('S_AUTHORITY_R0_A4_V2_EDIT_COMPLETE',json.dumps(report))
