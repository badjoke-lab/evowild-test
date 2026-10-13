"""V8 static edit of the real v7 Blender cage: anatomical planes and overlaps.

No v1-v7 output is written. No rig or animation is created. The source's coarse
shared mesh is edited directly: paired chest planes, a returning inferior edge,
inset shoulder lips, and an upper-arm face facing away from the shoulder cap.
"""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'art/p-creature/workspaces/P-v7-reference-retopology.blend'
OUT=ROOT/'art/p-creature/workspaces/P-v8-layered-anatomy.blend'
GLB=ROOT/'public/models/evowild-p/p-canonical-v8.glb'
E=ROOT/'docs/evidence/p-canonical-3d-v8-20261013'
W=ROOT/'work/p-canonical-v8';E.mkdir(parents=True,exist_ok=True);W.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='bddd334bd35976dc51a5d07aa5d45e6076ba150de5681c0aa0b2449d3a5be887'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
ref=bpy.data.objects['CANONICAL_P_IMAGE__DO_NOT_MODIFY'].data
reference_hash=hashlib.sha256(bytes(ref.packed_file.data)).hexdigest()
assert reference_hash==hashlib.sha256((ROOT/'public/concept/P.webp').read_bytes()).hexdigest()
body=bpy.data.objects['AUTHORING_hidden_shared_edge_cage']
body.name='P_v8_SHARED_ANATOMICAL_EDIT_CAGE';body.hide_set(False);body.hide_render=False;body.modifiers.clear()
bpy.data.objects.remove(bpy.data.objects['P_v7_CONTINUOUS_REFERENCE_SCULPT'],do_unlink=True)
head=bpy.data.objects['P_v7_edited_v6_head_cue_digits'];head.name='P_v8_preserved_head_cue_digits'
tail=bpy.data.objects['P_v7_edited_folded_tail'];tail.name='P_v8_short_heavy_folded_tail'

def material(name,rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.73
    return m
palette=[material('P v8 oxblood muscle surface',(.19,.026,.024)),
         material('P v8 shaded muscle side',(.125,.017,.021)),
         material('P v8 slate pectoral and upper arm',(.08,.103,.139)),
         material('P v8 connective fold',(.027,.036,.05)),
         material('P v8 shoulder crown plane',(.235,.039,.031))]
source_materials=[p.material_index for p in body.data.polygons]
body.data.materials.clear()
for m in palette:body.data.materials.append(m)
for p,mi in zip(body.data.polygons,source_materials):p.material_index=mi

# These are actual source face IDs, reviewed in v7's 858-vertex editable cage.
# They identify connected anatomical patches, not isolated objects or primitives.
# The mirrored half has the same face order with an offset of 428.
bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table();bm.verts.ensure_lookup_table()
assert len(bm.faces)==856 and len(bm.verts)==858
layer=bm.faces.layers.int.new('v8_anatomical_region');original=list(bm.faces)
for f in bm.faces:f[layer]=0
regions={
 'pectoral': [9,10,13,14],
 'clavicular': [8,11,12,15,116,117,118,119,120,121,122,123],
 'shoulder': list(range(92,100))+list(range(124,132)),
 'upper_arm': list(range(156,164))+[152,153,154,155,184,185,186,187],
 'triceps': list(range(132,140)),
}
edits=[]

def region_faces(name,side):return [original[i+(428 if side>0 else 0)] for i in regions[name]]
def verts_of(faces):return set(v for f in faces for v in f.verts)

# Move the shoulder girdle's crown above the breast and away from the sagittal
# plane. The paired clavicles stay below it; this changes the major silhouette.
for side in [-1,1]:
    shoulder=region_faces('shoulder',side)
    for v in verts_of(shoulder):
        x,y,z=v.co
        upper=max(0,min(1,(z-2.02)/.65))
        outer=max(0,min(1,(abs(y)-.32)/.56))
        v.co.y+=side*.13*outer
        v.co.z+=.18*upper
    for f in region_faces('upper_arm',side):f.material_index=2
    for f in region_faces('triceps',side):f.material_index=1
    for f in region_faces('clavicular',side):f.material_index=2
    for i in range(4,8):original[i+(428 if side>0 else 0)].material_index=2

# The deltoid must taper over the arm, not finish as a horizontal armor plate.
# Lift its anterior/posterior corners while leaving the central insertion low.
# Match the mirrored landmark by coordinates so both halves share the edit.
for index,delta in {47:(-.025,0,.18),49:(-.025,0,.24),233:(-.0125,0,.09),237:(-.0125,0,.12)}.items():
    anchor=bm.verts[index].co.copy()
    targets=[v for v in bm.verts if abs(v.co.x-anchor.x)<1e-5 and abs(abs(v.co.y)-abs(anchor.y))<1e-5 and abs(v.co.z-anchor.z)<1e-5]
    for v in targets:v.co+=Vector(delta)

# Recess the sternum between the two breasts, leaving the neck and abdomen intact.
# This is a change of the front surface's direction, not a painted vertical line.
for v in bm.verts:
    x,y,z=v.co
    if x<-1.0 and abs(y)<.13 and 1.74<z<2.33:
        v.co.x+=.10*(1-abs(y)/.13)
bm.normal_update()

def inset_plane(name,side,thickness,depth,normal=None,anchor=None):
    fs=region_faces(name,side)
    before={v:v.co.copy() for v in verts_of(fs)}
    result=bmesh.ops.inset_region(bm,faces=fs,thickness=thickness,depth=depth,use_even_offset=True,use_boundary=True,use_interpolate=True)
    rim=result['faces']
    interior=verts_of(fs)
    if normal is not None:
        n=Vector(normal).normalized();a=Vector(anchor)
        # Paired breast faces look forwards/outwards/downwards; the inset border
        # supplies the separate lower return surface, with continuous topology.
        for v in interior:v.co-=n*((v.co-a).dot(n))*.35
    for f in fs:f[layer]=1 if name=='pectoral' else 2
    for f in rim:
        f.material_index=(1 if f.calc_center_median().z<2.22 else 0) if name=='shoulder' else 2
        f[layer]=3
    if name=='pectoral':
        for f in fs:f.material_index=2
    else:
        # A lower shoulder lip overhangs the proximal upper arm. Its underside
        # and the upper-arm face point in different directions in FRONT34.
        for v in interior:
            if v.co.z<2.29:v.co.z-=.025
        for f in fs:f.material_index=0 if f.calc_center_median().z<2.68 else 4
    edits.append({'patch':name,'side':side,'originalFaces':len(fs),'newTransitionFaces':len(rim),'planeNormal':normal,'sharedTopology':True})
    return fs,rim

all_rims=[]
for side in [-1,1]:
    fs,rim=inset_plane('pectoral',side,.075,.055,(-.90,side*.33,-.15),(-1.29,side*.27,2.13));all_rims+=rim
    fs,rim=inset_plane('shoulder',side,.09,.045);all_rims+=rim

# Give the proximal upper arm its own broad plane beneath the shoulder lip.
# The triceps remains posterior; the frontal arm rotates away from the chest.
for side in [-1,1]:
    fs=region_faces('upper_arm',side)
    n=Vector((-.38,side*.90,.12)).normalized();a=Vector((-.43,side*.93,1.70))
    vs=verts_of(fs)
    for v in vs:
        if 1.42<v.co.z<1.94:
            v.co-=n*((v.co-a).dot(n))*.40
    for f in fs:f[layer]=4

# One returning edge under each breast. The broad dark transition is geometry,
# not an engraved scar or a detached breast-shaped shell.
crease=bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
for e in bm.edges:e[crease]=0
for f in all_rims:
    for e in f.edges:e[crease]=.10 if f.calc_center_median().z<2.1 else 0
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
assert all(e.is_manifold for e in bm.edges),'Non-manifold anatomical edit'
bm.to_mesh(body.data);bm.free();body.data.update()
for p in body.data.polygons:p.use_smooth=True

# Use smooth material boundaries carried by the actual subdivision topology.
# Remove the old vertex-paint attributes, so no v7 scar or jagged paint survives.
for a in list(body.data.color_attributes):body.data.color_attributes.remove(a)
body['anatomy']='paired pectoral planes / returning breast edge / shoulder lip / proximal arm'
body['source']='Direct edit of v7 coarse shared mesh, no primitive reconstruction'
sub=body.modifiers.new('Anatomical edge-flow subdivision','SUBSURF');sub.levels=2;sub.render_levels=2

# Directly reshape the existing folded tail cage. A broad root and midsection
# survive subdivision; the short terminal hook remains part of the same cage.
tail.modifiers.clear()
tail_before=[list(v.co) for v in tail.data.vertices]
tail_control=[(.67,0,1.80),(.92,-.31,1.82),(.92,.31,1.82),
 (1.22,-.37,1.70),(1.22,.37,1.70),(1.37,-.35,1.67),(1.37,.35,1.67),
 (1.48,-.31,1.78),(1.48,.31,1.78),(1.62,-.27,1.78),(1.62,.27,1.78),
 (1.77,-.16,1.60),(1.77,.16,1.60),(1.86,0,1.28),
 (.94,0,1.37),(1.35,0,1.29),(1.59,0,1.42)]
assert len(tail.data.vertices)==len(tail_control)
for v,p in zip(tail.data.vertices,tail_control):v.co=p
tail.data.materials.clear()
for m in palette:tail.data.materials.append(m)
for p in tail.data.polygons:p.material_index=0 if p.index<7 else (1 if p.index<13 else 3);p.use_smooth=True
sub=tail.modifiers.new('Heavy folded tail surface','SUBSURF');sub.levels=2;sub.render_levels=2

# Retain an editable cage in the .blend, while exporting the evaluated surface.
cage=body.copy();cage.data=body.data.copy();scene.collection.objects.link(cage)
cage.name='AUTHORING_v8_layered_anatomy_cage';cage.hide_render=True;cage.hide_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.object.modifier_apply(modifier=body.modifiers[0].name)
body.name='P_v8_CONTINUOUS_LAYERED_ANATOMY'

def inspect(o):
    bm=bmesh.new();bm.from_mesh(o.data);left=set(bm.verts);parts=[]
    while left:
        todo=[left.pop()];n=0
        while todo:
            v=todo.pop();n+=1
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in left:left.remove(w);todo.append(w)
        parts.append(n)
    d={'vertices':len(bm.verts),'faces':len(bm.faces),'components':parts,'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)}
    bm.free();assert len(parts)==1 and d['nonManifoldEdges']==0,d
    return d
checks={'body':inspect(body),'tailCage':inspect(tail),'source':SOURCE.relative_to(ROOT).as_posix(),'referenceSHA256':reference_hash,'edits':edits,'tailControlBefore':tail_before,'tailControlAfter':tail_control,'staticOnly':True}
scene.name='Canonical P v8 / layered anatomy / STATIC REVIEW'
scene['model_source']='public/models/evowild-p/p-canonical-v8.glb'
scene['static_gate']='REVIEW_PENDING; no rig or motion permitted in this iteration'
scene['canonical_reference_sha256']=reference_hash
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
bpy.ops.object.select_all(action='DESELECT')
for o in (body,head,tail):o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
checks['blendSHA256']=hashlib.sha256(OUT.read_bytes()).hexdigest();checks['glbSHA256']=hashlib.sha256(GLB.read_bytes()).hexdigest()
(E/'source-validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print('V8_SHARED_ANATOMY',json.dumps(checks))
if '--preview' in sys.argv:
    scene.render.resolution_percentage=65;scene.cycles.samples=20
    for view in ['FRONT34','FRONT']:
        scene.camera=bpy.data.objects['CAM_'+view];scene.render.filepath=str(W/f'preview-{view}.png');bpy.ops.render.render(write_still=True)
