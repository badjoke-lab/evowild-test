"""R1-A2 v2 real shoulder seam structural audit (READ ONLY).
Maps face winding, edge-to-face bends and in-scene orange high-dihedral edges.
Do not mistake review overlays for modeled creature details.
"""
from pathlib import Path
import bpy,bmesh,math,json,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output/review/authority-r1-a3-seam"
OUT.mkdir(parents=True,exist_ok=True)
body=bpy.data.objects["S_B2a_v5_continuous_body"]
m=body.data
before=hashlib.sha256(repr([(tuple(v.co)) for v in m.vertices]+[tuple(p.vertices) for p in m.polygons]).encode()).hexdigest()
bm=bmesh.new();bm.from_mesh(m);bm.normal_update();bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
def in_roi(p):
    return .072<abs(p.x)<.222 and -.245<p.y<.153 and .765<p.z<1.149
def subroi(p):
    return .075<abs(p.x)<.19 and -.18<p.y<.04 and .89<p.z<1.16
records=[];high=[]
for edge in bm.edges:
    if len(edge.link_faces)!=2:continue
    mid=(edge.verts[0].co+edge.verts[1].co)/2
    if not in_roi(mid):continue
    faces=list(edge.link_faces)
    angle=math.degrees(faces[0].normal.angle(faces[1].normal))
    edge_len=(edge.verts[0].co-edge.verts[1].co).length
    rec={"edge_index":edge.index,"v":[v.index for v in edge.verts],
         "xyz_mid":[float(x) for x in mid],
         "angle_deg":round(angle,4),"length":round(edge_len,6),
         "faces":[f.index for f in faces],
         "vertex_valences":[len(v.link_edges) for v in edge.verts],
         "face_sides":[len(f.verts) for f in faces],
         "central_shoulder_seam":bool(subroi(mid))}
    records.append(rec)
    if angle>37:high.append((edge,rec))
records.sort(key=lambda x:x["angle_deg"],reverse=True)
left=[x for x in records if x["xyz_mid"][0]<0]
right=[x for x in records if x["xyz_mid"][0]>0]
def stat(rows):
    ss=sorted(x["angle_deg"] for x in rows)
    return {"edges":len(ss),"over_37":sum(a>37 for a in ss),
            "over_60":sum(a>60 for a in ss),
            "over_90":sum(a>90 for a in ss),
            "p90":ss[min(len(ss)-1,int(.9*len(ss)))] if ss else None}
counts={"LEFT":stat(left),"RIGHT":stat(right),
        "CENTRAL":stat([r for r in records if r["central_shoulder_seam"]])}
edge_segments=[]
for edge,r in high:
    if r["angle_deg"]<=37:continue
    edge_segments.append([tuple(v.co) for v in edge.verts])
# Add a separate orange diagnostic curve, NOT part of S geometry/3D output.
curve=bpy.data.curves.new("SHOULDER_SEAM_EDGE_AUDIT","CURVE")
curve.dimensions="3D"
curve.bevel_depth=.0027
curve.bevel_resolution=1
mat=bpy.data.materials.new("QA_ONLY_ORANGE_SHARP_EDGES")
mat.diffuse_color=(1.0,.25,.01,1)
curve.materials.append(mat)
for segment in edge_segments:
    spline=curve.splines.new("POLY")
    spline.points.add(1)
    for i,point in enumerate(segment):
        spline.points[i].co=(*point,1)
obj=bpy.data.objects.new("QA_NOT_CREATURE_SHOULDER_CREASES",curve)
bpy.context.scene.collection.objects.link(obj)
obj.matrix_world=body.matrix_world.copy()
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.light="STUDIO"
scene.display.shading.show_shadows=True
scene.render.resolution_x=1024
scene.render.resolution_y=768
scene.render.resolution_percentage=100
for view in ("FRONT34","REAR34","SIDE"):
    scene.camera=bpy.data.objects["S_REBUILD_CAM_"+view]
    scene.render.filepath=str(OUT/("S_R1_A3_seam_edges_"+view.lower()+".png"))
    bpy.ops.render.render(write_still=True)
after=hashlib.sha256(repr([(tuple(v.co)) for v in m.vertices]+[tuple(p.vertices) for p in m.polygons]).encode()).hexdigest()
bm.free()
assert before==after
data={"source":"S-authority-r1-a2-scapula-v2.blend","audited_body_vertices":len(m.vertices),
      "audited_body_polygons":len(m.polygons),"original_body_geometry_unchanged":True,
      "QA_what_is_orange":"actual mesh edges above 37-degree dihedral in upper chest/shoulder zone, NOT a geometry sculpt",
      "roi":{"x_abs":[.072,.222],"y":[-.245,.153],"z":[.765,1.149]},
      "side_statistics":counts,"sharp_edge_count":len(high),
      "top_edges":records[:140],"render_views":["FRONT34","REAR34","SIDE"]}
(OUT/"SEAM_EDGE_AUDIT.json").write_text(json.dumps(data,indent=2)+"\n")
print("SEAM_TOPOLOGY_AUDIT",json.dumps({k:data[k] for k in ("side_statistics","sharp_edge_count","render_views")}))
