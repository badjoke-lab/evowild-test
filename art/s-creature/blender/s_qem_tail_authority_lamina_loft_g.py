"""EvoWild Run S — real connected sculpted feather-tail trial G.

Uses only approved Git SHAs for the immutable S reference and TRELLIS2 donor.
This variant is built from an ACTUAL evaluated copy of existing original-QEM
tail extension A (NOT C-F's rectangular caps). For each real original skin
island, replace an ORIGINAL 3D skin patch with a continuously sewn multi-ring,
curved, narrow, tapered closed volumetric lamina. The new tail has no floating
pieces, no billboards, no R1 proxy substitution. Source is preserved. Rig,
materials and S-style approval are NOT inherited or implied.
"""
import bpy, bmesh, math, json, hashlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
OUT=BASE/"tail-authority-lamina-g-v1"
REV=OUT/"review"
REV.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
REF=ROOT/"references/00_s_type_modeling_image_v1.png"
SOURCE_HASH="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
REF_HASH="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
assert hashlib.sha256(REF.read_bytes()).hexdigest()==REF_HASH
scene=bpy.context.scene
scene.frame_set(1)
src=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
A=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
assert src.type=="MESH" and A.type=="MESH"
assert len(src.data.vertices)==29948 and len(src.data.polygons)==59932
assert len(A.data.vertices)==29948 and len(A.data.polygons)==59932

def evaluated_xyz(obj):
    bpy.context.view_layer.update()
    eo=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=eo.to_mesh()
    try:
        return np.asarray([eo.matrix_world@v.co for v in mesh.vertices],dtype=np.float64)
    finally:eo.to_mesh_clear()
src_xyz=evaluated_xyz(src)
src_hash=hashlib.sha256(src_xyz.tobytes()).hexdigest()
a_xyz=evaluated_xyz(A)
a_hash=hashlib.sha256(a_xyz.tobytes()).hexdigest()
mesh=bpy.data.meshes.new_from_object(A.evaluated_get(bpy.context.evaluated_depsgraph_get()),
                                    preserve_all_data_layers=True,
                                    depsgraph=bpy.context.evaluated_depsgraph_get())
assert len(mesh.vertices)==29948 and len(mesh.polygons)==59932
out=bpy.data.objects.new("S_QEM_REAL_TAIL_SWEPT_LAMINAE_G_DESIGN_TRIAL",mesh)
scene.collection.objects.link(out)
out.matrix_world=A.matrix_world.copy()
world=out.matrix_world.copy()
inverse=world.inverted()
bm=bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()
initial_faces=list(bm.faces)

def face_center(f):
    return sum((v.co for v in f.verts),Vector())/len(f.verts)
def eligible(f,lo,hi):
    p=world@face_center(f)
    normal=(world.to_3x3()@f.normal).normalized()
    return (lo<p.y<hi and p.z>1.46 and abs(p.x)<.25 and normal.z>.15)

def island_components(faces):
    left=set(faces)
    components=[]
    while left:
        first=left.pop()
        comp={first}
        todo=[first]
        while todo:
            f=todo.pop()
            for ed in f.edges:
                for ne in ed.link_faces:
                    if ne in left:
                        left.remove(ne)
                        comp.add(ne)
                        todo.append(ne)
        components.append(comp)
    return sorted(components,key=len,reverse=True)

def get_outer_loop(faces):
    selected=set(faces)
    half=[]
    for f in selected:
        vs=list(f.verts)
        for i in range(len(vs)):
            a,b=vs[i],vs[(i+1)%len(vs)]
            edge=bm.edges.get((a,b))
            assert edge is not None
            if sum(1 for neighbor in edge.link_faces if neighbor in selected)==1:
                half.append((a,b))
    if len(half)<6:return None,len(half),"boundary_short"
    # Face winding yields directed, consistently oriented perimeter edges.
    successors={}
    for a,b in half:
        if a in successors:return None,len(half),"multiple_outgoing"
        successors[a]=b
    start=half[0][0]
    ordered=[start]
    visited={start}
    x=start
    while True:
        if x not in successors:return None,len(half),"open_boundary"
        x=successors[x]
        if x==start:break
        if x in visited:return None,len(half),"crossing_loop"
        visited.add(x)
        ordered.append(x)
    if len(ordered)!=len(half):return None,len(half),"multiple_boundary_loops"
    return ordered,len(half),"OK"

# Strictly separate Y segments — allow two skin islands in each, for up to
# six genuine feather-like blades branching from different sides of tail.
specs=[
    {"zone":"BASE","lo":1.70,"hi":1.92,"length":.54,"arc":.095},
    {"zone":"MIDDLE","lo":2.00,"hi":2.22,"length":.74,"arc":.13},
    {"zone":"DISTAL","lo":2.30,"hi":2.54,"length":.88,"arc":.10},
]
selected=[]
selection_evidence=[]
for sp in specs:
    opts=[f for f in initial_faces if eligible(f,sp["lo"],sp["hi"])]
    groups=island_components(opts)
    selection_evidence.append({"zone":sp["zone"],
       "candidate_faces":len(opts),"island_face_counts":[len(g) for g in groups[:8]]})
    for rank,group in enumerate(groups[:2]):
        if len(group)<16:continue
        loop,edges,reason=get_outer_loop(group)
        if loop is None:
            selection_evidence[-1].setdefault("skipped",[]).append(
              {"rank":rank,"faces":len(group),"boundary":edges,"reason":reason})
            continue
        selected.append((sp,rank,group,loop))
assert len(selected)>=4,("not enough original coherent real tail patches",selection_evidence)
# Ensure all selected polygons mutually disjoint (and not a single large
# fabricated replacement plate).
allgroups=[f for sp,rank,faces,loop in selected for f in faces]
assert len(allgroups)==len(set(allgroups))
print("G_REAL_TAIL_SELECTION",json.dumps(selection_evidence),
      "separate_skin_patches",len(selected))

def smooth(x):
    t=max(0.,min(1.,float(x)))
    return t*t*(3-2*t)

plates=[]
for sp,rank,group,perimeter in selected:
    assert all(f.is_valid for f in group)
    loop,_,reason=get_outer_loop(group)
    assert loop is not None and reason=="OK"
    # Establish correct world-space root, with signed outboard side.
    points=[world@v.co for v in loop]
    center=sum(points,Vector())/len(points)
    side=-1. if rank==0 else 1.
    # The authority has overlapping posterior swept feathers, not 3 upright
    # cuboids. A multi-ring closed blade loft elongates in +Y and curves in Z.
    # Progressively narrow X width / Z thickness and end in ONE shared tip.
    length=sp["length"]*(1.0+.08*rank)
    lateral=side*(.10 + (0.055 if sp["zone"]!="BASE" else 0.025))
    vertical_offset=(-.10 if rank==1 else .04)
    def spine(t):
        return center+Vector((lateral*t, length*t,
                    sp["arc"]*math.sin(math.pi*t)+vertical_offset*t-.075*t*t))
    N=len(loop)
    oldverts=set(v for f in group for v in f.verts)
    theta=[2*math.pi*i/N for i in range(N)]
    # Deleted faces leave perimeter skin connected to new four-dimensional
    # tapered sweep. No detached plate meshes/decals allowed.
    for f in list(group):bm.faces.remove(f)
    ring_prev=loop
    rings=[.105,.22,.36,.52,.67,.80,.90,.965]
    new_vertices=0
    new_faces=0
    for t in rings:
        center_here=spine(t)
        # Smoothly convert irregular original skin boundary loop into a
        # flattened oval cross-section perpendicular to the posterior Y axis.
        morph=smooth((t-.10)/.28)
        width=.086*(1.-.82*t**1.65)
        thickness=.021*(1.-.65*t)
        next_ring=[]
        for i,p0 in enumerate(points):
            original_offset=p0-center
            ellipse=Vector((width*math.cos(theta[i]),0.,
                            thickness*math.sin(theta[i])))
            off=(1.-morph)*original_offset*(1.-.25*t)+morph*ellipse
            p=center_here+off
            v=bm.verts.new(inverse@p)
            next_ring.append(v)
        for i in range(N):
            j=(i+1)%N
            bm.faces.new((ring_prev[i],ring_prev[j],next_ring[j],next_ring[i]))
            new_faces+=1
        ring_prev=next_ring
        new_vertices+=N
    tip=bm.verts.new(inverse@spine(1.0))
    new_vertices+=1
    for i in range(N):
        bm.faces.new((ring_prev[i],ring_prev[(i+1)%N],tip))
        new_faces+=1
    # Removed cap-internal vertices must not remain as loose vertices.
    for v in oldverts:
        if v.is_valid and not v.link_faces:bm.verts.remove(v)
    plates.append({
       "zone":sp["zone"],"rank":rank,"original_patch_faces":len(group),
       "root_world":list(center),"tip_world":list(spine(1.0)),
       "length":length,"root_boundary_edges":N,
       "new_loft_rings":len(rings),
       "new_loft_vertices_requested":new_vertices,
       "new_loft_faces_requested":new_faces,
       "method":"integrated manifold skin-hole loft; no separate objects"
    })
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bm.normal_update()
# Capture BMesh face normals before final triangulation for diagnostics.
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bm.normal_update()
bm.to_mesh(mesh)
bm.free()
mesh.update()
assert all(len(f.vertices)==3 for f in mesh.polygons)
assert hashlib.sha256(evaluated_xyz(src).tobytes()).hexdigest()==src_hash
assert hashlib.sha256(evaluated_xyz(A).tobytes()).hexdigest()==a_hash

# Global manifoldness, disconnectedness, degenerates and shape metrics.
vcount=len(mesh.vertices);fcount=len(mesh.polygons)
xyz=evaluated_xyz(out)
assert len(xyz)==vcount and np.isfinite(xyz).all()
triangles=np.asarray([tuple(f.vertices) for f in mesh.polygons],dtype=np.int32)
tt=xyz[triangles]
normal=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0])
area=np.linalg.norm(normal,axis=1)
edge_use={}
links=[[] for _ in range(vcount)]
for a,b,c in triangles:
    a,b,c=int(a),int(b),int(c)
    for i,j in [(a,b),(b,c),(c,a)]:
        edge=(min(i,j),max(i,j))
        edge_use[edge]=edge_use.get(edge,0)+1
        links[i].append(j);links[j].append(i)
components=[]
reached=set()
for i in range(vcount):
    if i in reached:continue
    stack=[i];reached.add(i);nn=0
    while stack:
        v=stack.pop();nn+=1
        for neighbor in links[v]:
            if neighbor not in reached:
                reached.add(neighbor);stack.append(neighbor)
    components.append(nn)
components.sort(reverse=True)
topology={
 "vertices":vcount,"triangles":fcount,
 "components":len(components),"component_sizes":components[:10],
 "boundary_edges":sum(x==1 for x in edge_use.values()),
 "nonmanifold_or_boundary_edges":sum(x!=2 for x in edge_use.values()),
 "degenerate_faces":int(np.count_nonzero(area<1e-10)),
 "min_double_face_area":float(area.min()),
 "max_double_face_area":float(area.max())
}
print("G_MANIFOLD_AND_MESH_QA",topology)
# Optional explicit surface self-collision audit of posterior tail triangle
# subset. BVH returns true geometric overlaps; discount only shared vertices.
mask=np.mean(tt[:,:,1],axis=1)>1.55
mask &= np.mean(tt[:,:,2],axis=1)>1.28
mask &= np.abs(np.mean(tt[:,:,0],axis=1))<.55
ids=np.flatnonzero(mask)
try:
    tail_faces=[tuple(int(x) for x in triangles[k]) for k in ids]
    bvh=BVHTree.FromPolygons([Vector(v) for v in xyz],tail_faces,
                             all_triangles=True,epsilon=1.e-7)
    collisions=[]
    for ai,bi in bvh.overlap(bvh):
        if ai>=bi:continue
        facea=tail_faces[ai];faceb=tail_faces[bi]
        if set(facea)&set(faceb):continue
        collisions.append((int(ids[ai]),int(ids[bi])))
    distinct_intersections=len(collisions)
    collision_report={"status":"MEASURED","tail_face_count":len(tail_faces),
         "intersections_nonshared_vertex_faces":distinct_intersections,
         "first_30_polygon_pairs":collisions[:30]}
except Exception as e:
    collision_report={"status":"MEASUREMENT_FAILED","error":str(e)}

topology_pass=(topology["components"]==1 and
               topology["nonmanifold_or_boundary_edges"]==0 and
               topology["degenerate_faces"]==0)
self_collision_pass=(collision_report["status"]=="MEASURED" and
                     collision_report["intersections_nonshared_vertex_faces"]==0)
report={
  "canonical_reference_path":"art/s-creature/references/00_s_type_modeling_image_v1.png",
  "canonical_reference_sha256":REF_HASH,
  "original_donor_glb_sha256":SOURCE_HASH,
  "source_original_preserved":True,
  "original_A_trial_preserved":True,
  "original_source_counts":{"vertices":29948,"triangles":59932},
  "derived_tail_counts":{"vertices":vcount,"triangles":fcount},
  "original_skin_patch_selection":selection_evidence,
  "swept_laminae_connected_to_existing_skin":plates,
  "blade_count":len(plates),
  "topology":topology,
  "tail_self_collision_bvh":collision_report,
  "gate":{
    "one_connected_manifold_topology":"PASS" if topology_pass else "FAIL",
    "tail_self_collision":"PASS" if self_collision_pass else "FAIL_OR_UNVERIFIED",
    "visual_match_to_canonical":"REVIEW_PENDING_NOT_APPROVED",
    "rig_skinning":"NOT_TESTED_ON_NEW_GEOMETRY",
    "3_cycle_gait":"NOT_TESTED_ON_NEW_GEOMETRY",
    "game_production":"REJECT_NOT_APPROVED"
  },
  "method_limitations":"Original QEM branch repaired, not a certified match to S authority. New tails are actual connected swept 3D surfaces, but visual, intersection, material, rig, silhouette gates are independently required."
}
(OUT/"QEM_G_REAL_TAIL_LOFT_QA.json").write_text(json.dumps(report,indent=2)+"\n")

cam=scene.camera
assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.show_cavity=True
scene.display.shading.light="STUDIO"
scene.render.image_settings.file_format="PNG"
scene.render.resolution_x=1080
scene.render.resolution_y=810
scene.render.resolution_percentage=100
cam.data.type="ORTHO"
views={
 "SIDE":Vector((1,0,0)),"FRONT":Vector((0,-1,0)),
 "FRONT34":Vector((1,-1,0)).normalized(),
 "REAR34":Vector((1,1,0)).normalized(),
 "BACK":Vector((0,1,0))
}
for name,view in views.items():
    target=Vector((0,.16,1.28))
    cam.data.ortho_scale=6.15
    cam.location=target+view*9
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for k,obj in (("ORIGINAL_A",A),("LOFT_G",out)):
        src.hide_render=True
        A.hide_render=obj!=A
        out.hide_render=obj!=out
        scene.render.filepath=str(REV/f"REAL_S_QEM_TAIL_{k}_{name}.png")
        bpy.ops.render.render(write_still=True)
for name,view in (("SIDE",Vector((1,0,0))),
                  ("REAR34",Vector((1,1,0)).normalized()),
                  ("BACK",Vector((0,1,0)))):
    target=Vector((0,2.30,1.54))
    cam.data.ortho_scale=2.0
    cam.location=target+view*6
    cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
    for k,obj in (("ORIGINAL_A",A),("LOFT_G",out)):
        src.hide_render=True
        A.hide_render=obj!=A
        out.hide_render=obj!=out
        scene.render.filepath=str(REV/f"REAL_S_QEM_TAIL_DETAIL_{k}_{name}.png")
        bpy.ops.render.render(write_still=True)
src.hide_render=True
A.hide_render=True
out.hide_render=False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"S-QEM-real-connected-tail-lamina-loft-G-TRIAL.blend"),compress=True)
print("S_QEM_TRUE_REFERENCE_LOFT_G_FINAL",report["gate"],
      "blades",len(plates),"faces",fcount,
      "collision",collision_report["status"])
