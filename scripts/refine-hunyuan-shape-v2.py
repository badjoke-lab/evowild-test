import bpy
import json
import math
import os
import sys
from mathutils import Vector


def args():
    xs = sys.argv
    if "--" not in xs:
        raise SystemExit("Expected input.glb output.glb metadata.json render_dir")
    user = xs[xs.index("--")+1:]
    if len(user) != 4:
        raise SystemExit("Expected 4 args")
    return [os.path.abspath(x) for x in user]


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def join_meshes():
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    if not meshes:
        raise RuntimeError("No meshes")
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]
    if len(meshes)>1:
        bpy.ops.object.join()
    obj=bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    return obj


def mesh_bounds(obj):
    pts=[obj.matrix_world @ v.co for v in obj.data.vertices]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    b=dict(min_x=min(xs),max_x=max(xs),min_y=min(ys),max_y=max(ys),min_z=min(zs),max_z=max(zs))
    return pts,b


def detect_head_sign(pts,b):
    length=max(1e-6,b["max_z"]-b["min_z"])
    plus=[p.y for p in pts if p.z>=b["max_z"]-length*0.22]
    minus=[p.y for p in pts if p.z<=b["min_z"]+length*0.22]
    return 1 if (max(plus) if plus else b["min_y"]) >= (max(minus) if minus else b["min_y"]) else -1


def smoothstep(a,b,x):
    if a==b: return 0.0
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)


def refine_shape(obj):
    pts,b=mesh_bounds(obj)
    head_sign=detect_head_sign(pts,b)
    width=max(1e-6,b["max_x"]-b["min_x"])
    height=max(1e-6,b["max_y"]-b["min_y"])
    length=max(1e-6,b["max_z"]-b["min_z"])
    cx=(b["min_x"]+b["max_x"])*0.5
    cz=(b["min_z"]+b["max_z"])*0.5
    bottom=b["min_y"]

    stats={"vertices":len(obj.data.vertices),"head_sign":head_sign}

    for v in obj.data.vertices:
        p=obj.matrix_world @ v.co
        x,y,z=p.x,p.y,p.z
        h=(y-bottom)/height
        u=((z-cz)*head_sign)/length
        lateral=(x-cx)/width

        # 1. Raise the trunk without moving feet: longer, lighter-looking legs.
        body_lift=smoothstep(0.18,0.46,h) * (1.0-smoothstep(0.82,0.98,h))
        y += height*0.055*body_lift

        # 2. Slim torso/neck in width. Keep hoof spread and high crest largely intact.
        torso=smoothstep(0.34,0.52,h)*(1.0-smoothstep(0.82,0.96,h))
        mid_long=1.0-smoothstep(0.40,0.62,abs(u))
        neck_front=smoothstep(0.18,0.52,u)*smoothstep(0.45,0.72,h)
        width_scale=1.0 - 0.10*torso*mid_long - 0.12*neck_front
        x = cx + (x-cx)*width_scale

        # 3. Make the trunk read longer and more sprint-oriented.
        trunk=smoothstep(0.36,0.55,h)*(1.0-smoothstep(0.80,0.94,h))
        trunk*=1.0-smoothstep(0.43,0.62,abs(u))
        z += head_sign*length*(0.030*u)*trunk

        # 4. Smaller, narrower head while retaining integrated crest.
        head_zone=smoothstep(0.30,0.54,u)*smoothstep(0.52,0.72,h)
        crest_zone=smoothstep(0.36,0.62,u)*smoothstep(0.73,0.90,h)
        pure_head=max(0.0,head_zone-0.75*crest_zone)
        x = cx + (x-cx)*(1.0-0.16*pure_head)
        y_center=bottom+height*0.69
        y = y_center + (y-y_center)*(1.0-0.08*pure_head)

        # 5. Push the crest/head silhouette forward and slightly flatter.
        z += head_sign*length*(0.055*pure_head + 0.115*crest_zone)
        y += height*(0.010*pure_head + 0.018*crest_zone)

        # 6. Extend and taper rear tail silhouette.
        tail_zone=smoothstep(0.28,0.54,-u)*smoothstep(0.42,0.68,h)
        z -= head_sign*length*0.085*tail_zone
        x = cx + (x-cx)*(1.0-0.08*tail_zone)

        # 7. Slightly pull belly upward for a lighter racing body.
        belly=smoothstep(0.28,0.48,h)*(1.0-smoothstep(0.58,0.72,h))
        belly*=1.0-smoothstep(0.34,0.54,abs(u))
        y += height*0.025*belly

        local=obj.matrix_world.inverted() @ Vector((x,y,z))
        v.co=local

    bpy.context.view_layer.objects.active=obj
    obj.data.update()

    _,after=mesh_bounds(obj)
    stats["before_bounds"]=b
    stats["after_bounds"]=after
    stats["width_before"]=width
    stats["height_before"]=height
    stats["length_before"]=length
    stats["width_after"]=after["max_x"]-after["min_x"]
    stats["height_after"]=after["max_y"]-after["min_y"]
    stats["length_after"]=after["max_z"]-after["min_z"]
    return stats


def point_camera(cam,target):
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()


def setup_render():
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE"
    scene.render.resolution_x=900
    scene.render.resolution_y=700
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.world.color=(0.055,0.065,0.085)

    # Neutral studio lights; avoid Workbench headless crashes on CI.
    bpy.ops.object.light_add(type="AREA", location=(4.5,6.0,5.5))
    key=bpy.context.object
    key.data.energy=1050
    key.data.shape="DISK"
    key.data.size=5.0

    bpy.ops.object.light_add(type="AREA", location=(-4.0,2.5,3.0))
    fill=bpy.context.object
    fill.data.energy=650
    fill.data.size=4.0

    bpy.ops.object.light_add(type="AREA", location=(0.0,-4.5,4.0))
    rim=bpy.context.object
    rim.data.energy=800
    rim.data.size=3.0

    bpy.ops.object.camera_add()
    cam=bpy.context.object
    cam.data.type="ORTHO"
    scene.camera=cam
    return cam

def render_views(obj,render_dir,prefix):
    os.makedirs(render_dir,exist_ok=True)
    _,b=mesh_bounds(obj)
    cx=(b["min_x"]+b["max_x"])*0.5
    cy=(b["min_y"]+b["max_y"])*0.5
    cz=(b["min_z"]+b["max_z"])*0.5
    width=b["max_x"]-b["min_x"]
    height=b["max_y"]-b["min_y"]
    length=b["max_z"]-b["min_z"]
    span=max(width,height,length)
    cam=setup_render()
    cam.data.ortho_scale=max(height*1.18,length*0.76)

    views={
      "side":((cx+span*2.6,cy,cz),(cx,cy,cz)),
      "front":((cx,cy,cz+span*2.6),(cx,cy,cz)),
      "back":((cx,cy,cz-span*2.6),(cx,cy,cz)),
      "threequarter":((cx+span*1.9,cy+span*0.22,cz+span*1.9),(cx,cy,cz)),
    }
    for name,(loc,target) in views.items():
        cam.location=loc
        point_camera(cam,target)
        if name in ("front","back"):
            cam.data.ortho_scale=max(height*1.18,width*1.35)
        else:
            cam.data.ortho_scale=max(height*1.18,length*0.72)
        bpy.context.scene.render.filepath=os.path.join(render_dir,f"{prefix}-{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    input_path,output_path,meta_path,render_dir=args()
    os.makedirs(os.path.dirname(output_path),exist_ok=True)
    os.makedirs(os.path.dirname(meta_path),exist_ok=True)

    clear()
    bpy.ops.import_scene.gltf(filepath=input_path)
    obj=join_meshes()

    stats=refine_shape(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        export_animations=False,
        export_yup=True,
        use_selection=True
    )

    stats["status"]="shape_refine_v2_candidate_not_canonical"
    stats["source"]=os.path.basename(input_path)
    stats["output"]=os.path.basename(output_path)
    with open(meta_path,"w",encoding="utf-8") as fh:
        json.dump(stats,fh,indent=2)

    if os.path.getsize(output_path)<1024:
        raise RuntimeError("Output GLB missing/too small")
    print("SHAPE_V2",json.dumps(stats,separators=(",",":")))


if __name__=="__main__":
    main()
