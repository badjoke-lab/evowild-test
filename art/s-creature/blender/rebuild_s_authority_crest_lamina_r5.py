"""EvoWild S R5 laminar crest-only rebuild with R4 bulbous-neck regression reverted.

This is a *real mesh construction* experiment, with neutral five-view Blender
renders. Not a final production topology or approved creature.
Source-of-truth S-type modeling image remains locked outside this file.
"""
import bpy, bmesh, math, json
from mathutils import Vector
from pathlib import Path

ROOT=Path(bpy.path.abspath("//")).resolve()
BASE=ROOT/"art/s-creature/experiments/authority-rebuild-20261009"
SRC=BASE/"S-authority-trellis-v1.glb"
OUT=BASE/"r5-crest-lamina"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SRC))
found=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(found)==1, f"expected one source model, got {len(found)}"
donor=found[0]
donor.name="DONOR_body_nonproduction"
matrix=donor.matrix_world.copy()

# Target only the generated upper single spear. Leave the existing head,
# neck, thorax and all body vertices untouched. R4's loft was a REJECT.
bm=bmesh.new()
bm.from_mesh(donor.data)
body_before=len(bm.faces)
cut=[]
for f in bm.faces:
    q=sum((matrix@v.co for v in f.verts),Vector())/len(f.verts)
    if -.425<=q.y<=-.015 and q.z>.132 and abs(q.x)<.048:
        cut.append(f)
if not (1000<len(cut)<90000):
    raise RuntimeError("Unsafe old-crest removal count "+str(len(cut)))
bmesh.ops.delete(bm,geom=cut,context="FACES")
bm.to_mesh(donor.data)
bm.free()
donor.data.update()
newparts=[]

def blade(name,path,halfwidths,thicks):
    """Broad *side-profile* laminar blade, thickness in lateral X.
    Unlike R3's x/y ellipsoid rods, the leaf's broad face is in Y/Z.
    """
    assert len(path)==len(halfwidths)==len(thicks)
    vs=[]
    n=len(path)
    for i,(x,y,z) in enumerate(path):
        a=Vector(path[max(0,i-1)][1:])
        b=Vector(path[min(n-1,i+1)][1:])
        tang=(b-a).normalized()
        norm=Vector((-tang.y,tang.x))
        w=halfwidths[i];t=thicks[i]
        for sy,sz in ((-1,-1),(1,-1),(1,1),(-1,1)):
            vs.append((x+sz*t,y+sy*norm.x*w,z+sy*norm.y*w))
    fs=[(3,2,1,0)]
    for i in range(n-1):
        for k in range(4):
            fs.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    base=4*(n-1);fs.append(tuple(base+j for j in range(4)))
    mesh=bpy.data.meshes.new(name+"_bladed_sheet")
    mesh.from_pydata(vs,[],fs);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(mesh);bm.free()
    for p in mesh.polygons:p.use_smooth=True
    newparts.append(ob)
    return ob

# Anchor blades well inside the continuous skull loft. A split is already
# visible at the root when viewed from front/back, never a sagittal horn.
for s in (-1,1):
    main=[
      (s*.022,-.359,.101),
      (s*.029,-.329,.148),
      (s*.036,-.291,.197),
      (s*.042,-.239,.265),
      (s*.051,-.176,.323),
      (s*.061,-.093,.386),
      (s*.070,-.009,.442),
      (s*.072,.027,.454)
    ]
    blade("PRIMARY_LAMINA_"+("L" if s<0 else "R"),main,
          [.012,.027,.042,.047,.043,.030,.012,.0004],
          [.007,.009,.010,.009,.008,.005,.003,.0005])
    # Root gussets widen into the occipital skull, paired rather than needles.
    blade("ROOT_SUPPORT_"+("L" if s<0 else "R"),[
       (s*.014,-.375,.092),(s*.034,-.329,.135),
       (s*.045,-.281,.181),(s*.050,-.253,.201)],
       [.014,.021,.012,.0007],[.009,.008,.005,.0006])
    # Smaller secondary swept sheets, underneath the dominating profile.
    blade("SECONDARY_LAMINA_"+("L" if s<0 else "R"),[
       (s*.029,-.345,.114),(s*.037,-.292,.144),
       (s*.049,-.244,.175),(s*.055,-.200,.199),
       (s*.061,-.160,.209)],
       [.010,.017,.015,.010,.0004],[.006,.006,.005,.004,.0004])

# Slim two-sided anatomical face plates, not antlers or eye-stalks.
for side in (-1,1):
    blade("TEMPORAL_SCULPT_"+("L" if side<0 else "R"),[
       (side*.023,-.438,.097),(side*.032,-.404,.116),
       (side*.037,-.369,.125),(side*.036,-.346,.107)],
       [.003,.012,.014,.0004],[.003,.004,.005,.0004])

parts=[donor]+newparts

# Source-derived animal body remains low quality and non-watertight; the R4
# torso is not declared a valid deformation mesh.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-crest-lamina-r5.blend"))
bpy.ops.object.select_all(action="DESELECT")
for obj in parts:obj.select_set(True)
bpy.context.view_layer.objects.active=donor
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-authority-crest-lamina-r5.glb"),
                          export_format="GLB",use_selection=True,export_apply=True,export_yup=True)
bpy.ops.object.select_all(action="DESELECT")

scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(.69,.71,.74)
scene.display.shading.show_shadows=True
scene.render.resolution_x=800;scene.render.resolution_y=800
scene.render.resolution_percentage=100
scene.render.film_transparent=False
scene.render.image_settings.file_format="PNG"
scene.world.color=(.045,.055,.07)

pts=[o.matrix_world@v.co for o in parts for v in o.data.vertices]
lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
ctr=(lo+hi)/2
ext=hi-lo
camera_data=bpy.data.cameras.new("ORTHO_R4")
camera=bpy.data.objects.new("ORTHO_R4",camera_data)
scene.collection.objects.link(camera)
scene.camera=camera
camera_data.type="ORTHO"
views={"side":Vector((1,0,0)),"front":Vector((0,-1,0)),
       "front34":Vector((1,-1,0)).normalized(),"rear34":Vector((1,1,0)).normalized(),
       "back":Vector((0,1,0))}
for name,d in views.items():
    camera.location=ctr+d*3
    camera.rotation_euler=((ctr-camera.location).to_track_quat("-Z","Y")).to_euler()
    horiz=Vector((-d.y,d.x,0)).normalized()
    project=[p.dot(horiz) for p in pts]
    camera_data.ortho_scale=max(max(project)-min(project),ext.z)*1.18
    scene.render.filepath=str(REV/("S_crest_lamina_r5_"+name+".png"))
    bpy.ops.render.render(write_still=True)

result={
 "input":str(SRC.relative_to(ROOT)),
 "s_type_reference_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "model":str((OUT/"S-authority-crest-lamina-r5.glb").relative_to(ROOT)),
 "blend":str((OUT/"S-authority-crest-lamina-r5.blend").relative_to(ROOT)),
 "donor_body_faces_before":body_before,
 "removed_generated_spear_faces":len(cut),
 "added_new_crest_and_temporal_parts":len(newparts),
 "part_names":[o.name for o in newparts],
 "applied_to_existing_reference_glb_only":True,
 "R4_neck_replacement_reverted":True,
 "original_head_and_neck_unchanged_except_spear_cut":True,
 "donor_body_is_non_watertight_and_not_animation_approved":True,
 "production_morphology_approved":False,
 "game_ready":False,
 "render_views":list(views.keys())
}
(OUT/"R5_EVIDENCE.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
