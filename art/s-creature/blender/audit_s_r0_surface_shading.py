"""R0 geometry-level cause analysis and read-only smooth-normal counterfactual.

No shape edits to existing accepted R0 source. This only diagnoses actual
polygon/vertex shading and records high-angle shoulder/pelvis edges.
"""
import bpy,bmesh,os,json,math,hashlib
from collections import defaultdict
from mathutils import Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"output","review","authority-r1-a1-trial","R0_FACETING_DIAGNOSTIC")
os.makedirs(OUT,exist_ok=True)
body=bpy.data.objects["S_B2a_v5_continuous_body"]
mesh=body.data
orig_smooth=sum(p.use_smooth for p in mesh.polygons)
verts=[tuple(v.co) for v in mesh.vertices]
faces=[tuple(p.vertices) for p in mesh.polygons]
def weighted(x):
    return ((-.18<x.y<.26) and (.65<x.z<1.16) and (abs(x.x)>.04)), ((.55<x.y<1.03) and (.65<x.z<1.16) and (abs(x.x)>.04))
bm=bmesh.new();bm.from_mesh(mesh)
bm.normal_update()
edges=[]
for e in bm.edges:
    if len(e.link_faces)!=2:continue
    a,b=e.link_faces
    angle=a.normal.angle(b.normal)*180/math.pi
    midpoint=sum((v.co for v in e.verts),Vector())/2
    fore,hind=weighted(midpoint)
    if fore or hind:
        edges.append({"edge_indices":[v.index for v in e.verts],"dihedral_degrees":float(angle),"midpoint":[float(v) for v in midpoint],"side":"FORE" if fore else "HIND"})
bm.free()
edges.sort(key=lambda o:o["dihedral_degrees"],reverse=True)
regions={}
for name in ["FORE","HIND"]:
    vals=[p["dihedral_degrees"] for p in edges if p["side"]==name]
    vals.sort()
    regions[name]={
      "edge_count":len(vals),
      "mean_angle_deg":sum(vals)/len(vals) if vals else None,
      "median_angle_deg":vals[len(vals)//2] if vals else None,
      "p90_deg":vals[min(len(vals)-1,int(.9*len(vals)))] if vals else None,
      "sharp_edges_gt_40deg":sum(v>40 for v in vals),
      "sharp_edges_gt_60deg":sum(v>60 for v in vals)
    }
# Diagnostic copy receives smooth normals, original remains untouched.
copy=body.copy();copy.data=body.data.copy()
copy.name="DIAGNOSTIC_SMOOTH_NORMALS_NO_GEOMETRY_CHANGE"
bpy.context.collection.objects.link(copy)
body.hide_render=True
for polygon in copy.data.polygons:
    polygon.use_smooth=True
before=hashlib.sha256(repr([verts,faces]).encode()).hexdigest()
after=hashlib.sha256(repr([[tuple(v.co) for v in mesh.vertices],[tuple(p.vertices) for p in mesh.polygons]]).encode()).hexdigest()
assert before==after
scene=bpy.context.scene
for stem in ("SIDE","FRONT34","REAR34"):
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+stem]
    scene.render.filepath=os.path.join(OUT,"S_R0_smooth_normal_only_"+stem.lower()+".png")
    bpy.ops.render.render(write_still=True)
report={
 "source":"S-authority-r0-a5-v2.blend",
 "body_object":body.name,
 "body_vertices":len(verts),"body_faces":len(faces),
 "face_smooth_count_original":orig_smooth,
 "flat_shaded_faces_original":len(faces)-orig_smooth,
 "source_geometry_unchanged":True,
 "high_curvature_regions":regions,
 "top_sharp_edges":edges[:80],
 "modification":"SHADING_NORMALS_DIAGNOSTIC_ONLY - no morphology or topology changes",
 "render_views":["side","front34","rear34"],
 "production_ready":False
}
with open(os.path.join(OUT,"R0_SHADING_AND_DIhedral.json"),"w") as f:json.dump(report,f,indent=2)
print("R0_DIAGNOSTIC",json.dumps({k:v for k,v in report.items() if k!="top_sharp_edges"}))
