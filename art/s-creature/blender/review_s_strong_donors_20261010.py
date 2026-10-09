"""EvoWild S: donor bake-off (review ONLY, no geometry re-authoring).

Two extant real 3D files: TRELLIS-derived R5 and TRELLIS2 QEM.
In each render both have identical orthographic camera, material, lighting,
and normalized vertical extent. Never silently substitute R0 simplified cage.
"""
from pathlib import Path
import bpy,bmesh,hashlib,json
from mathutils import Matrix,Vector

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE/"experiments"
OUT=ROOT/"strong-donor-evaluation-20261010"
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
SOURCE={
 "R5":{
  "path":ROOT/"authority-rebuild-20261009/r5-crest-lamina/S-authority-crest-lamina-r5.glb",
  "status":"UNAPPROVED visual shape donor; nonwatertight fragmented base",
  "generation":"TRELLIS-derived body plus rebuilt paired laminar crests",
 },
 "QEM":{
  "path":ROOT/"trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb",
  "status":"UNAPPROVED single watertight mesh; joint deformability untested",
  "generation":"TRELLIS2 image-to-3D candidate plus MeshFix/QEM reduction",
 }
}
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for cl in list(bpy.data.collections):
    if cl.name!="Collection" and cl.users==0:bpy.data.collections.remove(cl)

scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(.70,.74,.78)
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.render.resolution_x=860
scene.render.resolution_y=860
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.world.color=(.045,.054,.065)

facts={}
objects={}
extents={}
normalized_bbox={}
for key,source in SOURCE.items():
    path=source["path"]
    if not path.is_file() or path.stat().st_size<100000:
        raise FileNotFoundError(str(path))
    source_sha=hashlib.sha256(path.read_bytes()).hexdigest()
    previously=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    added=set(bpy.data.objects)-previously
    meshes=[o for o in added if o.type=="MESH"]
    if not meshes:raise ValueError(key+" no actual mesh")
    newcol=bpy.data.collections.new("DONOR_"+key+"_UNAPPROVED")
    scene.collection.children.link(newcol)
    for o in meshes:
        # Preserve source mesh topology. Move collection reference only.
        for c in list(o.users_collection):c.objects.unlink(o)
        newcol.objects.link(o)
    # Detach imported glTF mesh nodes from their parent empties while
    # retaining exact world-space geometry. Parent-space object transforms
    # otherwise suppress or double-apply explicit normalization rotations.
    for o in meshes:
        world=o.matrix_world.copy()
        o.parent=None
        o.matrix_world=world
    bpy.context.view_layer.update()
    verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lo=Vector([min(p[i] for p in verts) for i in range(3)])
    hi=Vector([max(p[i] for p in verts) for i in range(3)])
    span=hi-lo
    if min(span)<=0 or span.z<.05 or span.y<.05:
        raise ValueError(f"unexpected donor dimensions: {key} {list(span)}")
    axis_correction="NONE"
    # QEM GLB is authored with a different glTF up-axis transform: importer
    # reports Y=0.647 body height and Z=0.359 body length. The original
    # source audit is Z-up. Rotate only in review scene to reconcile axes.
    if key=="QEM" and span.y>span.z*1.3:
        correction=Matrix.Rotation(3.141592653589793/2,4,"X")
        for o in meshes:
            o.matrix_world=correction@o.matrix_world
        bpy.context.view_layer.update()
        verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
        lo=Vector([min(p[i] for p in verts) for i in range(3)])
        hi=Vector([max(p[i] for p in verts) for i in range(3)])
        span=hi-lo
        axis_correction="QEM +90deg X, applied to review scene transforms only"
        if span.z<span.y:
            raise RuntimeError("QEM correction still not upright "+str(list(span)))
    # Only review-space transform; never touch the source GLB geometry.
    s=2.55/span.z
    transform=Matrix.Translation(Vector((-(lo.x+hi.x)*s/2,-(lo.y+hi.y)*s/2,-lo.z*s)))@Matrix.Scale(s,4)
    for o in meshes:
        o.matrix_world=transform@o.matrix_world
    bpy.context.view_layer.update()
    # Actual geometric world-space dimensions now, not inferred camera bounds.
    pp=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    lower=Vector([min(p[i] for p in pp) for i in range(3)])
    upper=Vector([max(p[i] for p in pp) for i in range(3)])
    normspan=upper-lower
    if not (2.549<=normspan.z<=2.551):
        raise RuntimeError(f"{key} failed to normalize correctly: {normspan}")
    stats=[]
    for o in meshes:
        bm=bmesh.new();bm.from_mesh(o.data)
        boundary=sum(len(e.link_faces)==1 for e in bm.edges)
        nonmanifold=sum(len(e.link_faces)!=2 for e in bm.edges)
        stats.append({
          "name":o.name,"vertices":len(o.data.vertices),
          "polygons":len(o.data.polygons),
          "boundary_edges":boundary,
          "nonmanifold_edges":nonmanifold
        })
        bm.free()
    objects[key]=meshes
    extents[key]=normspan
    normalized_bbox[key]={"min":list(lower),"max":list(upper)}
    facts[key]={
      "file":str(path.relative_to(BASE)),
      "file_sha256":source_sha,
      "bytes":path.stat().st_size,
      "mesh_object_count":len(meshes),
      "total_vertices":sum(z["vertices"] for z in stats),
      "total_faces":sum(z["polygons"] for z in stats),
      "mesh_stats":stats[:20],
      "total_boundary_edges":sum(z["boundary_edges"] for z in stats),
      "total_nonmanifold_edges":sum(z["nonmanifold_edges"] for z in stats),
      "original_world_extent":list(span),
      "normalization_uniform_scale":s,
      "axis_correction":axis_correction,
      "normalized_bbox":normalized_bbox[key],
      "status":source["status"],"provenance":source["generation"],
    }

max_horiz=max(max(v.x,v.y) for v in extents.values())
camera_scale=max(3.20,max_horiz*1.13)
if camera_scale>9.5:raise RuntimeError(f"camera would make figure unreadable, check axes: {camera_scale}")
camera_data=bpy.data.cameras.new("S_SAME_CAMERA_AND_SCALE")
camera=bpy.data.objects.new("S_SAME_CAMERA_AND_SCALE",camera_data)
scene.collection.objects.link(camera)
camera_data.type="ORTHO"
camera_data.ortho_scale=camera_scale
scene.camera=camera
look=Vector((0,0,1.275))
directions={
 "side":Vector((1,0,0)),"front":Vector((0,-1,0)),
 "front34":Vector((1,-1,0)).normalized(),
 "rear34":Vector((1,1,0)).normalized(),
 "back":Vector((0,1,0))
}
for key in ("R5","QEM"):
    for other in objects:
        for o in objects[other]:o.hide_render=(other!=key)
    for tag,d in directions.items():
        camera.location=look+d*8
        camera.rotation_euler=((look-camera.location).to_track_quat("-Z","Y")).to_euler()
        scene.render.filepath=str(REVIEW/f"S_{key}_equal_camera_{tag}.png")
        bpy.ops.render.render(write_still=True)
# Archive an editable review scene with original mesh data unmodified, keeping
# donors separated side-by-side (not fused). This is not a repaired rig.
for key in objects:
    for o in objects[key]:
        o.hide_render=False
        o.matrix_world=Matrix.Translation(Vector((-2.0 if key=="R5" else 2.0,0,0)))@o.matrix_world
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-strong-donor-side-by-side-review.blend"),compress=True)
result={
 "authority":"art/s-creature/references/00_s_type_modeling_image_v1.png",
 "authority_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "evaluation":"actual 3D equal camera + equal vertical scale, full-body and provenance gate",
 "common_ortho_scale":camera_scale,
 "camera_directions":list(directions),
 "height_normalization":2.55,
 "candidates":facts,
 "notes":[
   "All mesh vertices/polygons are original from real GLBs; scene review transforms only.",
   "Equal z-height does not solve different poses or camera orientation uncertainty.",
   "Mesh closure does not establish creature design likeness, deformability or rig readiness.",
   "Source PNG authority must be compared before design acceptance.",
 ],
 "selected_for_production":None,
 "selected_for_anatomy_test":None,
 "production_ready":False,
 "animation_ready":False
}
(OUT/"DONOR_AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
print("DONOR_SIDE_BY_SIDE_RENDER_VERIFIED",json.dumps({
  k:{"vertices":v["total_vertices"],"faces":v["total_faces"],
     "objects":v["mesh_object_count"],"nonmanifold":v["total_nonmanifold_edges"]}
  for k,v in facts.items()},indent=2))
