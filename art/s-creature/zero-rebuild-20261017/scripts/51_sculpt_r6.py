"""R6 pelvis edit, executed in live Blender through MCP on the protected R5 copy.

Reshape existing pelvic volumes, exact-union them into the existing skin, and
fair only the new hip seams. No source generator or whole-body remeshing.
"""
import bpy, bmesh, hashlib, json, math, struct
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
TRIAL = globals().get('TRIAL', 'A')
OUT = ROOT / f'verification/S_ZERO_R6_TRIAL_{TRIAL}.blend'
REPORT = ROOT / f'evidence/SCULPT_R6_TRIAL_{TRIAL}.json'
assert bpy.app.version == (4, 3, 2)
assert not OUT.exists() and not REPORT.exists()
source = ROOT / 'verification/S_ZERO_R6_WORKING_COPY.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '87fd6732a682ece45733e1c9ad78861a6b2543259c5feae38ba506fe6a509923'
bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False)
body = bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
model = bpy.data.collections['S_ZERO_CREATURE']
targets = ['PELVIS_N', 'PELVIS_F', 'SACRAL_MANTLE']

def ease(t):
    t = max(0., min(1., t)); return t*t*(3.-2.*t)

def signature(ob):
    h = hashlib.sha256()
    for v in ob.data.vertices: h.update(struct.pack('<3f', *v.co))
    for p in ob.data.polygons:
        h.update(struct.pack('<'+'I'*len(p.vertices), *p.vertices))
        h.update(struct.pack('<I?', p.material_index, p.use_smooth))
    for row in ob.matrix_world: h.update(struct.pack('<4f', *row))
    for a in ob.data.color_attributes:
        h.update(a.name.encode())
        for d in a.data: h.update(struct.pack('<4f', *d.color))
    return h.hexdigest()

def tail(p):
    x, y, z = p
    return x > 1.07 and z > 1.78-.75*(x-1.12)

def region(p):
    x, y, z = p
    return .18 < x < 1.34 and 1.10 < z < 2.10 and not tail(p)

before = {o.name:signature(o) for o in model.objects if o.type == 'MESH'}
old_body = [tuple(v.co) for v in body.data.vertices]
original_mesh = body.data.copy()
frozen_rim=set()
for p in original_mesh.polygons:
    coords=[tuple(original_mesh.vertices[i].co) for i in p.vertices]
    if any(region(c) for c in coords) and not all(region(c) for c in coords):
        frozen_rim.update(coords)
changes = []
palette_shells={}
for name in targets:
    ob = bpy.data.objects[name]
    old = [v.co.copy() for v in ob.data.vertices]
    if name.startswith('PELVIS'):
        side = -1 if name.endswith('_N') else 1
        for v in ob.data.vertices:
            x,y,z = v.co
            outer = ease((abs(y)-.16)/.32)
            upper = ease((z-1.65)/.32)
            lower = ease((1.62-z)/.40)
            # Flatten the lateral bulb and bury the distal cap into its thigh.
            flatten, distal = (.030,.012) if TRIAL=='B' else (.052,.027)
            v.co.y -= side*(flatten*outer + distal*lower*ease((abs(y)-.18)/.18))
            # Lengthen the upper transition towards the waist, retaining the
            # original thigh endpoints and the staggered standing pose.
            v.co.x -= .034*upper
            v.co.z -= .014*upper
    else:
        for v in ob.data.vertices:
            v.co.z -= .010*ease((v.co.z-1.94)/.07)
    ob.data.update()
    if name.startswith('PELVIS'):
        palette_shells[side]=(BVHTree.FromPolygons([v.co.copy() for v in ob.data.vertices],
            [tuple(p.vertices) for p in ob.data.polygons]),
            [p.material_index for p in ob.data.polygons],list(ob.data.materials))
    changes.append({'object':name, 'operation':'existing vertex reshape then exact union into body',
                    'max_sculpt_displacement':max((v.co-p).length for v,p in zip(ob.data.vertices,old))})

# Fill only the underlying hip transition, with a smooth bounded influence.
core_changes = []
for v in body.data.vertices:
    x,y,z = v.co
    if not region(v.co) or z < 1.30 or tuple(v.co) in frozen_rim: continue
    w = math.exp(-((x-.79)/.30)**2-((z-1.63)/.27)**2)
    w *= ease((abs(y)-.12)/.20)*ease((x-.25)/.18)*ease((1.30-x)/.18)
    if w > .001:
        v.co.y += math.copysign((.008 if TRIAL=='B' else .018)*w,y)
        core_changes.append(v.index)
body.data.update()
source_coords = {tuple(v.co) for n in [body.name]+targets for v in bpy.data.objects[n].data.vertices}
for name in targets:
    ob = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.context.view_layer.update()
    mod = body.modifiers.new('R6 local pelvis union '+name, 'BOOLEAN')
    for prop,value in [('operation','UNION'),('solver','EXACT'),('material_mode','TRANSFER')]:
        assert value in [i.identifier for i in mod.bl_rna.properties[prop].enum_items]
        setattr(mod,prop,value)
    mod.object = ob
    for m in ob.data.materials:
        if m.name not in [x.name for x in body.data.materials]: body.data.materials.append(m)
    with bpy.context.temp_override(object=body, active_object=body,
            selected_objects=[body], selected_editable_objects=[body]):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(ob, do_unlink=True)

bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
seams = [v.co.copy() for v in bm.verts if tuple(v.co) not in source_coords]
assert seams
kd = KDTree(len(seams))
for i,p in enumerate(seams): kd.insert(p,i)
kd.balance()
# Tessellate the original Boolean cut polygons before fairing changes their
# planarity. This avoids invalid diagonals across concave smoothed n-gons.
ngons=[f for f in bm.faces if len(f.verts)>4 and all(region(v.co) for v in f.verts)]
bmesh.ops.triangulate(bm, faces=ngons)
bm.verts.index_update(); bm.normal_update()
# Exact Boolean cuts may contain a zero-thickness doubled triangular fin.
# Remove both opposing coincident faces only, then their unused edges. This
# is local geometric cleanup, not an arbitrary removal of nonmanifold faces.
coincident={}
for f in bm.faces:
    if all(region(v.co) for v in f.verts):
        coincident.setdefault(tuple(sorted(v.index for v in f.verts)),[]).append(f)
double_faces=[]
for fs in coincident.values():
    if len(fs)==2 and fs[0].normal.dot(fs[1].normal)<-.99:
        double_faces.extend(fs)
if double_faces: bmesh.ops.delete(bm, geom=double_faces, context='FACES_ONLY')
unused=[e for e in bm.edges if not e.link_faces and all(region(v.co) for v in e.verts)]
if unused: bmesh.ops.delete(bm, geom=unused, context='EDGES')
unused_v=[v for v in bm.verts if not v.link_edges and region(v.co)]
if unused_v: bmesh.ops.delete(bm, geom=unused_v, context='VERTS')
assert all(e.is_manifold for e in bm.edges), 'Pre-fairing triangulation invalid'
# Local cuts only: eliminate long boolean edges across the deforming junction.
subdivided = 0
for _ in range(2):
    edges = [e for e in bm.edges if e.calc_length() > .046
        and all(region(v.co) for v in e.verts)
        and not any(tuple(v.co) in frozen_rim for v in e.verts)
        and min(kd.find(v.co)[2] for v in e.verts) < .10]
    if not edges: break
    subdivided += len(edges)
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True)
weights = {v:1-ease(kd.find(v.co)[2]/.095) for v in bm.verts if region(v.co) and tuple(v.co) not in frozen_rim and kd.find(v.co)[2]<.095}
for _ in range(10):
    updates={}
    for v,w in weights.items():
        neighbors=[e.other_vert(v).co for e in v.link_edges]
        if neighbors: updates[v]=v.co.lerp(sum(neighbors,Vector())/len(neighbors),.36*w)
    for v,co in updates.items(): v.co=co
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
# Triangulating boolean n-gons can leave unused diagonals; remove only local
# zero-face edges, never boundaries or edges shared by more than two faces.
loose_edges = [e for e in bm.edges if not e.link_faces and all(region(v.co) for v in e.verts)]
if loose_edges: bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')
loose_vertices = [v for v in bm.verts if not v.link_edges and region(v.co)]
if loose_vertices: bmesh.ops.delete(bm, geom=loose_vertices, context='VERTS')
health={'boundary_edges':sum(e.is_boundary for e in bm.edges),
        'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
assert all(v==0 for v in health.values()), (health, [(len(e.link_faces),[list(v.co) for v in e.verts]) for e in bm.edges if not e.is_manifold][:10])
fairing_count=len(weights)
bm.to_mesh(body.data);bm.free();body.data.update()
# Blender's Exact Boolean may also retessellate pre-existing shoulder cuts.
# Graft ONLY the edited pelvic patch onto the original unmodified surface.
# Coordinates at its boundary must match exactly; manifold checks below catch
# any failed stitch. Preserve every original material, smooth flag and corner
# color outside the patch, including the R2 shoulder palette.
edited_mesh=body.data
vs=[];fs=[];lookup={};face_data=[]
attr_names={a.name:(a.data_type,a.domain) for a in original_mesh.color_attributes}
assert all(domain=='CORNER' for _,domain in attr_names.values())
for mesh,want_local in [(original_mesh,False),(edited_mesh,True)]:
    for p in mesh.polygons:
        is_local=all(region(mesh.vertices[i].co) for i in p.vertices)
        if is_local!=want_local: continue
        indices=[]
        for i in p.vertices:
            co=tuple(mesh.vertices[i].co)
            if co not in lookup: lookup[co]=len(vs);vs.append(co)
            indices.append(lookup[co])
        fs.append(indices)
        colors={n:[tuple(mesh.color_attributes[n].data[li].color) for li in p.loop_indices]
                for n in attr_names if n in mesh.color_attributes}
        face_data.append((p.material_index,p.use_smooth,colors))
graft=bpy.data.meshes.new('S_ZERO_R6_pelvis_local_graft')
graft.from_pydata(vs,[],fs)
for m in edited_mesh.materials:graft.materials.append(m)
for n,(data_type,domain) in attr_names.items():graft.color_attributes.new(name=n,type=data_type,domain=domain)
for p,(mi,smooth,colors) in zip(graft.polygons,face_data):
    p.material_index=mi;p.use_smooth=smooth
    for n,values in colors.items():
        for li,col in zip(p.loop_indices,values):graft.color_attributes[n].data[li].color=col
body.data=graft;graft.update()
check=bmesh.new();check.from_mesh(graft)
assert all(e.is_manifold for e in check.edges), ('Local patch stitch failed',sum(not e.is_manifold for e in check.edges))
check.free()
bpy.data.meshes.remove(original_mesh)
if edited_mesh.users==0:bpy.data.meshes.remove(edited_mesh)
palette_report=None
if TRIAL=='B':
    # Transfer the existing ivory pattern onto the actual welded surface.
    # The A trial showed that buried source faces otherwise cause large dark
    # bites. This changes color on continuous geometry; it does not cover gaps.
    mesh=body.data;mesh.update()
    colors=[]
    for m in mesh.materials:
        bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        colors.append(Vector(bs.inputs['Base Color'].default_value[:3]))
    faces=[[] for _ in mesh.vertices];neighbors=[set() for _ in mesh.vertices]
    for p in mesh.polygons:
        for i in p.vertices:faces[i].append(p)
    for e in mesh.edges:
        a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
    vc=[];painted=[]
    for v,linked in zip(mesh.vertices,faces):
        weights=[max(p.area,1e-12) for p in linked]
        col=sum((colors[p.material_index]*w for p,w in zip(linked,weights)),Vector())/sum(weights)
        if region(v.co) and abs(v.co.y)>.13:
            side=-1 if v.co.y<0 else 1
            tree,indices,mats=palette_shells[side]
            hit,normal,fi,dist=tree.ray_cast(Vector((v.co.x,side*1.5,v.co.z)),Vector((0,-side,0)),3.)
            if hit is not None and abs(v.co.y-hit.y)<.13 and side*v.normal.y>-.05:
                bs=next(n for n in mats[indices[fi]].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
                col=Vector(bs.inputs['Base Color'].default_value[:3]);painted.append(v.index)
        vc.append(col)
    support={v.index for v in mesh.vertices if region(v.co) and tuple(v.co) not in frozen_rim}
    for _ in range(2):
        updated=list(vc)
        for i in support:
            if neighbors[i]:updated[i]=vc[i].lerp(sum((vc[j] for j in neighbors[i]),Vector())/len(neighbors[i]),.38)
        vc=updated
    attr=mesh.color_attributes.new(name='R6 welded pelvis palette',type='FLOAT_COLOR',domain='CORNER')
    mat=bpy.data.materials.new('S | R6 welded pelvis transition');mat.use_nodes=True
    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Metallic'].default_value=.13;bs.inputs['Roughness'].default_value=.40
    node=mat.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name=attr.name
    mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    mesh.materials.append(mat);slot=len(mesh.materials)-1;paint_faces=0
    for p in mesh.polygons:
        if not all(region(mesh.vertices[i].co) for i in p.vertices):continue
        for li in p.loop_indices:attr.data[li].color=(*vc[mesh.loops[li].vertex_index],1)
        p.material_index=slot;paint_faces+=1
    palette_report={'source':'same R5 pearl / ivory / slate / graphite palette',
        'projected_vertices':len(painted),'local_faces':paint_faces,
        'method':'pelvic source face ray projection onto genuinely joined mesh; two-ring color interpolation'}
after={o.name:signature(o) for o in model.objects if o.type=='MESH'}
untouched=sorted(set(before)-set(targets)-{body.name})
assert all(before[n]==after[n] for n in untouched)
remaining={tuple(v.co) for v in body.data.vertices}
outside=[p for p in old_body if not region(p)]
missing=[p for p in outside if p not in remaining]
assert not missing, ('Changed protected body coordinates', missing[:20])
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)
body['r6_edit']='Existing pelvis/sacrum unified with original continuous core; bounded hip fairing and local edge subdivision.'
sc=bpy.context.scene;sc['stage']='R6_TRIAL_'+TRIAL
sc['candidate_status']='REVISE; real pelvis geometry trial awaiting render and deformation review'
sc.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
report={'source':'S_ZERO_CANDIDATE_REVISED_R5.blend','output':str(OUT.relative_to(ROOT)),
    'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(), 'changes':changes,
    'core_sculpt_vertices':len(core_changes),'new_seam_vertices':len(seams),
    'subdivided_edges':subdivided,'triangulated_local_ngons':len(ngons),
    'opposing_coincident_local_faces_removed':len(double_faces),
    'palette':palette_report,
    'faired_vertices':fairing_count,'protected_body_vertices_exact':len(outside),
    'protected_meshes':untouched,'before_signatures':before,'after_signatures':after,
    'health':health,'topology_changed':True,'rigged':False,
    'limitation':'Welded continuity is verified separately; neither boolean union nor closed topology proves usable deformation.'}
REPORT.write_text(json.dumps(report,indent=2)+'\n')
print('R6 trial saved', str(OUT), {k:v for k,v in report.items() if k in ['core_sculpt_vertices','new_seam_vertices','subdivided_edges','faired_vertices','protected_body_vertices_exact','health']})
