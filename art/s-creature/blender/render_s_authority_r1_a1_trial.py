"""EvoWild S Authority R1-A1 v1: five real model angles, render-only.

No additional modeling, no topology changes. Source of truth is the already
accepted R0 morphology and the locked source reference artwork.
"""
import bpy,os,json,hashlib
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output")
REV=os.path.join(OUT,"review","authority-r1-a1-trial")
os.makedirs(REV,exist_ok=True)
VAL=os.path.join(OUT,"S-authority-r1-a1-v1-validation.json")
report=json.load(open(VAL))
assert report["status"]=="REVIEW_PENDING"
assert report["r0_status"]=="ACCEPTED_R0_MORPHOLOGY"
assert report["outside_support_unchanged"] and report["body_topology_unchanged"]
assert report["separate_meshes_unchanged"] and report["body_nonmanifold_edge_count"]==0
assert report["camera_transforms_unchanged"]
assert report["roughness_after_mean"]<report["roughness_before_mean"]

def geometry_digest():
    h=hashlib.sha256()
    objs=sorted((o for o in bpy.data.objects if o.type=="MESH"),key=lambda o:o.name)
    for o in objs:
        h.update(o.name.encode())
        h.update(str(len(o.data.vertices)).encode())
        for v in o.data.vertices:h.update(repr(tuple(v.co)).encode())
        for face in o.data.polygons:h.update(repr(tuple(face.vertices)).encode())
        h.update(repr(tuple(tuple(r) for r in o.matrix_world)).encode())
    return h.hexdigest()

before=geometry_digest()
scene=bpy.context.scene
views=("side","front","front34","rear34","back")
for stem in views:
    cam=bpy.data.objects["S_REBUILD_CAM_"+stem.upper()]
    assert cam.type=="CAMERA"
    scene.camera=cam
    scene.render.filepath=os.path.join(REV,f"S_authority_r1_a1_{stem}.png")
    bpy.ops.render.render(write_still=True)
after=geometry_digest()
assert before==after,"RENDER_CHANGED_GEOMETRY"
report["rendered_views"]=list(views)
report["render_geometry_sha256_before"]=before
report["render_geometry_sha256_after"]=after
report["render_geometry_unchanged"]=True
report["decision"]="REVIEW_PENDING_ACTUAL_IMAGES"
with open(VAL,"w") as f:json.dump(report,f,indent=2)
print("S_R1_A1_FIVE_REAL_VIEWS_DONE",json.dumps({
  "views":list(views),
  "max_displacement":report["max_displacement"],
  "roughness_ratio":report["roughness_mean_ratio"],
  "geometry_unchanged":True
}))
