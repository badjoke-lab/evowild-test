"""S crest reconstruction R2. An actual editable Blender mesh, NOT an image concept.
Input: authority-generated TRELLIS S v1 GLB (kept untouched).
Only cranial high blade geometry is replaced in this experiment.
Run in Blender 4.3.2: blender -b -t 4 --python ... .
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi

ROOT=Path(bpy.path.abspath("//")).resolve()
BASE=ROOT/"art/s-creature/experiments/authority-rebuild-20261009"
SRC=BASE/"S-authority-trellis-v1.glb"
OUT=BASE/"r2-crest"
REVIEW=OUT/"review"
OUT.mkdir(parents=True,exist_ok=True)
REVIEW.mkdir(exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SRC))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
if len(meshes)!=1:
    raise RuntimeError("Expected exactly one GLB mesh, got "+str(len(meshes)))
body=meshes[0]
body.name="S_authority_3d_body_donor_crest_removed"
W=body.matrix_world.copy()

# Work in the local mesh data, assess in immutable world coordinates.
# Remove only the elevated narrow spear: do not touch limbs, chest, pelvis or tail.
bm=bmesh.new()
bm.from_mesh(body.data)
pre_faces=len(bm.faces)
cut=[]
for f in bm.faces:
    q=sum((W @ v.co for v in f.verts),Vector())/len(f.verts)
    # The generated single horn occupies the center above the original head.
    # z above 0.145 is further gated by the forward head/neck region.
    if (-0.425 <= q.y <= -0.015 and q.z > 0.145 and abs(q.x)<0.048):
        cut.append(f)
if not (50<len(cut)<90000):
    raise RuntimeError("unsafe crest-removal selection count="+str(len(cut)))
bmesh.ops.delete(bm,geom=cut,context="FACES")
bm.to_mesh(body.data)
bm.free()
body.data.update()
print("CUT old crest faces",len(cut),"from",pre_faces)

# Part coordinates are in the same Blender world space as the imported glTF.
# Long axis: +Y toward tail; -Y toward nose. Z up; x is lateral.
# Two main blades, independent frontal silhouettes, rooted INSIDE the skull.
def blade(name, stations, widths, thicknesses, color=None):
    n=10
    verts=[]
    faces=[]
    for i,(x,y,z) in enumerate(stations):
        t=i/(len(stations)-1)
        # Elliptic cross-sections create a convex laminar blade, not a flat plane.
        for j in range(n):
            ang=2*pi*j/n
            xx=x+widths[i]*cos(ang)
            yy=y+thicknesses[i]*sin(ang)
            verts.append((xx,yy,z))
    faces.append(tuple(range(n-1,-1,-1)))
    for i in range(len(stations)-1):
        for j in range(n):
            a=i*n+j
            b=i*n+(j+1)%n
            c=(i+1)*n+(j+1)%n
            d=(i+1)*n+j
            faces.append((a,b,c,d))
    base=(len(stations)-1)*n
    faces.append(tuple(base+j for j in range(n)))
    me=bpy.data.meshes.new(name+"_mesh")
    me.from_pydata(verts,[],faces)
    me.update()
    ob=bpy.data.objects.new(name,me)
    bpy.context.collection.objects.link(ob)
    # Consistent normals with Blender recalculation.
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(me);bm.free()
    for p in me.polygons:p.use_smooth=True
    mod=ob.modifiers.new("edge_transition_smoothing","WEIGHTED_NORMAL")
    return ob

# Anchor x offset establishes visible separation already at the forehead.
# Curve sweeps BACK (+Y) as Z rises. The two broad blades stay laterally separated.
made=[]
for side in (-1,1):
    def X(a):return side*a
    stations=[
        (X(.019),-.344,.115),
        (X(.024),-.307,.163),
        (X(.032),-.266,.227),
        (X(.041),-.210,.304),
        (X(.049),-.144,.370),
        (X(.058),-.074,.439),
        (X(.061),-.045,.458),
    ]
    widths=[.014,.014,.0125,.011,.009,.005,.0007]
    thickness=[.014,.014,.012,.0095,.007,.004,.0005]
    made.append(blade("CREST_MAIN_"+("L" if side<0 else "R"),stations,widths,thickness))
    # Supplemental short, swept lamina beneath the main blade.
    support=[
        (X(.020),-.323,.117),
        (X(.035),-.275,.155),
        (X(.050),-.214,.196),
        (X(.057),-.155,.221),
        (X(.062),-.112,.230)
    ]
    made.append(blade("CREST_SECONDARY_"+("L" if side<0 else "R"),support,
                      [.010,.011,.010,.006,.0006],[.010,.009,.007,.004,.0004]))

# The rooted blades must be genuine scene geometries, not image overlays.
crest_objects=[body]+made
for obj in crest_objects:
    obj.select_set(False)

# Preserve a Blender-native, editable master, then export tested GLB.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-authority-crest-r2.blend"))
bpy.ops.object.select_all(action="DESELECT")
for ob in crest_objects:ob.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(OUT/"S-authority-crest-r2.glb"),
                          export_format="GLB",use_selection=True,
                          export_apply=True,export_yup=True)
bpy.ops.object.select_all(action="DESELECT")

# Workbench uses real 3D mesh; lighting/neutral colors are not final materials.
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(.70,.72,.74)
scene.display.shading.show_shadows=True
scene.render.resolution_x=720
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.world.color=(.045,.055,.07)
scene.render.film_transparent=False

# Ortho views align identically across candidate reviews.
pts=[o.matrix_world@v.co for o in crest_objects for v in o.data.vertices]
lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
center=(lo+hi)*.5
extent=hi-lo
camdata=bpy.data.cameras.new("Orthographic_Review")
cam=bpy.data.objects.new("Orthographic_Review",camdata)
scene.collection.objects.link(cam)
scene.camera=cam
camdata.type="ORTHO"
views={
    "side":Vector((1,0,0)),
    "front":Vector((0,-1,0)),
    "front34":Vector((1,-1,0)).normalized(),
    "rear34":Vector((1,1,0)).normalized(),
    "back":Vector((0,1,0))
}
for name,direction in views.items():
    cam.location=center+direction*3.0
    cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()
    right=Vector((-direction.y,direction.x,0))
    right.normalize()
    horiz=max(p.dot(right) for p in pts)-min(p.dot(right) for p in pts)
    camdata.ortho_scale=max(horiz,extent.z)*1.20
    scene.render.filepath=str(REVIEW/("S_authority_crest_r2_"+name+".png"))
    bpy.ops.render.render(write_still=True)

result={
    "input":str(SRC.relative_to(ROOT)),
    "model":str((OUT/"S-authority-crest-r2.glb").relative_to(ROOT)),
    "blend":str((OUT/"S-authority-crest-r2.blend").relative_to(ROOT)),
    "pre_body_faces":pre_faces,
    "removed_old_spear_faces":len(cut),
    "crest_objects":[o.name for o in made],
    "crest_geometry":"two independently modeled main swept blade volumes and two secondary volumes",
    "outside_crest_edit_scope":"no body vertices modified, only face removal in fixed head-top ROI",
    "source_topology_bad":True,
    "body_geometry_unapproved":True,
    "crest_morphology_unapproved":True,
    "game_ready":False,
    "views":list(views.keys())
}
(OUT/"R2_CRESTRIG_EVIDENCE.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
