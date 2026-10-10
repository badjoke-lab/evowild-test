"""EvoWild Run S tail morphology B — connected original-QEM plate extrusions.

Loads ACTUAL tail variant A blend and EXACT donor GLB / authoritative PNG.
Bakes A's existing-vertex extension into a new derived mesh, and raises three
skin-connected dorsal plate patches using BMesh region extrusion (NO separate
floating fin objects). Original donor and A trial both remain untouched.

This test tests mesh connectivity and visual layout, NOT design/motion approval.
No proxy geometry or artificially generated source image.
"""
from pathlib import Path
from mathutils import Vector
import bpy, bmesh, numpy as np, hashlib, json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-integrated-plates-c-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
authority=ROOT/"references/00_s_type_modeling_image_v1.png"
assert hashlib.sha256(donor.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(authority.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
trial_a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
assert src.type=="MESH" and trial_a.type=="MESH"
assert len(src.data.vertices)==len(trial_a.data.vertices)==29948
assert len(src.data.polygons)==len(trial_a.data.polygons)==59932
scene=bpy.context.scene
scene.frame_set(1)

def worldcoords(obj):
    return np.asarray([obj.matrix_world@v.co for v in obj.data.vertices],dtype=np.float64)
s0=worldcoords(src)
src_sig=hashlib.sha256(s0.tobytes()).hexdigest()
dg=bpy.context.evaluated_depsgraph_get()
obj_eval=trial_a.evaluated_get(dg)
newmesh=bpy.data.meshes.new_from_object(obj_eval,preserve_all_data_layers=True,depsgraph=dg)
assert len(newmesh.vertices)==29948 and len(newmesh.polygons)==59932
out=bpy.data.objects.new("S_QEM_C_SEWN_INTEGRATED_PLATES_EXPERIMENT_NOT_APPROVED",newmesh)
scene.collection.objects.link(out)
out.matrix_world=trial_a.matrix_world.copy()
s_a=worldcoords(out)

bm=bmesh.new()
bm.from_mesh(newmesh)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()
original_bm_faces=len(bm.faces)
original_bm_vertices=len(bm.verts)
mw=out.matrix_world.copy()
inv=mw.inverted().to_3x3()
# Anchor regions are on the dorsal portion of the ORIGINAL continuously
# connected skin. We do not add separate plate objects or loose fin meshes.
# Groups are spaced along the +Y posterior existing tail extension.
bands=[
    dict(name="PLATE_01_ROOT",ymin=1.70,ymax=1.92,lift=.175,back=.100,flare=-.045),
    dict(name="PLATE_02_MID",ymin=2.00,ymax=2.22,lift=.220,back=.145,flare=+.050),
    dict(name="PLATE_03_TIP",ymin=2.30,ymax=2.54,lift=.175,back=.190,flare=-.027),
]
def face_centroid(f):
    return sum((v.co for v in f.verts),Vector())/len(f.verts)
def dorsal(f,ymin,ymax,minup=.15):
    wc=mw@face_centroid(f)
    nw=(mw.to_3x3()@f.normal).normalized()
    return ymin<wc.y<ymax and wc.z>1.46 and abs(wc.x)<.25 and nw.z>minup
def island_components(faces):
    fs=set(faces)
    left=set(fs)
    islands=[]
    while left:
        root=left.pop()
        island={root}
        stack=[root]
        while stack:
            f=stack.pop()
            for e in f.edges:
                for n in e.link_faces:
                    if n in left:
                        left.remove(n)
                        island.add(n)
                        stack.append(n)
        islands.append(island)
    return sorted(islands,key=len,reverse=True)

def replace_skin_patch_with_integrated_plate(bm,group,spec):
    """Skin patch replacement with manifold top and individually sewn sides."""
    selected=set(group)
    old_faces=[tuple(f.verts) for f in group]
    used=set(v for f in group for v in f.verts)
    boundary=[]
    for f in group:
        fv=list(f.verts)
        for k in range(len(fv)):
            va,vb=fv[k],fv[(k+1)%len(fv)]
            e=bm.edges.get((va,vb))
            assert e is not None
            if sum(other in selected for other in e.link_faces)==1:
                boundary.append((va,vb))
    assert len(boundary)>=5,("bad plate boundary",spec["name"],len(boundary))
    delta=inv@Vector((spec["flare"],spec["back"],spec["lift"]))
    dup={v:bm.verts.new(v.co+delta) for v in used}
    for f in group:bm.faces.remove(f)
    for orig in old_faces:
        bm.faces.new(tuple(dup[v] for v in orig))
    # Original source perimeter receives the sidewall; no floating cap.
    for va,vb in boundary:
        bm.faces.new((va,vb,dup[vb],dup[va]))
    for v in used:
        if v.is_valid and len(v.link_faces)==0:
            bm.verts.remove(v)
    for e in list(bm.edges):
        if e.is_valid and len(e.link_faces)==0:bm.edges.remove(e)
    return {"boundary_edge_count":len(boundary),
            "duplicated_top_vertices":len(dup),
            "side_wall_quads":len(boundary),
            "world_displacement":[spec["flare"],spec["back"],spec["lift"]]}

plate_results=[]
for spec in bands:
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    options=[f for f in bm.faces if dorsal(f,spec["ymin"],spec["ymax"])]
    islands=island_components(options)
    group=list(islands[0]) if islands else []
    stat={
      "name":spec["name"],"band_y":[spec["ymin"],spec["ymax"]],
      "candidate_faces":len(options),
      "connected_candidate_islands":[len(x) for x in islands[:10]],
      "selected_region_faces":len(group),
    }
    print("PLATE_CANDIDATE_SELECTION",json.dumps(stat))
    assert len(group)>=3,(spec["name"],"not enough original contiguous dorsal skin",stat)
    stat.update(replace_skin_patch_with_integrated_plate(bm,group,spec))
    plate_results.append(stat)
    bm.normal_update()

# Connectedness and watertightness evaluated ON REAL RESULT. Non-manifold
# or disconnected new plate geometry must remain visible as FAIL, not PASS.
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()
pretri_total_faces=len(bm.faces)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(newmesh)
bm.free()
newmesh.update()
assert all(len(p.vertices)==3 for p in newmesh.polygons)
vcount=len(newmesh.vertices)
fcount=len(newmesh.polygons)
# Graph over mesh *edges*, not bounding-box appearances.
adj=[[] for _ in range(vcount)]
edge_usage={}
for poly in newmesh.polygons:
    vs=list(poly.vertices)
    for ii in range(3):
        aa,bb=vs[ii],vs[(ii+1)%3]
        adj[aa].append(bb)
        adj[bb].append(aa)
        e=(aa,bb) if aa<bb else (bb,aa)
        edge_usage[e]=edge_usage.get(e,0)+1
seen=set()
component_sizes=[]
for i in range(vcount):
    if i in seen:continue
    todo=[i]
    seen.add(i)
    c=0
    while todo:
        t=todo.pop()
        c+=1
        for k in adj[t]:
            if k not in seen:
                seen.add(k)
                todo.append(k)
    component_sizes.append(c)
component_sizes.sort(reverse=True)
boundary=sum(t==1 for t in edge_usage.values())
bad_edges=sum(t!=2 for t in edge_usage.values())
degenerate=sum(p.area<1e-10 for p in newmesh.polygons)

actual=np.asarray([out.matrix_world@v.co for v in newmesh.vertices],dtype=np.float64)
assert np.isfinite(actual).all()
post_source=worldcoords(src)
assert hashlib.sha256(post_source.tobytes()).hexdigest()==src_sig
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
assert len(trial_a.data.vertices)==29948 and len(trial_a.data.polygons)==59932
assert vcount>29948 and fcount>59932,("No added tail mesh topology",vcount,fcount)
# Source untouched. The derived topology MUST be flagged as NEW.
topology_gate=(bad_edges==0 and len(component_sizes)==1 and degenerate==0)
report={
 "original_source":"S-trellis2-qem-repair-best.glb",
 "source_glb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "design_png_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "original_source_preserved":True,
 "previous_A_source_preserved":True,
 "source_vertex_count":29948,"source_faces":59932,
 "variant_C_vertex_count":vcount,"variant_C_triangles":fcount,
 "new_vertex_count":vcount-29948,
 "new_triangle_count":fcount-59932,
 "pretri_faces":pretri_total_faces,
 "plate_count_requested":len(bands),
 "plate_groups":plate_results,
 "connected_component_sizes":component_sizes[:10],
 "mesh_connected_components":len(component_sizes),
 "boundary_edges":boundary,
 "nonmanifold_or_boundary_edges":bad_edges,
 "degenerate_faces":degenerate,
 "geometry_gate":"PASS_SEWN_MANIFOLD_PLATES" if topology_gate else "FAIL_SEWN_PLATE_TOPOLOGY",
 "visual_design_gate":"NOT_APPROVED_PENDING_HUMAN_REAL_FIVE_VIEW",
 "source_rig_revalidation":"NOT_RUN_ON_CHANGED_TOPOLOGY",
 "color_material":"NOT_IMPLEMENTED",
 "S_type_complete":False,
 "game_approved":False
}

cam=scene.camera
assert cam and cam.type=="CAMERA"
cam.data.type="ORTHO"
cam.data.ortho_scale=5.65
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
center=Vector((0,0,1.275))
views={
 "SIDE":Vector((1,0,0)),
 "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for tag,vec in views.items():
    cam.location=center+vec*9
    cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
    for part,visible in [
       ("SOURCE",src),("TAIL_A",trial_a),("SEWN_PLATES_C",out)]:
        for ob in (src,trial_a,out):
            ob.hide_render=(ob!=visible)
        scene.render.filepath=str(REV/f"REAL_QEM_{part}_{tag}.png")
        bpy.ops.render.render(write_still=True)
for ob in (src,trial_a):ob.hide_render=True
out.hide_render=False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-tail-sewn-plates-C-TRIAL.blend"),compress=True)
(OUT/"SEWN_TAIL_PLATES_C_QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("QEM_TAIL_PLATES_C",report["geometry_gate"],
      "original",29948,59932,"derived",vcount,fcount,
      "components",len(component_sizes),"nonmanifold",bad_edges,
      "selected",[x["selected_region_faces"] for x in plate_results])
