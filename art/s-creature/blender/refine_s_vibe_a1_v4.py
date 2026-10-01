"""Experimental Vibe Gate A1-v4: crest topology rebuild only.
Source: S-vibe-a1-v2.blend.
Preserve all first 160 core coordinates (v2 head/neck/body/tail) and every limb/foot mesh.
Remove the bilateral paired 3+3 crest extrusion and replace it with one compact overlapping laminar fan.
"""
import bpy, os, json, hashlib, bmesh
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

def hash_fixed():
    h=hashlib.sha256()
    # All non-crest core coordinates are fixed.
    for i in range(160):
        h.update(core.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(core.data.vertices[i].co)).encode())
    # All separate body appendages are fixed.
    for o in sorted(cage.objects,key=lambda o:o.name):
        if o.type!='MESH' or o==core or o.name=='S_crest_fan_v4': continue
        for i,v in enumerate(o.data.vertices):
            h.update(o.name.encode()); h.update(str(i).encode()); h.update(repr(tuple(v.co)).encode())
    return h.hexdigest()

# Snapshot first 160 coords before topology replacement.
fixed_coords=[tuple(old.vertices[i].co) for i in range(160)]
appendage_counts={o.name:(len(o.data.vertices),len(o.data.polygons)) for o in cage.objects if o.type=='MESH' and o!=core}

# Preserve every face that belongs entirely to the original 160-vertex body.
base_faces=[tuple(p.vertices) for p in old.polygons if all(i<160 for i in p.vertices)]
# Restore the six skull panels that were previously opened for paired crest extrusions.
face_set={tuple(f) for f in base_faces}
for q in ROOT_QUADS:
    if q not in face_set and tuple(reversed(q)) not in face_set:
        base_faces.append(q)

newmesh=bpy.data.meshes.new('S_rebuild_v2_core_without_paired_crest')
newmesh.from_pydata(fixed_coords,[],base_faces); newmesh.update()
for p in newmesh.polygons: p.use_smooth=True
bm=bmesh.new(); bm.from_mesh(newmesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(newmesh); bm.free()
core.data=newmesh

# A single fan object with four non-mirrored/staggered blades.
# Each blade is a tapered 3-section prism that starts slightly inside the rear cranium.
# x centers are deliberately staggered and converge rearward; this avoids bilateral horn towers in FRONT.
blade_specs=[
 # name, [(x,y,z, half_x, half_z), ...]
 ('upper',[
   (-.018,-.655,1.438,.024,.035),
   (-.012,-.355,1.505,.016,.026),
   (-.006, .035,1.565,.003,.005),
 ]),
 ('mid_right',[
   (.034,-.645,1.420,.022,.031),
   (.026,-.330,1.475,.014,.023),
   (.010,-.015,1.525,.003,.005),
 ]),
 ('mid_left',[
   (-.040,-.625,1.405,.020,.028),
   (-.030,-.300,1.452,.013,.020),
   (-.014, .015,1.492,.003,.004),
 ]),
 ('lower',[
   (.018,-.600,1.390,.018,.024),
   (.014,-.265,1.428,.011,.017),
   (.006, .045,1.462,.003,.004),
 ]),
]

verts=[]; faces=[]; blade_ranges=[]
for name,sections in blade_specs:
    start=len(verts)
    rings=[]
    for x,y,z,hx,hz in sections:
        # cross section ordered around y axis
        ring=[
          (x-hx,y,z+hz),(x+hx,y,z+hz),
          (x+hx,y,z-hz),(x-hx,y,z-hz)
        ]
        ids=[]
        for p in ring:
            ids.append(len(verts)); verts.append(p)
        rings.append(ids)
    faces.append(tuple(reversed(rings[0])))
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(4):
            faces.append((a[j],b[j],b[(j+1)%4],a[(j+1)%4]))
    faces.append(tuple(rings[-1]))
    blade_ranges.append({'name':name,'start':start,'end':len(verts)-1,'tip_center':sections[-1][:3]})

fm=bpy.data.meshes.new('S_crest_fan_v4_mesh')
fm.from_pydata(verts,[],faces); fm.update()
fan=bpy.data.objects.new('S_crest_fan_v4',fm); cage.objects.link(fan)
for p in fm.polygons: p.use_smooth=False
bm=bmesh.new(); bm.from_mesh(fm); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(fm); bm.free()

# Confirm fixed coordinates and appendages are identical.
assert len(core.data.vertices)==160
for i,co in enumerate(fixed_coords):
    assert tuple(core.data.vertices[i].co)==co, f'fixed core coord changed {i}'
for o in cage.objects:
    if o.type=='MESH' and o!=core and o!=fan and o.name in appendage_counts:
        assert (len(o.data.vertices),len(o.data.polygons))==appendage_counts[o.name]

fixed_hash=hash_fixed()
report={
 'lane':'exp/s-creature-vibe-modeling',
 'gate':'A1-v4-crest-topology',
 'source':'S-vibe-a1-v2.blend',
 'decision':'REVIEW_PENDING',
 'editable':['crest construction/topology only'],
 'hard_fixed':['all v2 head vertices','all v2 neck vertices','thorax','waist','pelvis','limbs','feet','tail'],
 'old_crest':'bilateral paired 3+3 extrusion / 72 crest vertices',
 'new_crest':'single fan object / four staggered overlapping tapered blades',
 'core_noncrest_vertex_count':160,
 'new_crest_vertex_count':len(fm.vertices),
 'restored_skull_root_panels':len(ROOT_QUADS),
 'fixed_geometry_hash':fixed_hash,
 'fixed_geometry_unchanged':True,
 'blade_ranges':blade_ranges,
 'topology_change_scope':'crest root panels + crest only'
}
with open(os.path.join(OUT,'S-vibe-a1-v4-validation.json'),'w') as f: json.dump(report,f,indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-vibe-a1-v4.blend'),compress=True)
print('VIBE_A1_V4_EDIT_COMPLETE',json.dumps(report))
