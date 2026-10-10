"""QEM anatomical joint-candidate survey on the ORIGINAL 3D mesh.
NOTE: landmarks represent measured geometric regions, NOT approved bones.
No donor geometry or topology modifications. Overlay is diagnostic only.
"""
from pathlib import Path
import bpy,json,hashlib
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/qem-deformation-gate-20261010/joint-anatomy-survey-v2"
OUT.mkdir(parents=True,exist_ok=True)
source=bpy.data.objects["geometry_0"] if "geometry_0" in bpy.data.objects else next(o for o in bpy.data.objects if o.type=="MESH")
coords=np.asarray([source.matrix_world@v.co for v in source.data.vertices],dtype=float)
assert coords.shape==(29948,3)
digest=hashlib.sha256(coords.tobytes()).hexdigest()
# Candidate windows derived from source QEM's fore (-Y), hind (+Y),
# transverse (X) and upright (Z) directions; not textbook quadruped loci.
WINDOWS={
"FORE_SHOULDER":(-1.04,-.36,1.16,1.70,.13,.53),
"FORE_ELBOW":(-1.10,-.34,.61,1.14,.15,.55),
"FORE_WRIST":(-1.53,-.55,.20,.53,.15,.58),
"HIND_HIP":(.80,1.57,1.24,1.92,.13,.50),
"HIND_STIFLE":(1.12,1.89,.86,1.26,.14,.53),
"HIND_HOCK":(1.57,2.25,.38,.84,.15,.57)
}
# Need centroid of local actual surface vertices around each anatomy zone;
# use percentile robust median and report nearest real surface point index.
joint={}
for side in (-1,1):
    prefix="L" if side<0 else "R"
    for name,(a,b,c,d,x0,x1) in WINDOWS.items():
        mask=(coords[:,1]>=a)&(coords[:,1]<=b)&(coords[:,2]>=c)&(coords[:,2]<=d)&(side*coords[:,0]>=x0)&(side*coords[:,0]<=x1)
        idx=np.flatnonzero(mask)
        if len(idx)<20:
            raise RuntimeError(f"Not enough actual QEM surface coordinates {prefix}_{name}: {len(idx)}")
        med=np.median(coords[idx],axis=0)
        nearest_idx=int(idx[np.argmin(np.linalg.norm(coords[idx]-med[None,:],axis=1))])
        p=coords[nearest_idx]
        joint[prefix+"_"+name]={"surface_vertex_index":nearest_idx,"xyz":list(map(float,p)),
           "median_region_xyz":list(map(float,med)),"source_region_vertex_count":len(idx),
           "region":{"y":[a,b],"z":[c,d],"absolute_x":[x0,x1]},
           "approved":False}
# Explicitly do not save the original QEM as altered geometry.
color={
 "FORE_SHOULDER":(.95,.65,.12,1),"FORE_ELBOW":(.9,.38,.08,1),"FORE_WRIST":(.95,.18,.08,1),
 "HIND_HIP":(.12,.62,1,1),"HIND_STIFLE":(.12,.83,.79,1),"HIND_HOCK":(.39,.43,1,1)}
for key,item in joint.items():
    name=key[2:]
    p=item["xyz"]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.045,location=p)
    ball=bpy.context.object
    ball.name="QA_JOINT_NOT_GEOMETRY_"+key
    mat=bpy.data.materials.new("QA_COLOR_"+key);mat.diffuse_color=color[name]
    ball.data.materials.append(mat)
    ball.display_type="WIRE"
    ball.hide_render=False
# Use consistent five baseline cameras but zoom slightly for anatomical read.
scene=bpy.context.scene
camera=scene.camera
assert camera and camera.data.type=="ORTHO"
camdirs={
"side":Vector((1,0,0)),"front":Vector((0,-1,0)),
"front34":Vector((1,-1,0)).normalized(),
"rear34":Vector((1,1,0)).normalized(),"back":Vector((0,1,0))}
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_cavity=True
scene.render.resolution_x=1024;scene.render.resolution_y=768
scene.render.resolution_percentage=100
center=Vector((0,0,1.275))
for name,d in camdirs.items():
    camera.location=center+d*9
    camera.rotation_euler=((center-camera.location).to_track_quat("-Z","Y")).to_euler()
    camera.data.ortho_scale=4.55
    scene.render.filepath=str(OUT/f"QEM_joint_candidates_{name}.png")
    bpy.ops.render.render(write_still=True)
after=np.asarray([source.matrix_world@v.co for v in source.data.vertices],dtype=float)
assert hashlib.sha256(after.tobytes()).hexdigest()==digest
result={
 "source":"S-QEM-pre-rig-source-review.blend derived from immutable QEM GLB",
 "source_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "original_mesh_untouched":True,
 "source_vertex_count":29948,
 "marker_count":len(joint),
 "joint_candidates":joint,
 "views":["side","front","front34","rear34","back"],
 "position_status":"GEOMETRY_DERIVED_CANDIDATES_NOT_ANATOMICAL_APPROVAL",
 "physical_joint_bend_not_run_here":True,
 "game_ready":False
}
(OUT/"JOINT_CANDIDATE_SURVEY.json").write_text(json.dumps(result,indent=2)+"\n")
print("JOINT_CANDIDATE_SURVEY",json.dumps({k:{"pos":v["xyz"],"points":v["source_region_vertex_count"]} for k,v in joint.items()},indent=2))
