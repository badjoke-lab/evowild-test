"""3D P independent rescue sculpt from intact v7 .blend, NEVER recovered Codex v8.
Blender 4.3.2 background: blender -b -t 4 --python scripts/modeling/build-p-v7b-rescue.py
Art-direct only selected chest/scapular planes and a genuine tail-root static boolean weld.
The candidate is a *static* review model, not a claim to the missing original v8.
"""
import bpy, bmesh, math, hashlib, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'art/p-creature/workspaces/P-v7-reference-retopology.blend'
AUTH=ROOT/'public/concept/P.webp'
OUT=ROOT/'art/p-creature/workspaces/P-v7b-rescue-static.blend'
GLB=ROOT/'public/models/evowild-p/p-canonical-v7b-rescue.glb'
E=ROOT/'docs/evidence/p-canonical-3d-v7b-rescue-20261014'
E.mkdir(parents=True,exist_ok=True)
assert all(p.exists() for p in (SRC,AUTH))
source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
ref=bpy.data.objects['CANONICAL_P_IMAGE__DO_NOT_MODIFY']
canonical=hashlib.sha256(AUTH.read_bytes()).hexdigest()
assert ref.data.packed_file and hashlib.sha256(bytes(ref.data.packed_file.data)).hexdigest()==canonical
body=bpy.data.objects['P_v7_CONTINUOUS_REFERENCE_SCULPT']
tail=bpy.data.objects['P_v7_edited_folded_tail']
head=bpy.data.objects['P_v7_edited_v6_head_cue_digits']
assert not any(x.type=='ARMATURE' for x in scene.objects)
# The reference is a three-quarter painting. These are intentional *inferred*
# stereo-depth adjustments to a real existing connected anatomical surface.
def falloff(x,z,cx,cz,rx,rz):
    d=math.sqrt(((x-cx)/rx)**2+((z-cz)/rz)**2)
    t=max(0.0,1.0-d)
    return t*t*(3-2*t)
def side_weight(y):return max(0.,min(1.,(abs(y)-.20)/.37))
# Distinct scapular cap overlapping the oblique forelimb insertion, not a
# uniformly inflated tube. Chest volume pulled forward below deltoid.
sculpt_stats={'verticesTouched':0,'maxVertexOffset':0.}
original_coords=[v.co.copy() for v in body.data.vertices]
for v,old in zip(body.data.vertices,original_coords):
    x,y,z=old
    side=side_weight(y)
    if side<=0.:continue
    scapular=falloff(x,z,-.62,2.48,.53,.44)
    clavicular=falloff(x,z,-1.16,1.92,.43,.52)
    triceps=falloff(x,z,-.29,1.82,.30,.51)
    pectoral_keel=falloff(x,z,-.96,1.68,.39,.20)
    separation=falloff(x,z,-.52,2.10,.20,.11)
    # Broad planes with one recessed muscular insertion line.
    dy=side*(.145*scapular+.080*clavicular+.065*triceps+
             .044*pectoral_keel-.036*separation)
    dz=side*(.075*scapular-.035*clavicular-.025*pectoral_keel)
    dx=side*(-.040*clavicular+.025*triceps)
    if abs(dy)+abs(dz)+abs(dx)>.0002:
        v.co.x+=dx
        v.co.y+=(-1 if y<0 else 1)*dy
        v.co.z+=dz
        sculpt_stats['verticesTouched']+=1
        sculpt_stats['maxVertexOffset']=max(sculpt_stats['maxVertexOffset'],math.sqrt(dx*dx+dy*dy+dz*dz))
body.data.update()
# Color modulation highlights anatomical transition along same surface,
# without painting detachable red/grey capsules over the chest.
colors=body.data.color_attributes.get('P_v7_color')
if colors:
    for loop in body.data.loops:
        v=body.data.vertices[loop.vertex_index]
        x,y,z=v.co
        r,g,b,a=colors.data[loop.index].color
        shoulder=falloff(x,z,-.68,2.40,.52,.36)*side_weight(y)
        groove=falloff(x,z,-.52,2.10,.21,.11)*side_weight(y)
        colors.data[loop.index].color=(
            min(1,r*(1+.13*shoulder-.20*groove)),
            min(1,g*(1+.06*shoulder-.12*groove)),
            min(1,b*(1+.05*shoulder-.11*groove)),a)
# Thicken the actual tail ROOT cage; the tip itself is preserved.
# Changes taper to 0 at the distal tail, unlike adding disconnected bulbs.
tail_stats={'rootMoved':0,'booleanAttempted':False,'booleanJoined':False}
for v in tail.data.vertices:
    x,y,z=v.co
    root=max(0.,min(1.,(1.52-x)/.82))
    root=root*root*(3-2*root)
    if root>.0001:
        v.co.x-=.065*root
        v.co.y*=1+.48*root
        v.co.z+=.028*root
        tail_stats['rootMoved']+=1
tail.data.update()
# Apply tail subdivision before mesh union for consistent source coordinates.
bpy.context.view_layer.objects.active=tail
for mod in list(tail.modifiers):
    if mod.type=='SUBSURF':
        bpy.ops.object.modifier_apply(modifier=mod.name)
def inspect_mesh(obj):
    bm=bmesh.new();bm.from_mesh(obj.data)
    comps=0;unseen=set(bm.verts)
    while unseen:
        comps+=1;todo=[unseen.pop()]
        while todo:
            v=todo.pop()
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);todo.append(w)
    d={'vertices':len(bm.verts),'faces':len(bm.faces),
       'components':comps,'boundary':sum(e.is_boundary for e in bm.edges),
       'nonManifold':sum(not e.is_manifold for e in bm.edges)}
    bm.free()
    return d
preBody=inspect_mesh(body);preTail=inspect_mesh(tail)
assert preBody['components']==1 and preBody['nonManifold']==0 and preTail['nonManifold']==0
# Boolean-weld on a duplicate: if an exact union does not preserve manifold
# connectivity, DISCARD the attempt and keep the original two clean meshes.
copy=body.copy();copy.data=body.data.copy();scene.collection.objects.link(copy)
copy.name='P_v7b_STATIC_tail_union_candidate'
tail_stats['booleanAttempted']=True
try:
    bpy.context.view_layer.objects.active=copy
    modifier=copy.modifiers.new('Exact tail-root static join','BOOLEAN')
    modifier.operation='UNION';modifier.solver='EXACT';modifier.object=tail
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    result=inspect_mesh(copy)
    tail_stats['booleanResult']=result
    if result['components']==1 and result['nonManifold']==0 and result['boundary']==0:
        # The exact Boolean weld appends tail loops without the body's painted
        # vertex colors. Assign a deliberate tail palette on those new loops,
        # or Blender exports a bright unpainted (white) tail.
        painted=next((m for m in copy.data.materials if m.node_tree and
          any(n.type=='VERTEX_COLOR' for n in m.node_tree.nodes)),None)
        if painted is None:
            painted=body.data.materials[0]
        pigment=copy.data.color_attributes.get('P_v7_color')
        assert pigment is not None, 'Boolean unexpectedly erased vertex-color channel'
        loops_painted=0
        for polygon in copy.data.polygons:
            for li in polygon.loop_indices:
                v=copy.data.vertices[copy.data.loops[li].vertex_index]
                x,y,z=v.co
                if x>1.03 and 1.25<z<1.95 and abs(y)<.38:
                    # Dorsal crimson/lateral maroon/underside slate.
                    upper=max(0.,min(1.,(z-1.43)/.25))
                    rust=(.19,.038,.032)
                    slate=(.065,.086,.117)
                    color=tuple((1-upper)*slate[i]+upper*rust[i] for i in range(3))
                    pigment.data[li].color=(*color,1.0)
                    loops_painted+=1
            polygon.material_index=0
        copy.data.materials.clear()
        copy.data.materials.append(painted)
        tail_stats['tailColorLoopsPainted']=loops_painted
        assert loops_painted>80,('tail paint coverage missing',loops_painted)
        # Keep the v7 editable body in the source, export the welded mesh.
        copy['relation']='static boolean of real v7b torso and corrected root'
        tail_stats['booleanJoined']=True
        body.hide_render=True
        tail.hide_render=True
    else:
        bpy.data.objects.remove(copy,do_unlink=True)
        copy=None
except Exception as exc:
    tail_stats['booleanError']=str(exc)
    if copy and copy.name in bpy.data.objects:bpy.data.objects.remove(copy,do_unlink=True)
    copy=None
if not tail_stats['booleanJoined']:
    body.hide_render=False
    tail.hide_render=False
# Only review-model meshes, never the review floor.
selected=[head,copy] if tail_stats['booleanJoined'] else [head,body,tail]
for obj in bpy.data.objects:obj.select_set(False)
for obj in selected:obj.select_set(True);obj.hide_set(False)
bpy.context.view_layer.objects.active=selected[-1]
for obj in selected:obj.hide_render=False
bpy.ops.export_scene.gltf(
 filepath=str(GLB),export_format='GLB',use_selection=True,
 export_apply=True,export_animations=False,export_yup=True)
# On opening the source, expose the editable body and the static joined target.
body.hide_set(False)
if tail_stats['booleanJoined']:
    body.hide_render=True
    tail.hide_render=True
scene.camera=bpy.data.objects['CAM_FRONT34']
scene['review']='INDEPENDENT v7b RESCUE REVISE / original v8 NOT recovered'
scene['reference_sha256']=canonical
scene['source_v7_sha256']=source_hash
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
manifest={
 'candidate':'P v7b rescue, NOT the missing original v8',
 'production':'HOLD','shape':'REVIEW_PENDING',
 'canonicalSHA256':canonical,'originalV7BlendSHA256':source_hash,
 'newBlendSHA256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
 'newGLBSHA256':hashlib.sha256(GLB.read_bytes()).hexdigest(),
 'bytes':GLB.stat().st_size,'sculpt':sculpt_stats,'tail':tail_stats,
 'sourceManifold':preBody,'tailManifold':preTail,'rigged':False,'animations':0,
 'rootWelded':tail_stats['booleanJoined']
}
(E/'AUTHORING.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'public/models/evowild-p/manifest-v7b-rescue.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('P_3D_RESCUE_BUILD',json.dumps(manifest))
