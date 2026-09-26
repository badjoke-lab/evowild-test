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


def lerp(a,b,t):
    t=max(0.0,min(1.0,t))
    return a+(b-a)*t


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
        y += height*0.024*body_lift

        # 2. Slim torso/neck in width. Keep hoof spread and high crest largely intact.
        torso=smoothstep(0.34,0.52,h)*(1.0-smoothstep(0.82,0.96,h))
        mid_long=1.0-smoothstep(0.40,0.62,abs(u))
        neck_front=smoothstep(0.18,0.52,u)*smoothstep(0.45,0.72,h)
        width_scale=1.0 - 0.065*torso*mid_long - 0.10*neck_front
        x = cx + (x-cx)*width_scale

        # 3. Make the trunk read longer and more sprint-oriented.
        trunk=smoothstep(0.36,0.55,h)*(1.0-smoothstep(0.80,0.94,h))
        trunk*=1.0-smoothstep(0.43,0.62,abs(u))
        z += head_sign*length*(0.022*u)*trunk

        # 4. Smaller, narrower head while retaining integrated crest.
        head_zone=smoothstep(0.30,0.54,u)*smoothstep(0.52,0.72,h)
        crest_zone=smoothstep(0.36,0.62,u)*smoothstep(0.73,0.90,h)
        pure_head=max(0.0,head_zone-0.75*crest_zone)
        x = cx + (x-cx)*(1.0-0.12*pure_head)
        y_center=bottom+height*0.69
        y = y_center + (y-y_center)*(1.0-0.055*pure_head)

        # 5. Push the crest/head silhouette forward and slightly flatter.
        # Keep the skull slightly forward, but sweep the high crest backward
        # instead of making the whole horn fan project from the muzzle.
        z += head_sign*length*(0.048*pure_head + 0.018*crest_zone)
        crest_high=crest_zone*smoothstep(0.76,0.94,h)
        z -= head_sign*length*0.070*crest_high
        y += height*(0.004*pure_head + 0.008*crest_zone)

        # 6. Extend and taper rear tail silhouette.
        tail_zone=smoothstep(0.28,0.54,-u)*smoothstep(0.42,0.68,h)
        z -= head_sign*length*0.055*tail_zone
        x = cx + (x-cx)*(1.0-0.05*tail_zone)

        # 7. Slightly pull belly upward for a lighter racing body.
        belly=smoothstep(0.28,0.48,h)*(1.0-smoothstep(0.58,0.72,h))
        belly*=1.0-smoothstep(0.34,0.54,abs(u))
        y += height*0.014*belly

        # 8. Keep the distal legs substantial. v2 over-stretched them and made
        # the hind limbs read as wires; v2.1 restores visual mass below h=0.32.
        lower_leg=(1.0-smoothstep(0.28,0.38,h))
        leg_side=smoothstep(0.08,0.20,abs(lateral))
        x = cx + (x-cx)*(1.0 + 0.055*lower_leg*leg_side)

        # 9. Reduce deer/horse-like shoulder and rump bulk without thinning
        # the central ribcage into a tube.
        shoulder=smoothstep(0.10,0.30,u)*smoothstep(0.48,0.70,h)*(1.0-smoothstep(0.76,0.90,h))
        rump=smoothstep(0.10,0.36,-u)*smoothstep(0.48,0.70,h)*(1.0-smoothstep(0.82,0.94,h))
        x = cx + (x-cx)*(1.0 - 0.055*shoulder - 0.070*rump)

        # 10. Restore side-view mass to the distal legs. Width-only scaling
        # does not help the silhouette from the race cameras, so expand each
        # lower limb around an approximate longitudinal center as well.
        fore_center=0.205
        hind_center=-0.235
        fore_w=(1.0-smoothstep(0.075,0.15,abs(u-fore_center)))*(1.0-smoothstep(0.32,0.43,h))
        hind_w=(1.0-smoothstep(0.075,0.15,abs(u-hind_center)))*(1.0-smoothstep(0.32,0.43,h))
        if fore_w>hind_w and fore_w>0.0:
            u2=fore_center+(u-fore_center)*(1.0+0.16*fore_w)
            z=cz+u2*length*head_sign
        elif hind_w>0.0:
            u2=hind_center+(u-hind_center)*(1.0+0.18*hind_w)
            z=cz+u2*length*head_sign

        # 11. Flatten the high horse-like rump and slightly lower the
        # shoulder peak. The S morph should read long and low through the back.
        rump_top=smoothstep(0.12,0.38,-u)*smoothstep(0.70,0.83,h)*(1.0-smoothstep(0.92,0.99,h))
        shoulder_top=smoothstep(0.10,0.32,u)*smoothstep(0.70,0.83,h)*(1.0-smoothstep(0.92,0.99,h))
        y -= height*(0.026*rump_top + 0.014*shoulder_top)

        # 12. Pull the feather-like tail mass into a narrower aerodynamic
        # stream while preserving the original topology.
        tail_stream=smoothstep(0.26,0.54,-u)*smoothstep(0.40,0.70,h)
        tail_center_y=bottom+height*0.54
        x = cx + (x-cx)*(1.0-0.12*tail_stream)
        y = tail_center_y + (y-tail_center_y)*(1.0-0.13*tail_stream)
        z -= head_sign*length*0.030*tail_stream

        # 13. Lengthen the actual running chassis rather than faking length
        # with the crest/tail. Front body moves forward, rear body backward;
        # lower feet remain nearly fixed so the stance becomes more athletic.
        upper_body=smoothstep(0.34,0.52,h)
        front_split=smoothstep(0.04,0.30,u)*upper_body
        rear_split=smoothstep(0.04,0.30,-u)*upper_body
        z += head_sign*length*(0.040*front_split - 0.038*rear_split)

        # 14. Strong crest treatment: narrow the fan in frontal width, lower
        # its vertical spread, and sweep the high blades rearward. This keeps
        # the original topology but removes the upright antelope-antler read.
        crest4=smoothstep(0.18,0.44,u)*smoothstep(0.70,0.88,h)
        crest_tip=crest4*smoothstep(0.78,0.98,h)
        crest_base_y=bottom+height*0.72
        x = cx + (x-cx)*(1.0-0.22*crest4)
        y = crest_base_y + (y-crest_base_y)*(1.0-0.10*crest_tip)
        z -= head_sign*length*(0.045*crest4 + 0.095*crest_tip)

        # 15. More decisive head reduction and muzzle projection. The skull
        # remains integrated with the crest but reads less like a deer head.
        head4=smoothstep(0.24,0.48,u)*smoothstep(0.52,0.74,h)*(1.0-smoothstep(0.82,0.94,h))
        head_center_y=bottom+height*0.675
        x = cx + (x-cx)*(1.0-0.10*head4)
        y = head_center_y + (y-head_center_y)*(1.0-0.075*head4)
        z += head_sign*length*0.035*head4

        # 16. Collapse the outer tail plume toward a single balancing stream.
        # Region is restricted to the far rear/high vertices to avoid pulling
        # the hind limbs into the tail.
        tail4=smoothstep(0.34,0.58,-u)*smoothstep(0.42,0.62,h)*(1.0-smoothstep(0.78,0.90,h))
        tail_curve_y=bottom+height*(0.56-0.10*smoothstep(0.34,0.58,-u))
        x = cx + (x-cx)*(1.0-0.30*tail4)
        y = tail_curve_y + (y-tail_curve_y)*(1.0-0.30*tail4)
        z -= head_sign*length*0.055*tail4

        # 17. Turn the lowest foot regions into longer, flatter sprint feet
        # instead of compact hoof-like ends.
        foot_low=1.0-smoothstep(0.075,0.14,h)
        fore_foot=(1.0-smoothstep(0.08,0.17,abs(u-fore_center)))*foot_low
        hind_foot=(1.0-smoothstep(0.08,0.17,abs(u-hind_center)))*foot_low
        foot_w=max(fore_foot,hind_foot)
        if foot_w>0.0:
            center_u=fore_center if fore_foot>=hind_foot else hind_center
            u3=center_u+(u-center_u)*(1.0+0.22*foot_w)
            z=cz+u3*length*head_sign
            foot_y=bottom+height*0.055
            y=foot_y+(y-foot_y)*(1.0-0.12*foot_w)

        # 18. Collapse the source antler fan onto two bilateral swept blades.
        crest6=smoothstep(0.16,0.42,u)*smoothstep(0.70,0.88,h)
        if crest6>0.0:
            side=1.0 if (x-cx)>=0.0 else -1.0
            t=max(0.0,min(1.0,(h-0.70)/0.30))
            target_u=0.34-0.30*t
            target_x=cx+side*width*(0.070+0.010*(1.0-t))
            target_y=bottom+height*(0.70+0.27*t)
            target_z=cz+head_sign*length*target_u
            x=lerp(x,target_x,0.82*crest6)
            y=lerp(y,target_y,0.70*crest6)
            z=lerp(z,target_z,0.78*crest6)

        # 19. Collapse the feather fan into one tapered balancing tail axis.
        tail6=smoothstep(0.31,0.58,-u)*smoothstep(0.36,0.70,h)
        if tail6>0.0:
            r=max(0.0,min(1.0,((-u)-0.31)/0.30))
            target_y=bottom+height*(0.57-0.15*r)
            target_z=cz-head_sign*length*(0.31+0.30*r)
            x=lerp(x,cx,0.86*tail6)
            y=lerp(y,target_y,0.82*tail6)
            z=lerp(z,target_z,0.62*tail6)

        # 20. Smaller skull and cleaner neck-to-head transition.
        skull6=smoothstep(0.26,0.50,u)*smoothstep(0.52,0.76,h)*(1.0-smoothstep(0.82,0.92,h))
        skull_y=bottom+height*0.67
        x=cx+(x-cx)*(1.0-0.11*skull6)
        y=skull_y+(y-skull_y)*(1.0-0.075*skull6)
        z+=head_sign*length*0.018*skull6

        # 21. Reduce barrel-chest depth and flatten the deer-like rump.
        chassis=smoothstep(0.36,0.52,h)*(1.0-smoothstep(0.76,0.90,h))
        chassis*=1.0-smoothstep(0.38,0.56,abs(u))
        x=cx+(x-cx)*(1.0-0.055*chassis)
        rump6=smoothstep(0.12,0.36,-u)*smoothstep(0.66,0.82,h)
        y-=height*0.018*rump6

        # 22. v7 hard convergence: include the lower/back legacy crest roots
        # that v6 still left visible. Collapse almost completely to two rails.
        crest7=smoothstep(-0.02,0.36,u)*smoothstep(0.64,0.84,h)
        if crest7>0.0:
            side=1.0 if (x-cx)>=0.0 else -1.0
            t=max(0.0,min(1.0,(h-0.64)/0.36))
            target_u=0.33-0.29*t
            target_x=cx+side*width*(0.060+0.008*(1.0-t))
            target_y=bottom+height*(0.66+0.31*t)
            target_z=cz+head_sign*length*target_u
            x=lerp(x,target_x,0.94*crest7)
            y=lerp(y,target_y,0.88*crest7)
            z=lerp(z,target_z,0.92*crest7)

        # 23. v7 tail convergence: catch both the far plume and its central
        # root while excluding lateral hind-leg mass.
        central=1.0-smoothstep(0.20,0.38,abs(lateral))
        tail_far=smoothstep(0.27,0.52,-u)*smoothstep(0.30,0.76,h)
        tail_root=smoothstep(0.17,0.32,-u)*smoothstep(0.42,0.72,h)*central
        tail7=max(tail_far,tail_root)
        if tail7>0.0:
            r=max(0.0,min(1.0,((-u)-0.20)/0.42))
            target_y=bottom+height*(0.57-0.055*r)
            target_z=cz-head_sign*length*(0.24+0.38*r)
            x=lerp(x,cx,0.94*tail7)
            y=lerp(y,target_y,0.90*tail7)
            z=lerp(z,target_z,0.78*tail7)

        # 24. Pull the belly upward and reduce torso depth in side view.
        belly7=smoothstep(0.24,0.42,h)*(1.0-smoothstep(0.60,0.72,h))
        belly7*=1.0-smoothstep(0.38,0.58,abs(u))
        y+=height*0.032*belly7

        # 25. Slim the running limbs rather than restoring horse-like mass.
        leg_low=1.0-smoothstep(0.34,0.47,h)
        fore7=(1.0-smoothstep(0.085,0.17,abs(u-fore_center)))*leg_low
        hind7=(1.0-smoothstep(0.085,0.17,abs(u-hind_center)))*leg_low
        leg7=max(fore7,hind7)
        if leg7>0.0:
            center_u=fore_center if fore7>=hind7 else hind_center
            u4=center_u+(u-center_u)*(1.0-0.14*leg7)
            z=cz+u4*length*head_sign
            x=cx+(x-cx)*(1.0-0.08*leg7)

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

    stats["status"]="shape_refine_v7_hard_convergence_candidate_not_canonical"
    stats["source"]=os.path.basename(input_path)
    stats["output"]=os.path.basename(output_path)
    with open(meta_path,"w",encoding="utf-8") as fh:
        json.dump(stats,fh,indent=2)

    if os.path.getsize(output_path)<1024:
        raise RuntimeError("Output GLB missing/too small")
    print("SHAPE_V7",json.dumps(stats,separators=(",",":")))


if __name__=="__main__":
    main()
