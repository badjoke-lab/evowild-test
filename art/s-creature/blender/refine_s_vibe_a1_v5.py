"""Experimental Vibe Gate A1-v5: curved tapered laminar crest blades only.
Source: S-vibe-a1-v2.blend. Preserve all v2 head/neck/body/tail coordinates and every limb/foot mesh.
"""
import bpy, os, json, hashlib, bmesh, math
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
old=core.data
assert len(old.vertices)==232

ROOT_QUADS=[
 (16,24,25,17),(17,25,26,18),(18,26,27,19),
 (19,27,28,20),(24,32,33,25),(27,35,36,28)
]

# Snapshot fixed geometry.
fixed_coords=[tuple(old.vertices[i].co) for i in range(160)]
appendage_snapshot={}
for o in cage.objects:
    if o.type=='MESH' and o!=core:
        appendage_snapshot[o.name]=[
            tuple(v.co) for v in o.data.vertices
        ]

# Remove the old paired crest topology while preserving all non-crest coordinates.
base_faces=[tuple(p.vertices) for p in old.polygons if all(i<160 for i in p.vertices)]
existing={tuple(f) for f in base_faces}
for q in ROOT_QUADS:
    if q not in existing and tuple(reversed(q)) not in existing:
        base_faces.append(q)
newmesh=bpy.data.meshes.new('S_rebuild_v2_core_curved_crest_base')
newmesh.from_pydata(fixed_coords,[],base_faces); newmesh.update()
for p in newmesh.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(newmesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(newmesh); bm.free()
core.data=newmesh

# Curved blade definition: root/control/tip centers, root half-width, lateral half-thickness.
# Width is measured perpendicular to the centerline in the SIDE (Y/Z) plane.
blade_specs=[
  {
    'name':'blade_A',
    'root':(-.040,-.655,1.405),'ctrl':(-.038,-.345,1.485),'tip':(-.032,.005,1.535),
    'root_width':.052,'root_thickness':.009
  },
  {
    'name':'blade_B',
    'root':(-.012,-.650,1.420),'ctrl':(-.010,-.335,1.490),'tip':(-.014,-.015,1.510),
    'root_width':.048,'root_thickness':.008
  },
  {
    'name':'blade_C',
    'root':(.020,-.635,1.405),'ctrl':(.024,-.315,1.465),'tip':(.020,.018,1.485),
    'root_width':.044,'root_thickness':.008
  },
  {
    'name':'blade_D',
    'root':(.050,-.610,1.385),'ctrl':(.048,-.290,1.435),'tip':(.043,.035,1.455),
    'root_width':.040,'root_thickness':.007
  },
]

def qbez(a,b,c,t):
    u=1.0-t
    return a*(u*u)+b*(2*u*t)+c*(t*t)

verts=[]; faces=[]; blade_meta=[]
sections=7
for spec in blade_specs:
    r=Vector(spec['root']); q=Vector(spec['ctrl']); tip=Vector(spec['tip'])
    rings=[]
    start=len(verts)
    centers=[]
    for si in range(sections):
        t=si/(sections-1)
        center=qbez(r,q,tip,t)
        # Analytical tangent of quadratic Bezier.
        tangent=(q-r)*(2*(1-t))+(tip-q)*(2*t)
        tyz=Vector((0,tangent.y,tangent.z))
        if tyz.length==0: tyz=Vector((0,1,0))
        tyz.normalize()
        normal=Vector((0,-tyz.z,tyz.y))
        width=spec['root_width']*((1-t)**0.72)+.0025*t
        thick=spec['root_thickness']*((1-t)**0.85)+.0012*t
        lateral=Vector((1,0,0))
        ring=[]
        for sx,sw in [(-1,1),(1,1),(1,-1),(-1,-1)]:
            p=center+lateral*(sx*thick)+normal*(sw*width)
            ring.append(len(verts)); verts.append(tuple(p))
        rings.append(ring); centers.append(tuple(center))
    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))
    blade_meta.append({'name':spec['name'],'start':start,'end':len(verts)-1,'centers':centers})

fm=bpy.data.meshes.new('S_curved_laminar_crest_v5_mesh')
fm.from_pydata(verts,[],faces); fm.update()
fan=bpy.data.objects.new('S_curved_laminar_crest_v5',fm); cage.objects.link(fan)
for p in fm.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(fm); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(fm); bm.free()

# Fixed-geometry validation.
assert len(core.data.vertices)==160
for i,co in enumerate(fixed_coords):
    assert tuple(core.data.vertices[i].co)==co, f'fixed core coordinate changed: {i}'
for name,coords in appendage_snapshot.items():
    o=bpy.data.objects[name]
    assert len(o.data.vertices)==len(coords)
    for i,co in enumerate(coords):
        assert tuple(o.data.vertices[i].co)==co, f'appendage changed: {name}:{i}'

def fixed_hash():
    h=hashlib.sha256()
    for i in range(160):
        h.update(str(i).encode()); h.update(repr(tuple(core.data.vertices[i].co)).encode())
    for name in sorted(appendage_snapshot):
        o=bpy.data.objects[name]
        for i,v in enumerate(o.data.vertices):
            h.update(name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v5-curved-laminar-crest',
 'source':'S-vibe-a1-v2.blend',
 'decision':'REVIEW_PENDING',
 'editable':['crest representation/topology only'],
 'hard_fixed':['all v2 head/neck coordinates','thorax','waist','pelvis','limbs','feet','tail'],
 'representation':'quadratic centerline + perpendicular tapering ribbon prism',
 'blade_count':len(blade_specs),
 'sections_per_blade':sections,
 'new_crest_vertex_count':len(fm.vertices),
 'restored_skull_root_panels':len(ROOT_QUADS),
 'fixed_geometry_hash':fixed_hash(),
 'fixed_geometry_unchanged':True,
 'blade_meta':blade_meta,
 'topology_change_scope':'crest root panels + crest only'
}
with open(os.path.join(OUT,'S-vibe-a1-v5-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v5.blend'),compress=True)
print('VIBE_A1_V5_EDIT_COMPLETE',json.dumps(report))
