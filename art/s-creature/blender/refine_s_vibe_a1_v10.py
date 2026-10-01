"""Experimental Vibe Gate A1-v10: compact crisp plate crest only.
Source: S-vibe-a1-v9.blend.
All non-crest coordinates are immutable.
Goal: preserve the reference-driven two-primary-plus-subordinate construction,
but remove the oversized rabbit-ear read by lowering/narrowing/bringing the
primary plates closer while keeping real FRONT plate-face width.
"""
import bpy, os, json, hashlib, bmesh, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
old_crest=bpy.data.objects['S_reference_crest_v9']
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

blade_specs=[
  {
    'name':'primary_L',
    'root':(-.022,-.545,1.345),'ctrl':(-.020,-.270,1.455),'tip':(-.016,.115,1.545),
    'widths':(.030,.036,.012),'thickness':(.0040,.0045,.0015),'roll_deg':-48.0
  },
  {
    'name':'primary_R',
    'root':(.022,-.545,1.345),'ctrl':(.020,-.270,1.455),'tip':(.016,.115,1.545),
    'widths':(.030,.036,.012),'thickness':(.0040,.0045,.0015),'roll_deg':48.0
  },
  {
    'name':'sub_L',
    'root':(-.030,-.518,1.326),'ctrl':(-.026,-.305,1.392),'tip':(-.020,.010,1.455),
    'widths':(.022,.028,.010),'thickness':(.0036,.0040,.0014),'roll_deg':-38.0
  },
  {
    'name':'sub_R',
    'root':(.030,-.500,1.316),'ctrl':(.026,-.315,1.372),'tip':(.020,-.020,1.425),
    'widths':(.020,.025,.009),'thickness':(.0034,.0038,.0013),'roll_deg':38.0
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
    cr=max(abs(math.cos(roll)),0.5)
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
        broad=(side_normal*math.cos(roll))+(lateral*sr)
        thin=(lateral*math.cos(roll))-(side_normal*sr)
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
      'name':spec['name'],'root':spec['root'],'ctrl':spec['ctrl'],'tip':spec['tip'],
      'widths':spec['widths'],'roll_deg':spec['roll_deg'],'centers':centers
    })

fm=bpy.data.meshes.new('S_reference_crest_v10_mesh')
fm.from_pydata(verts,[],faces); fm.update()
crest=bpy.data.objects.new('S_reference_crest_v10',fm); cage.objects.link(crest)
for p in fm.polygons: p.use_smooth=False
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
 'gate':'A1-v10-compact-crisp-reference-crest',
 'source':'S-vibe-a1-v9.blend',
 'decision':'REVIEW_PENDING',
 'editable':['crest only'],
 'hard_fixed':['head','neck','thorax','waist','pelvis','limbs','feet','tail'],
 'all_noncrest_geometry_unchanged':True,
 'head_neck_shape_unchanged':True,
 'fixed_geometry_hash':fixed_after,
 'reference_basis':['00_full_reference multi-angle inset','04_crest_structure C5 plate language','01_s_body_primary'],
 'construction':'two close compact broad primary laminae + two shorter subordinate laminae',
 'primary_change':'lower tips, reduced SIDE width, reduced center separation, crisp flat facets',
 'front_goal':'close broad plate pair integrated with skull; no rabbit ears, no thin horns, no single needle',
 'side_goal':'slender rear-swept layered stack',
 'blade_count':len(blade_specs),
 'new_crest_vertex_count':len(fm.vertices),
 'topology_change_scope':'crest object only',
 'blade_meta':meta
}
with open(os.path.join(OUT,'S-vibe-a1-v10-validation.json'),'w') as f:
    json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v10.blend'),compress=True)
print('VIBE_A1_V10_EDIT_COMPLETE',json.dumps(report))
