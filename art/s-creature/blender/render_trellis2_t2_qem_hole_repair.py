import bpy
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(bpy.path.abspath("//")).resolve()
BASE = ROOT / "art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000"
SOURCE = BASE / "t2-meshfix/S-trellis2-clean-seed0000-maincomponent-meshfix.glb"
REPAIRED = BASE / "t2-qem-repair/S-trellis2-qem-repair-best.glb"
OUT = BASE / "t2-qem-repair/review"
OUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def import_mesh(path):
    bpy.ops.import_scene.gltf(filepath=str(path))
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        raise RuntimeError(f"No mesh objects imported from {path}")
    return objs


def world_vertices(objs):
    pts = []
    for obj in objs:
        mw = obj.matrix_world
        pts.extend(mw @ v.co for v in obj.data.vertices)
    return pts


def bounds(pts):
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    lo=Vector((min(xs),min(ys),min(zs)))
    hi=Vector((max(xs),max(ys),max(zs)))
    return lo,hi,(lo+hi)*0.5,hi-lo


def make_material():
    mat=bpy.data.materials.new("neutral_mesh")
    mat.diffuse_color=(0.64,0.66,0.69,1.0)
    mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(0.64,0.66,0.69,1.0)
        bsdf.inputs["Roughness"].default_value=0.8
        bsdf.inputs["Metallic"].default_value=0.0
    return mat


def setup_scene(objs):
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.world.color=(0.045,0.055,0.07)

    mat=make_material()
    for obj in objs:
        obj.data.materials.clear()
        obj.data.materials.append(mat)

    key=bpy.data.lights.new("Key","AREA")
    key.energy=900
    key.shape="DISK"
    key.size=5.0
    ko=bpy.data.objects.new("Key",key)
    scene.collection.objects.link(ko)
    ko.location=(3.0,-4.0,5.0)

    fill=bpy.data.lights.new("Fill","AREA")
    fill.energy=500
    fill.size=4.0
    fo=bpy.data.objects.new("Fill",fill)
    scene.collection.objects.link(fo)
    fo.location=(-4.0,2.0,3.0)

    rim=bpy.data.lights.new("Rim","AREA")
    rim.energy=650
    rim.size=3.0
    ro=bpy.data.objects.new("Rim",rim)
    scene.collection.objects.link(ro)
    ro.location=(2.0,4.0,4.0)


def detect_axes(pts, center, ext):
    # Blender glTF import converts Y-up assets to Z-up. The longer horizontal
    # axis is the creature's longitudinal body axis.
    if ext.x >= ext.y:
        long_axis=Vector((1,0,0))
        width_axis=Vector((0,1,0))
        long_extent=ext.x
    else:
        long_axis=Vector((0,1,0))
        width_axis=Vector((1,0,0))
        long_extent=ext.y

    coords=[(p-center).dot(long_axis) for p in pts]
    threshold=0.34*long_extent
    plus=[p for p,c in zip(pts,coords) if c>=threshold]
    minus=[p for p,c in zip(pts,coords) if c<=-threshold]
    # Raised head/crest end has a larger upper-Z statistic than tail end.
    plus_top=max((p.z for p in plus), default=center.z)
    minus_top=max((p.z for p in minus), default=center.z)
    front=long_axis if plus_top>=minus_top else -long_axis
    return front,width_axis


def render_views(label,path):
    clear_scene()
    objs=import_mesh(path)
    pts=world_vertices(objs)
    lo,hi,center,ext=bounds(pts)
    front,width=detect_axes(pts,center,ext)
    setup_scene(objs)

    cam_data=bpy.data.cameras.new("ReviewCamera")
    cam=bpy.data.objects.new("ReviewCamera",cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.data.type="ORTHO"

    views={
        "side": width,
        "front": front,
        "front34": (front+width).normalized(),
        "rear34": (-front+width).normalized(),
        "back": -front,
    }

    dist=max(ext.x,ext.y,ext.z)*4.0+0.5
    for name,direction in views.items():
        direction=direction.normalized()
        cam.location=center+direction*dist
        cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()

        right=Vector((-direction.y,direction.x,0.0))
        if right.length<1e-8:
            right=Vector((1,0,0))
        right.normalize()
        proj=[(p-center).dot(right) for p in pts]
        horiz=max(proj)-min(proj)
        vertical=hi.z-lo.z
        cam.data.ortho_scale=max(vertical,horiz)*1.18

        bpy.context.scene.render.filepath=str(OUT/f"{label}_{name}.png")
        bpy.ops.render.render(write_still=True)

    return {
        "label":label,
        "bounds":[list(lo),list(hi)],
        "extents":list(ext),
        "front":list(front),
        "width":list(width),
    }


source_meta=render_views("meshfix_source",SOURCE)
repair_meta=render_views("qem_repair_best",REPAIRED)

import json
(OUT/"render-meta.json").write_text(
    json.dumps({"source":source_meta,"lod":repair_meta},indent=2)+"\n"
)
print(json.dumps({"source":source_meta,"lod":repair_meta},indent=2))
