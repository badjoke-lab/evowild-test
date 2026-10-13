"""Render unmodified S original Hunyuan in real Blender; no geometry edits.

Five original 3D views, plus camera crops over the real shoulder/chest.
Review against SHA-locked reference; REAR34 is continuity only.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path.cwd()
OUT = ROOT / "art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/baseline-five-view-20261014"
OUT.mkdir(parents=True, exist_ok=True)
SRC = ROOT / "art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/S_ORIGINAL_HUNYUAN_ART_SCULPT_STATION__UNEDITED_BASE.blend"
REF = ROOT / "art/s-creature/references/00_s_type_modeling_image_v1.png"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
protect = {str(p.relative_to(ROOT)): sha(p) for p in (SRC, REF)}
assert sha(REF) == "93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert sha(SRC) == "1f26bbd4485721a69d74c0c4c4da917dacf9341c15932785e42ba478c3f71c37"
bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene
objects = [o for o in bpy.data.objects if o.type == "MESH"]
assert len(objects) == 1, [o.name for o in objects]
body = objects[0]
mesh = body.data
assert len(mesh.vertices) == 38802 and len(mesh.polygons) == 77684
original_positions = [tuple(v.co) for v in mesh.vertices]
orig_faces = [tuple(p.vertices) for p in mesh.polygons]

# Reference guides and camera marker objects must never contaminate render.
for obj in list(scene.objects):
    if obj != body and obj.type not in ("CAMERA", "LIGHT"):
        obj.hide_render = True
for o in scene.objects:
    if o.type == "LIGHT": o.hide_render = True
worldpts = [body.matrix_world @ v.co for v in mesh.vertices]
center = sum(worldpts, Vector()) / len(worldpts)
mins = [min(v[k] for v in worldpts) for k in range(3)]
maxs = [max(v[k] for v in worldpts) for k in range(3)]
roi = [p for p in worldpts if -.59 < p.y < -.015 and -.19 < p.z < .25]
assert len(roi) > 500
roi_center = sum(roi, Vector()) / len(roi)

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 8
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
world = bpy.data.worlds.new("BASELINE_NEUTRAL_WORLD")
scene.world = world
world.use_nodes = True
world.node_tree.nodes.get("Background").inputs["Color"].default_value = (.38, .40, .44, 1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value = .8
material = bpy.data.materials.new("BASELINE_TEMPORARY_NEUTRAL_MAT")
material.diffuse_color = (.49, .53, .56, 1)
material.use_nodes = True
bsdf = material.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (.49, .53, .56, 1)
bsdf.inputs["Roughness"].default_value = .76
body.data.materials.clear()
body.data.materials.append(material)
# Not saved to source blend; render-only material.
def light(name,loc,energy,size):
    data = bpy.data.lights.new(name, "AREA")
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (center-ob.location).to_track_quat("-Z","Y").to_euler()
    data.energy = energy
    data.shape = "DISK"; data.size = size

light("SCULPT_PROOF_KEY", tuple(center + Vector((1.8, -2.0, 3.6))), 850, 4.0)
light("SCULPT_PROOF_FILL", tuple(center + Vector((-2.1, 1.8, 1.6))), 560, 5.0)
light("SCULPT_PROOF_RIM", tuple(center + Vector((1.8, 2.2, 3.0))), 450, 3.0)
dirs = {
  "SIDE": Vector((1,0,0)),
  "FRONT": Vector((0,-1,0)),
  "FRONT34": Vector((1,-1,0)).normalized(),
  "REAR34": Vector((1,1,0)).normalized(),
  "BACK": Vector((0,1,0)),
}
# These camera directions match the existing sculpt-station guides, which
# have approximate registration only. Do not claim pixel registration.
def shoot(tag, direction, target, crop=False):
    cd = bpy.data.cameras.new("REAL_S_"+tag)
    cam = bpy.data.objects.new("REAL_S_"+tag, cd)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = target + direction*5.0
    cam.rotation_euler = (target-cam.location).to_track_quat("-Z","Y").to_euler()
    bpy.context.view_layer.update()
    # Camera right/up expressed in world coordinates.
    q = cam.rotation_euler.to_quaternion()
    right = q @ Vector((1,0,0))
    up = q @ Vector((0,1,0))
    coords = roi if crop else worldpts
    w = max(p.dot(right) for p in coords)-min(p.dot(right) for p in coords)
    h = max(p.dot(up) for p in coords)-min(p.dot(up) for p in coords)
    cd.type="ORTHO"
    cd.ortho_scale = max(h, w*.75) * (1.4 if crop else 1.16)
    cd.lens = 45
    scene.render.filepath = str(OUT / (("DETAIL_" if crop else "BASELINE_")+tag+".png"))
    bpy.ops.render.render(write_still=True)
    return dict(view=tag,direction=list(direction),crop=crop,ortho_scale=cd.ortho_scale,
                image=Path(scene.render.filepath).name)

views = [shoot(tag, direction, center) for tag,direction in dirs.items()]
detail = [shoot(tag,dirs[tag],roi_center,True) for tag in ("SIDE","FRONT","FRONT34")]
assert [tuple(v.co) for v in mesh.vertices] == original_positions
assert [tuple(p.vertices) for p in mesh.polygons] == orig_faces
assert {str(p.relative_to(ROOT)): sha(p) for p in (SRC,REF)} == protect

report = dict(result="RENDERED_REAL_BASELINE_ONLY",
              source_sha256=protect,blend_version=bpy.app.version_string,
              mesh=mesh.name,vertices=len(mesh.vertices),faces=len(mesh.polygons),
              bounds_world_xyz=[mins,maxs],center=list(center),
              roi_definition_world_yz=[[-.59,-.015],[-.19,.25]],
              roi_vertices=len(roi),roi_center=list(roi_center),
              views=views,details=detail,
              render_only_material=True,
              geometry_unchanged=True,
              no_sculpt_performed=True,
              registration="APPROXIMATE ONLY; reference is authority",
              reference_front34="ILLUSTRATED",reference_rear34="UNILLUSTRATED_CONTINUITY")
(OUT/"BASELINE_GEOMETRY_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
print("S_HUNYUAN_5VIEW_REAL_RENDER_PASS",json.dumps(report),flush=True)
