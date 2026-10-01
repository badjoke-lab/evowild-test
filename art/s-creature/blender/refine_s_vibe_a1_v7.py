"""Experimental Vibe Gate A1-v7: crest-only layered lamina rebuild.
Source: S-vibe-a1-v6.blend.
Preserve every core vertex (head, neck, torso, tail) and every non-crest appendage.
Replace only the v6 four near-parallel curved crest blades with one dominant
rear-upward primary lamina plus three shorter overlapping subordinate layers.
"""
import bpy, os, json, hashlib, bmesh
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
old_crest=bpy.data.objects['S_curved_laminar_crest_v5']
mesh=core.data
assert len(mesh.vertices)==160

# Hard-lock all non-crest geometry, including the accepted v6 head and neck.
core_before=[tuple(v.co) for v in mesh.vertices]
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

# Crest-only replacement.
bpy.data.objects.remove(old_crest, do_unlink=True)

# Quadratic centerline specs in the v6 head coordinate position.
# Width is lamina half-width in the SIDE (Y/Z) plane.
# X thickness/centers remain tightly clustered so FRONT/BACK stays narrow.
blade_specs=[
  {
    'name':'primary',
    'root':(-.015,-.545,1.360),'ctrl':(-.010,-.245,1.535),'tip':(-.006,.135,1.635),
    'widths':(.050,.064,.010),'thickness':(.009,.010,.0022)
  },
  {
    'name':'sub_upper',
    'root':(.018,-.535,1.345),'ctrl':(.014,-.280,1.470),'tip':(.008,.060,1.535),
    'widths':(.043,.050,.008),'thickness':(.008,.0085,.0019)
  },
  {
    'name':'sub_mid',
    'root':(-.038,-.520,1.330),'ctrl':(-.025,-.285,1.420),'tip':(-.010,.020,1.475),
    'widths':(.038,.045,.007),'thickness':(.0075,.008,.0017)
  },
  {
    'name':'sub_low',
    'root':(.040,-.505,1.315),'ctrl':(.026,-.300,1.385),'tip':(.012,-.020,1.430),
    'widths':(.032,.038,.006),'thickness':(.0065,.007,.0015)
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
    rings=[]; centers=[]; start=len(verts)
    for si in range(sections):
        t=si/(sections-1)
        center=qbez(r,q,tip,t)
        tangent=(q-r)*(2*(1-t))+(tip-q)*(2*t)
        tyz=Vector((0,tangent.y,tangent.z))
        if tyz.length==0: tyz=Vector((0,1,0))
        tyz.normalize()
        side_normal=Vector((0,-tyz.z,tyz.y))
        half_w=profile3(spec['widths'],t)
        half_x=profile3(spec['thickness'],t)
        lateral=Vector((1,0,0))
        ring=[]
        for sx,sw in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=center+lateral*(sx*half_x)+side_normal*(sw*half_w)
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring); centers.append(tuple(center))
    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))
    meta.append({
        'name':spec['name'],'start':start,'end':len(verts)-1,
        'root':spec['root'],'ctrl':spec['ctrl'],'tip':spec['tip'],
        'widths':spec['widths'],'centers':centers
    })

fm=bpy.data.meshes.new('S_layered_crest_v7_mesh')
fm.from_pydata(verts,[],faces); fm.update()
crest=bpy.data.objects.new('S_layered_crest_v7',fm); cage.objects.link(crest)
for p in fm.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(fm)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(fm); bm.free()

# Exact hard-lock validation.
assert len(core.data.vertices)==160
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
 'gate':'A1-v7-crest-only-layered-lamina',
 'source':'S-vibe-a1-v6.blend',
 'decision':'REVIEW_PENDING',
 'editable':['crest only'],
 'hard_fixed':['head','neck','thorax','waist','pelvis','limbs','feet','tail'],
 'core_vertex_count':len(core.data.vertices),
 'head_neck_shape_unchanged':True,
 'all_noncrest_geometry_unchanged':True,
 'fixed_geometry_hash':fixed_after,
 'old_crest':'S_curved_laminar_crest_v5 / four near-parallel curved blades',
 'new_crest':'S_layered_crest_v7 / dominant rear-upward primary lamina + 3 shorter overlapping layers',
 'blade_count':len(blade_specs),
 'sections_per_blade':sections,
 'new_crest_vertex_count':len(fm.vertices),
 'front_back_design':'narrow sagittal cluster; no bilateral horn towers',
 'blade_meta':meta,
 'topology_change_scope':'crest object only'
}
with open(os.path.join(OUT,'S-vibe-a1-v7-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v7.blend'),compress=True)
print('VIBE_A1_V7_EDIT_COMPLETE',json.dumps(report))
