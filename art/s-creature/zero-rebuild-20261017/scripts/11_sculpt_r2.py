"""Edit the saved R1 copy in live Blender MCP. Never runs a source generator.

Local shoulder fairing + exact unions, and frontal crown section sculpt only.
Writes a review trial, not the accepted R2. All source artifacts are immutable.
"""
import bpy
import bmesh
import hashlib
import json
import math
import struct
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / 'verification/S_ZERO_R2_TRIAL_A.blend'
assert Path(bpy.data.filepath).name == 'S_ZERO_R2_WORKING_COPY.blend'
assert hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest() == 'f8e8a80360ee5886d485a17610cf62a9387d10cdb09e4801a055be99bf8d8a4f'
assert not TRIAL.exists()
model = bpy.data.collections['S_ZERO_CREATURE']
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
shoulders = ['SCAPULA_N', 'DELTOID_N', 'BRACHIAL_FORE_NEAR',
             'SCAPULA_F', 'DELTOID_F', 'BRACHIAL_FORE_FAR']
crowns = [f'CROWN_{part}_{side}' for side in ['N', 'F'] for part in ['MAIN', 'BLUE', 'IVORY_RIDGE']]


def signature(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices:
        h.update(struct.pack('<3f', *v.co))
    for p in obj.data.polygons:
        h.update(struct.pack('<' + 'I' * len(p.vertices), *p.vertices))
        h.update(struct.pack('<I?', p.material_index, p.use_smooth))
    for row in obj.matrix_world:
        h.update(struct.pack('<4f', *row))
    return h.hexdigest()


def ease(t):
    t = max(0, min(1, t))
    return t*t*(3-2*t)


before = {o.name: signature(o) for o in model.objects if o.type == 'MESH'}
original_body = [tuple(v.co) for v in body.data.vertices]
source_coords = {tuple(v.co) for name in [body.name] + shoulders for v in bpy.data.objects[name].data.vertices}
changes = []

# Reshape existing shoulder volumes into a flatter, tapered plane. Upper arm
# moves towards its own flesh core before fusion; no distant surface projection.
for name in shoulders:
    obj = bpy.data.objects[name]
    old = [v.co.copy() for v in obj.data.vertices]
    side = -1 if name.endswith(('_N', '_NEAR')) else 1
    for v in obj.data.vertices:
        x, y, z = v.co
        if name.startswith('DELTOID'):
            outer = ease((abs(y) - .20) / .23)
            v.co.y -= side * .035 * outer
            upper = ease((z - 1.64) / .33)
            v.co.x += .025 * upper
            # Less bulbous frontal apex, retain the supported arm-root volume.
            v.co.y -= side * .012 * upper * outer
        elif name.startswith('BRACHIAL'):
            upper = ease((z - 1.07) / .43)
            v.co.y -= side * (.012 + .038 * upper)
            v.co.z += .015 * upper
        elif name.startswith('SCAPULA'):
            v.co.y -= side * .012 * ease((abs(y) - .19) / .20)
    obj.data.update()
    changes.append({'object': name, 'operation': 'existing vertex sculpt then exact union into body',
                    'max_sculpt_displacement': max((v.co-p).length for v,p in zip(obj.data.vertices,old))})

# Store sculpted vertex coordinates so boolean-created seam vertices can be found.
source_coords = {tuple(v.co) for name in [body.name] + shoulders for v in bpy.data.objects[name].data.vertices}
for name in shoulders:
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    mod = body.modifiers.new('R2 local anatomical union ' + name, 'BOOLEAN')
    assert 'UNION' in [i.identifier for i in mod.bl_rna.properties['operation'].enum_items]
    assert 'EXACT' in [i.identifier for i in mod.bl_rna.properties['solver'].enum_items]
    mod.operation = 'UNION'
    mod.solver = 'EXACT'
    mod.object = obj
    assert 'TRANSFER' in [i.identifier for i in mod.bl_rna.properties['material_mode'].enum_items]
    mod.material_mode = 'TRANSFER'
    # Boolean material transfer uses matching named slots.
    for mat in obj.data.materials:
        if mat.name not in [m.name for m in body.data.materials]:
            body.data.materials.append(mat)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(obj, do_unlink=True)

# Fair the cut seams within 65 mm only. Do not voxel-remesh the whole creature.
bm = bmesh.new()
bm.from_mesh(body.data)
bm.verts.ensure_lookup_table()
seams = [v for v in bm.verts if tuple(v.co) not in source_coords]
kd = KDTree(len(seams))
for i,v in enumerate(seams):
    kd.insert(v.co,i)
kd.balance()
weights = {}
for v in bm.verts:
    x,y,z = v.co
    if not (-1.23 < x < -.36 and 1.00 < z < 2.10 and abs(y) > .12):
        continue
    if seams:
        _,_,dist = kd.find(v.co)
        w = 1-ease(dist/.065)
        if w > 0:
            weights[v] = w
for _ in range(7):
    targets = {}
    for v,w in weights.items():
        neighbors = [e.other_vert(v).co for e in v.link_edges]
        if neighbors:
            avg = sum(neighbors, Vector())/len(neighbors)
            targets[v] = v.co.lerp(avg, .38*w)
    for v,co in targets.items():
        v.co = co
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
fairing_count = len(weights)
bm.to_mesh(body.data)
bm.free()
body.data.update()

# Front-facing lenticular crown sections. Sagittal X/Z outline is unchanged.
outline = [(-2.19,2.19),(-1.98,2.43),(-1.65,2.64),(-1.18,2.83),(-.62,3.00),(-.08,3.11),(-.70,2.89),(-1.25,2.67),(-1.69,2.42),(-1.98,2.23)]


def section_x(z):
    hits=[]
    for (x1,z1),(x2,z2) in zip(outline,outline[1:]+outline[:1]):
        if min(z1,z2) <= z <= max(z1,z2) and abs(z2-z1)>1e-6:
            hits.append(x1+(x2-x1)*(z-z1)/(z2-z1))
    return (min(hits),max(hits)) if hits else (0,0)


for name in crowns:
    obj=bpy.data.objects[name]
    side=-1 if name.endswith('_N') else 1
    old=[v.co.copy() for v in obj.data.vertices]
    for v in obj.data.vertices:
        x,y,z=v.co
        t=max(0,min(1,(z-2.19)/.92))
        lo,hi=section_x(z)
        q=max(0,min(1,(x-lo)/max(.001,hi-lo)))
        envelope=math.sin(math.pi*t)**1.35
        v.co.y += side*envelope*(.025+.105*(.5-q))
    obj.data.update()
    assert all(v.co.x==p.x and v.co.z==p.z for v,p in zip(obj.data.vertices,old))
    changes.append({'object':name,'operation':'lateral crown section widening; same X/Z outline',
                    'max_sculpt_displacement':max((v.co-p).length for v,p in zip(obj.data.vertices,old))})

after = {o.name:signature(o) for o in model.objects if o.type=='MESH'}
untouched = sorted(set(before)-set(shoulders)-set(crowns)-{body.name})
assert all(before[n]==after[n] for n in untouched)
remaining_coords={tuple(v.co) for v in body.data.vertices}
# Scapula joins remove 26 covered core vertices at |Y|=.102-.120 as well.
# Include that medial attachment in the permitted shoulder region; the smoothing
# radius itself above remains limited to |Y|>.12.
outside=[p for p in original_body if not (-1.23<p[0]<-.36 and 1.00<p[2]<2.10 and abs(p[1])>.095)]
assert all(p in remaining_coords for p in outside), 'Union affected unrelated body vertices'
body['r2_edit']='Existing R1 shoulder/scapula/upper-arm union + local seam fairing; no whole-body remesh'
sc=bpy.context.scene
sc['stage']='R2_TRIAL_A'
sc['candidate_status']='REVISE; local shape trial awaiting real render review'
sc.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(TRIAL),compress=True)
report={'source':'S_ZERO_CANDIDATE_REVISED_R1.blend','trial':str(TRIAL.relative_to(ROOT)),
        'source_sha256':'f8e8a80360ee5886d485a17610cf62a9387d10cdb09e4801a055be99bf8d8a4f',
        'changed_parts':changes,'body_union_inputs':shoulders,'seam_vertices':len(seams),
        'locally_faired_vertices':fairing_count,'unchanged_mesh_count':len(untouched),
        'unchanged_meshes':untouched,'before_signatures':before,'after_signatures':after,
        'unrelated_body_vertices_exactly_preserved':len(outside),
        'body_vertices':len(body.data.vertices),'body_faces':len(body.data.polygons),
        'crown_side_outline_preserved':True,'decision':'Pending visual review'}
(ROOT/'evidence/REVISION_R2_TRIAL_A.json').write_text(json.dumps(report,indent=2)+'\n')
print('R2_TRIAL_A_SAVED',len(untouched),'unchanged meshes;',fairing_count,'fairing verts;',len(outside),'protected body verts')
