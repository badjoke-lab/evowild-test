"""EvoWild S real-QEM tail E: manifold supported smooth swept lamina test.

Reference + GLB SHA locked; real C sewn tail .blend remains untouched.
Create a derived high-topology mesh with multiple genuine supported plate
edge subdivisions. Round top vertices and cautiously sweep top plate tips.
Verify actual 3D triangle deformation relative to the SAME supported rest
topology and 5-view/close-up renders. Never claim S authority match until
five-view visual review. No proxy or detached fin meshes.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,hashlib,json
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-supported-f-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
assert hashlib.sha256(donor.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(ref.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
A=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
C=bpy.data.objects["S_QEM_C_SEWN_INTEGRATED_PLATES_EXPERIMENT_NOT_APPROVED"]
assert len(src.data.vertices)==len(A.data.vertices)==29948
assert len(C.data.vertices)==30029 and len(C.data.polygons)==60094
def evaluated(ob):
    bpy.context.view_layer.update()
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=eo.to_mesh()
    try:return np.asarray([eo.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:eo.to_mesh_clear()
srcxyz=evaluated(src)
srcsig=hashlib.sha256(srcxyz.tobytes()).hexdigest()
a_xyz=evaluated(A)
c_xyz=evaluated(C)
original_C_hash=hashlib.sha256(c_xyz.tobytes()).hexdigest()
assert np.isfinite(c_xyz).all()

# Identify plate cap original C vertices: >.028 from closest real trial A
tree=KDTree(len(a_xyz))
for i,v in enumerate(a_xyz):tree.insert(Vector(v),i)
tree.balance()
caps=[i for i,v in enumerate(c_xyz) if tree.find(Vector(v))[2]>.028]
assert 100<=len(caps)<=145,("cannot identify 3 plate cap vertex sets",len(caps))
# Use 3 positive-Y zones. No visible object other than real QEM skin.
regions=[
  {"name":"ROOT","ylo":1.76,"yhi":2.08},
  {"name":"MID","ylo":2.08,"yhi":2.43},
  {"name":"TIP","ylo":2.43,"yhi":2.90}
]
cap_sets=[]
for r in regions:
    indices=[i for i in caps if r["ylo"]<=c_xyz[i,1]<r["yhi"]]
    assert len(indices)>=18,(r,indices)
    cap_sets.append(indices)
print("E_TOP_SOURCE_CAP_GROUPS",list(map(len,cap_sets)))

# Full 3D original supported topology: refine the cap and sidewall edges in
# situ. BMesh subdivide of relevant ORIGINAL C edges updates neighbor faces,
# no floating surfaces. Manifoldness is remeasured after the operation.
outmesh=C.data.copy()
out=bpy.data.objects.new("S_QEM_F_TOPOLOGY_CONSTRAINED_SWEEP_NOT_APPROVED",outmesh)
bpy.context.scene.collection.objects.link(out)
out.matrix_world=C.matrix_world.copy()
bm=bmesh.new()
bm.from_mesh(outmesh)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
mw=out.matrix_world.copy()
cap_vertex_indices=set(caps)
# Edges with at least one upper cap vertex, and only in the posterior tail
# between rump and distal. These include the sidewalls joining original skin.
refine_edges=[]
for e in bm.edges:
    i,j=e.verts[0].index,e.verts[1].index
    if (i in cap_vertex_indices or j in cap_vertex_indices):
        p=mw@((e.verts[0].co+e.verts[1].co)*.5)
        if p.y>1.64 and p.z>1.34:
            refine_edges.append(e)
assert len(refine_edges)>90,len(refine_edges)
# Cut once to create support edge flow while limiting vertex budget.
bmesh.ops.subdivide_edges(bm,edges=refine_edges,cuts=1,use_grid_fill=True)
bm.normal_update()
bm.faces.ensure_lookup_table()
# All triangles for comparable actual source+C+E face metrics.
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(outmesh)
bm.free()
outmesh.update()
nverts=len(outmesh.vertices);nfaces=len(outmesh.polygons)
assert nverts>len(C.data.vertices) and nfaces>len(C.data.polygons)
assert all(len(p.vertices)==3 for p in outmesh.polygons)
# Measure face adjacency and connectivity before trusting new support topology.
def topology(me):
    faceverts=[tuple(int(x) for x in f.vertices) for f in me.polygons]
    N=len(me.vertices)
    links=[[] for _ in range(N)]
    edges={}
    for face in faceverts:
        for i in range(3):
            a,b=face[i],face[(i+1)%3]
            links[a].append(b);links[b].append(a)
            k=(min(a,b),max(a,b))
            edges[k]=edges.get(k,0)+1
    reached=set()
    components=[]
    for i in range(N):
        if i in reached:continue
        stack=[i];reached.add(i);size=0
        while stack:
            j=stack.pop();size+=1
            for k in links[j]:
                if k not in reached:
                    reached.add(k);stack.append(k)
        components.append(size)
    return {"components":len(components),"component_sizes":sorted(components,reverse=True)[:10],
            "boundary":sum(x==1 for x in edges.values()),
            "nonmanifold_or_boundary":sum(x!=2 for x in edges.values()),
            "vertices":N,"triangles":len(me.polygons)}
topo=topology(outmesh)
print("F_ACTUAL_SUPPORTED_TOPOLOGY",topo)
assert topo["components"]==1 and topo["nonmanifold_or_boundary"]==0,topo
rest=evaluated(out)
polys=np.asarray([tuple(f.vertices) for f in outmesh.polygons],dtype=np.int32)
tri=rest[polys]
norm0=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
area0=np.linalg.norm(norm0,axis=1)
assert area0.min()>1e-10,("subdivision generated tiny faces",float(area0.min()))
# Classify whole new mesh based on proximity to *cap point cloud*: important
# to distribute displacement over *sidewalls and support loops*, not just tops.
cap_points=c_xyz[caps]
cap_tree=KDTree(len(cap_points))
for i,v in enumerate(cap_points):cap_tree.insert(Vector(v),i)
cap_tree.balance()
dist=np.array([cap_tree.find(Vector(v))[2] for v in rest])
# Influence smooth transitions over .07 to prevent abrupt sidewall face stretch.
def smoother(x):
    t=np.maximum(0.,np.minimum(1.,x))
    return t*t*(3-2*t)
cap_weight=1.-smoother((dist-.012)/.095)
# Influence slightly decays at plate boundary; no moving unrelated legs/head.
mask=(rest[:,1]>1.68)&(rest[:,2]>1.32)&(np.abs(rest[:,0])<.48)
cap_weight*=mask.astype(float)
assert np.count_nonzero(cap_weight>.25)>150
# Source-preserving, separate shape key for extra supported surface.
out.shape_key_add(name="C_CONNECTED_MESH_REFINED_REST",from_mix=False)
key=out.shape_key_add(name="F_TRIANGLE_CONSTRAINED_PLATE_SWEEP",from_mix=False)
key.value=1.
inv=out.matrix_world.inverted()
def qa(actual):
    t=actual[polys]
    normals=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])
    length=np.linalg.norm(normals,axis=1)
    ratio=length/area0
    return {
        "flips":int(np.count_nonzero(np.sum(normals*norm0,axis=1)<0)),
        "collapses":int(np.count_nonzero(length<1e-10)),
        "under_half":int(np.count_nonzero(ratio<.5)),
        "over_double":int(np.count_nonzero(ratio>2.0)),
        "min_area_ratio":float(ratio.min()),"max_area_ratio":float(ratio.max())
    }
def requested_shape(stretch):
    desired=rest.copy()
    for zone in regions:
        ys=rest[:,1]
        zone_weight=smoother((ys-zone["ylo"])/.095)*(1.-smoother((ys-(zone["yhi"]-.095))/.095))
        w=zone_weight*cap_weight
        u=smoother((ys-zone["ylo"])/max(zone["yhi"]-zone["ylo"],1e-5))
        desired[:,1]+=stretch*u*w
        desired[:,2]+=.32*stretch*u*w
        desired[:,0]+=(0.020 if zone["name"]=="MID" else -0.013)*u*w
    # No unconditional ±.008 X chamfer: the E trial showed it inverted thin
    # faces even with essentially zero longitudinal sweep.
    return desired

def assign_shape(arr):
    for i,v in enumerate(arr):
        key.data[i].co=inv@Vector(v)

def bad_faces(actual):
    x=actual[polys]
    n=np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0])
    L=np.linalg.norm(n,axis=1)
    ratios=L/area0
    bad=np.flatnonzero((np.sum(n*norm0,axis=1)<0) |
                      (L<1.e-10)|(ratios<.5)|(ratios>2.))
    return bad

# Repair the *deformation field*, not the source topology. Selectively scale
# vertex shifts near actual failing triangles, respecting their neighbors.
# Keep an audit of how much the requested shaping survives constraint solving.
# Never count a near-zero solution as a meaningful aesthetic pass.
neighbors=[set() for _ in range(nverts)]
for a,b0,c in polys:
    a,b0,c=int(a),int(b0),int(c)
    neighbors[a].update((b0,c))
    neighbors[b0].update((a,c))
    neighbors[c].update((a,b0))
scans=[]
chosen=None
chosen_vertices=None
for stretch in (.13,.10,.075,.055,.040,.025,.015):
    request=requested_shape(stretch)
    displacement=request-rest
    strength=np.ones(nverts,dtype=np.float64)
    trace=[]
    for iteration in range(22):
        trial=rest+displacement*strength[:,None]
        assign_shape(trial)
        actual=evaluated(out)
        bad=bad_faces(actual)
        stats=qa(actual)
        retained=float(np.linalg.norm(actual-rest,axis=1).sum()/
                       max(np.linalg.norm(request-rest,axis=1).sum(),1.e-12))
        trace.append({
          "iter":iteration,"bad_face_count":int(len(bad)),
          "worst_ratio":stats["min_area_ratio"],
          "largest_ratio":stats["max_area_ratio"],
          "retained_displacement_fraction":retained,
          "bad_face_ids":[int(j) for j in bad[:20]]
        })
        if not len(bad):
            break
        badverts=np.unique(polys[bad].reshape(-1))
        # Scale failing faces' own vertex moves, and softly scale the boundary
        # ring so adjacent triangles are not torn by abrupt local attenuation.
        strength[badverts]*=.72
        ring=set()
        for j in badverts: ring.update(neighbors[int(j)])
        ring.difference_update(map(int,badverts))
        if ring:
            strength[np.fromiter(ring,dtype=int)]*=.94
    final=qa(actual)
    peak=float(np.linalg.norm(actual-rest,axis=1).max())
    final_bad=bad_faces(actual)
    reportrow={
      "requested_sweep":stretch,
      "face_quality":final,
      "bad_face_ids":[int(j) for j in final_bad[:50]],
      "bad_face_count":int(len(final_bad)),
      "iterations":len(trace),
      "final_displacement_retained":retained,
      "peak_vertex_motion":peak,
      "vertex_attenuation_under_half":int(np.count_nonzero(strength<.5)),
      "iterations_detail":trace,
      "triangle_pass":int(len(final_bad))==0,
      "meaningful_motion":peak>.008 and retained>.40
    }
    scans.append(reportrow)
    print("QEM_F_CONSTRAINED_SWEEP",stretch,reportrow["triangle_pass"],
          "bad",len(final_bad),"retained",retained,"peak",peak)
    if reportrow["triangle_pass"] and reportrow["meaningful_motion"]:
        chosen=reportrow
        chosen_vertices=actual.copy()
        break
if chosen is None:
    chosen=scans[-1]
    chosen_vertices=actual.copy()
assign_shape(chosen_vertices)
# Blender shape-key coordinates quantize at ~1e-7 when written again.
# Replayed safety is the face gate, not exact equality of floating min/max.
assert len(bad_faces(evaluated(out)))==0 if chosen["triangle_pass"] else True
assert hashlib.sha256(evaluated(src).tobytes()).hexdigest()==srcsig
assert hashlib.sha256(evaluated(C).tobytes()).hexdigest()==original_C_hash
report={
 "canonical_sha256":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
 "donor_glb_sha256":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
 "source_unchanged":True,"C_manifold_base_unchanged":True,
 "donor_verts":29948,"donor_tris":59932,
 "C_verts":30029,"C_tris":60094,
 "new_E_supported_topology":topo,
 "plate_cap_vertices":len(caps),
 "support_refined_edges":len(refine_edges),
 "all_candidates":scans,"selected":chosen,
 "topology_gate":"PASS_MANIFOLD_ONE_COMPONENT",
 "subdivided_mesh_deformation_gate":"PASS_CONSTRAINED" if chosen["triangle_pass"] and chosen["meaningful_motion"] else "FAIL_CONSTRAINED",
 "visual_S_design_gate":"NOT_APPROVED_REQUIRES_VISUAL_REVIEW",
 "self_intersection_validation":"NOT_TESTED",
 "rig_and_gait_on_changed_geometry":"NOT_TESTED",
 "game_ready":False
}
(OUT/"F_CONSTRAINED_TAIL_QA.json").write_text(json.dumps(report,indent=2)+"\n")
scene=bpy.context.scene
cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)), "FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),"BACK":Vector((0,1,0))
}
for view,vec in views.items():
    look=Vector((0,0,1.275))
    cam.data.ortho_scale=5.65
    cam.location=look+vec*9
    cam.rotation_euler=(look-cam.location).to_track_quat("-Z","Y").to_euler()
    for label,o in (("SEWN_C",C),("CONSTRAINED_F",out)):
        for ob in (src,A,C,out):ob.hide_render=ob!=o
        scene.render.filepath=str(REV/f"S_QEM_TAIL_{label}_{view}.png")
        bpy.ops.render.render(write_still=True)
for view,vec in (("SIDE",Vector((1,0,0))),("REAR34",Vector((1,1,0)).normalized())):
    look=Vector((0,2.19,1.64))
    cam.data.ortho_scale=1.65
    cam.location=look+vec*5
    cam.rotation_euler=(look-cam.location).to_track_quat("-Z","Y").to_euler()
    for label,o in (("SEWN_C",C),("CONSTRAINED_F",out)):
        for ob in (src,A,C,out):ob.hide_render=ob!=o
        scene.render.filepath=str(REV/f"S_QEM_TAIL_CLOSE_{label}_{view}.png")
        bpy.ops.render.render(write_still=True)
for ob in (src,A,C):ob.hide_render=True
out.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-actual-supported-tail-F-TRIAL.blend"),compress=True)
print("F_FINAL_ACTUAL_MESH",report["topology_gate"],report["subdivided_mesh_deformation_gate"],
      "vertices",nverts,"faces",nfaces,"sweep",chosen["requested_sweep"])
