"""Experimental Vibe Gate A1-v8: crest face-orientation correction only.
Source: S-vibe-a1-v7.blend.
Preserve every non-crest coordinate. Keep the v7 crest centerline family and SIDE
silhouette width, but roll the lamina broad faces so FRONT/BACK see layered plate
surfaces rather than edge-on horn needles.
"""
import bpy, os, json, hashlib, bmesh, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
old_crest=bpy.data.objects['S_layered_crest_v7']
assert len(core.data.vertices)==160

core_before=[tuple(v.co) for v in core.data.vertices]
appendage_before={}
for o in cage.objects:
    if o.type=='MESH' and o not in (core,old_crest):
        appendage_before[o.name]=[tuple(v.co) for v in o.data.vertices]

def fixed_hash():
    h=hashlib.sha256()
    for i,v in enumerate(core.data.vertices):
        h.update(core.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    for name in sorted(appendage_before):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

fixed_before=fixed_hash()
bpy.data.objects.remove(old_crest,do_unlink=True)

# Same v7 centerline family. Only plate-face roll/orientation is changed.
blade_specs=[
  {
    'name':'primary',
    'root':(-.015,-.545,1.360),'ctrl':(-.010,-.245,1.535),'tip':(-.006,.135,1.635),
    'widths':(.050,.064,.010),'thickness':(.009,.010,.0022),'roll_deg':28.0
  },
  {
    'name':'sub_upper',
    'root':(.018,-.535,1.345),'ctrl':(.014,-.280,1.470),'tip':(.008,.060,1.535),
    'widths':(.043,.050,.008),'thickness':(.008,.0085,.0019),'roll_deg':-24.0
  },
  {
    'name':'sub_mid',
    'root':(-.038,-.520,1.330),'ctrl':(-.025,-.285,1.420),'tip':(-.010,.020,1.475),
    'widths':(.038,.045,.007),'thickness':(.0075,.008,.0017),'roll_deg':20.0
  },
  {
    'name':'sub_low',
    'root':(.040,-.505,1.315),'ctrl':(.026,-.300,1.385),'tip':(.012,-.020,1.430),
    'widths':(.032,.038,.006),'thickness':(.0065,.007,.0015),'roll_deg':-16.0
  },
]

def qbez(a,b,c,t):
    u=1.0-t
    return a*(u*u)+b*(2*u*t)+c*(t*t)

def profile3(vals,t):
    a,b,c=vals
    if t<=0.45:
        s=t/0.45
        return a+(b-a)*s
    s=(t-0.45)/0.55
    return b+(c-b)*s

verts=[]; faces=[]; meta=[]
sections=8
for spec in blade_specs:
    r=Vector(spec['root']); q=Vector(spec['ctrl']); tip=Vector(spec['tip'])
    roll=math.radians(spec['roll_deg'])
    cr=max(math.cos(roll),0.5)
    sr=math.sin(roll)
    rings=[]; centers=[]; start=len(verts)
    for si in range(sections):
        t=si/(sections-1)
        center=qbez(r,q,tip,t)
        tangent=(q-r)*(2*(1-t))+(tip-q)*(2*t)
        tyz=Vector((0,tangent.y,tangent.z))
        if tyz.length==0: tyz=Vector((0,1,0))
        tyz.normalize()
        side_normal=Vector((0,-tyz.z,tyz.y))
        lateral=Vector((1,0,0))

        # Rotate the broad lamina axis around the centerline. Compensate width by
        # cos(roll) so the Y/Z (SIDE) silhouette width stays approximately v7.
        broad=(side_normal*cr)+(lateral*sr)
        thin=(lateral*cr)-(side_normal*sr)
        broad.normalize(); thin.normalize()
        side_half=profile3(spec['widths'],t)
        half_w=side_half/cr
        half_t=profile3(spec['thickness'],t)

        ring=[]
        for sb,st in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=center+broad*(sb*half_w)+thin*(st*half_t)
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring); centers.append(tuple(center))
    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))
    meta.append({
      'name':spec['name'],'roll_deg':spec['roll_deg'],
      'root':spec['root'],'ctrl':spec['ctrl'],'tip':spec['tip'],
      'widths':spec['widths'],'centers':centers
    })

fm=bpy.data.meshes.new('S_layered_crest_v8_mesh')
fm.from_pydata(verts,[],faces); fm.update()
crest=bpy.data.objects.new('S_layered_crest_v8',fm); cage.objects.link(crest)
for p in fm.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(fm)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(fm); bm.free()

for i,co in enumerate(core_before):
    assert tuple(core.data.vertices[i].co)==co, f'core changed {i}'
for name,coords in appendage_before.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==co, f'appendage changed {name}:{i}'
fixed_after=fixed_hash()
assert fixed_after==fixed_before

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v8-crest-face-orientation',
 'source':'S-vibe-a1-v7.blend',
 'decision':'REVIEW_PENDING',
 'editable':['crest only'],
 'hard_fixed':['head','neck','thorax','waist','pelvis','limbs','feet','tail'],
 'all_noncrest_geometry_unchanged':True,
 'head_neck_shape_unchanged':True,
 'fixed_geometry_hash':fixed_after,
 'centerline_family':'identical to v7',
 'side_width_policy':'compensated to preserve v7 Y/Z silhouette width',
 'face_orientation_change':'controlled lamina roll around each blade centerline',
 'roll_degrees':{s['name']:s['roll_deg'] for s in blade_specs},
 'front_back_goal':'show overlapping plate width; avoid central needle and bilateral horn towers',
 'blade_count':len(blade_specs),
 'new_crest_vertex_count':len(fm.vertices),
 'topology_change_scope':'crest object only',
 'blade_meta':meta
}
with open(os.path.join(OUT,'S-vibe-a1-v8-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v8.blend'),compress=True)
print('VIBE_A1_V8_EDIT_COMPLETE',json.dumps(report))
