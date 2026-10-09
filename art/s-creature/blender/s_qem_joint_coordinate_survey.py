"""S QEM deformation gate stage 0: REAL anatomical-coordinate landmark survey.

Read locked QEM GLB unchanged, normalize only review-scene transforms,
save clean Blender renders and topology/vertex slices in world-space.
No guessed skeleton is inserted and no animal is replaced.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib,math
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/"experiments"
DONOR=EXP/"trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
OUT=EXP/"qem-deformation-gate-20261010"
REV=OUT/"landmark-survey"
REV.mkdir(parents=True,exist_ok=True)
sha=hashlib.sha256(DONOR.read_bytes()).hexdigest()
assert sha=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",sha
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(DONOR))
meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
assert len(meshes)==1,"Expected exact one geometry-locked QEM body"
body=meshes[0]
wm=body.matrix_world.copy()
body.parent=None
body.matrix_world=wm
bpy.context.view_layer.update()
raw=[body.matrix_world@v.co for v in body.data.vertices]
lo=Vector([min(p[i] for p in raw) for i in range(3)])
hi=Vector([max(p[i] for p in raw) for i in range(3)])
span=hi-lo
scale=2.55/span.z
offset=Vector((-(lo.x+hi.x)*scale/2,-(lo.y+hi.y)*scale/2,-lo.z*scale))
body.matrix_world=Matrix.Translation(offset)@Matrix.Scale(scale,4)@body.matrix_world
bpy.context.view_layer.update()
coords=np.asarray([body.matrix_world@v.co for v in body.data.vertices],dtype=np.float64)
mins=coords.min(axis=0);maxs=coords.max(axis=0)
assert 2.549<(maxs[2]-mins[2])<2.551
assert maxs[1]-mins[1]>3.5
assert 29948==len(body.data.vertices) and len(body.data.polygons)==59932
bm=bmesh.new();bm.from_mesh(body.data)
nonmanifold=sum(len(e.link_faces)!=2 for e in bm.edges)
bm.free()
assert nonmanifold==0

# Local density and anatomical joint candidates are DELIBERATELY kept
# observational. Do not infer a real knee from bbox midpoint.
y_edges=np.linspace(mins[1],maxs[1],25)
bins=[]
for i in range(24):
    selected=(coords[:,1]>=y_edges[i])&(coords[:,1]<(y_edges[i+1] if i<23 else y_edges[i+1]+1e-8))
    cp=coords[selected]
    if not len(cp):
        bins.append({"y_min":float(y_edges[i]),"y_max":float(y_edges[i+1]),"count":0})
        continue
    z=np.quantile(cp[:,2],[0.01,.05,.25,.5,.75,.95,.99])
    x=np.quantile(cp[:,0],[0.01,.05,.5,.95,.99])
    bins.append({"y_min":float(y_edges[i]),"y_max":float(y_edges[i+1]),
                 "count":len(cp),
                 "z_quantiles":[round(float(q),5) for q in z],
                 "x_quantiles":[round(float(q),5) for q in x]})
# Identify candidate distal foot regions: low z and off-center x.
low=coords[(coords[:,2]<=mins[2]+.31)&(np.abs(coords[:,0])>=.12)]
foot_hist=[]
for i in range(24):
    v=low[(low[:,1]>=y_edges[i])&(low[:,1]<y_edges[i+1])]
    foot_hist.append({"y_range":[round(float(y_edges[i]),3),round(float(y_edges[i+1]),3)],
                      "total_low_lateral_vertices":len(v),
                      "left":int((v[:,0]<0).sum()) if len(v) else 0,
                      "right":int((v[:,0]>0).sum()) if len(v) else 0,
                      "median_z":round(float(np.median(v[:,2])),4) if len(v) else None})

scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="SINGLE"
scene.display.shading.single_color=(.70,.73,.76)
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type="BOTH"
scene.render.resolution_x=1024;scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.world.color=(.045,.05,.065)
scene.render.film_transparent=False
camdata=bpy.data.cameras.new("SURVEY_SAME_ORTHOGRAPHIC")
cam=bpy.data.objects.new("SURVEY_SAME_ORTHOGRAPHIC",camdata)
scene.collection.objects.link(cam);scene.camera=cam;camdata.type="ORTHO";camdata.ortho_scale=5.4
center=Vector((0,0,1.275))
directions={
 "side":Vector((1,0,0)),"front":Vector((0,-1,0)),
 "front34":Vector((1,-1,0)).normalized(),
 "rear34":Vector((1,1,0)).normalized(),
 "back":Vector((0,1,0))}
for name,d in directions.items():
    cam.location=center+d*9
    cam.rotation_euler=((center-cam.location).to_track_quat("-Z","Y")).to_euler()
    scene.render.filepath=str(REV/f"S_QEM_survey_{name}.png")
    bpy.ops.render.render(write_still=True)

# Native scene saves copy of QEM mesh as untouched original topology (review
# world matrix changes only), no joints or deformation.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-pre-rig-source-review.blend"),compress=True)
qa={
 "source_sha256":sha,"source_bytes":DONOR.stat().st_size,
 "source_path":str(DONOR.relative_to(ROOT)),
 "normalized_bounds":[mins.tolist(),maxs.tolist()],
 "original_bounds":[list(lo),list(hi)],
 "normalization_scale_only":float(scale),
 "mesh_vertices":len(body.data.vertices),"mesh_faces":len(body.data.polygons),
 "nonmanifold_edges":nonmanifold,
 "scan_bins_by_body_axis_y":bins,
 "low_lateral_foot_candidate_y_bins":foot_hist,
 "view_directions":list(directions),
 "joint_landmark_status":"NOT_APPROVED: must inspect screenshot and quantitative y-z occupancy before fitting joints",
 "deformation_test_status":"NOT_STARTED",
 "original_glb_unmodified":True,
 "production_approved":False,
}
(OUT/"JOINT_LANDMARK_SURVEY.json").write_text(json.dumps(qa,indent=2)+"\n")
print("REAL_QEM_JOINT_SURVEY",json.dumps({
 "bbox":qa["normalized_bounds"],
 "foot_hist":foot_hist,
 "nonmanifold_edges":nonmanifold
},indent=2))
