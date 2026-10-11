"""EvoWild S actual QEM integrated leaf V — real sewn root collar RETOPOLOGY.

Rebuild selected ORIGINAL M tail skin hole + its first two support loops
as a tangential, smoothly raised stepped transition instead of Q's folding
root-to-ellipse strip. Each candidate is a newly constructed Blender mesh
with a NEW longitudinal ring topology (not U's weighted position shifts).
Test true evaluated geometry, full manifold, face winding and tail BVH self-
intersection. Keep entire benchmark even if every attempt fails.

SOURCE AUTHORITY = sole user approved 00_s_type_modeling_image_v1.png.
No R0/R1 proxy, no flat image as actual asset, no production promotion.
"""
import bpy,bmesh,numpy as np,math,hashlib,json,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/qem-deformation-gate-20261010"
PANEL=os.environ.get("Q_V_CASE","")
assert PANEL in ("PROXIMAL_RIGHT","DISTAL_RIGHT"),PANEL
OUT=BASE/("tail-integrated-collar-v-"+PANEL.lower())
REVIEW=OUT/"review"
REVIEW.mkdir(parents=True,exist_ok=True)
REFERENCE=ROOT/"references/00_s_type_modeling_image_v1.png"
DONOR=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
RS="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
GS="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest()==RS
assert hashlib.sha256(DONOR.read_bytes()).hexdigest()==GS
s=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
a=bpy.data.objects["S_QEM_TAIL_MORPH_TEST_A_NOT_APPROVED"]
m=bpy.data.objects["S_REAL_QEM_UNIFORM_ANGULAR_TAIL_M_NOT_APPROVED"]
assert (len(s.data.vertices),len(s.data.polygons))==(29948,59932)
assert (len(m.data.vertices),len(m.data.polygons))==(31948,63932)
base_m=m.matrix_world.copy()
scene=bpy.context.scene
scene.frame_set(1)
def eval_xyz(ob):
    bpy.context.view_layer.update()
    eo=ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me=eo.to_mesh()
    try:return np.asarray([eo.matrix_world@v.co for v in me.vertices],dtype=np.float64)
    finally:eo.to_mesh_clear()
source_sig=hashlib.sha256(eval_xyz(s).tobytes()).hexdigest()
M_sig=hashlib.sha256(eval_xyz(m).tobytes()).hexdigest()

plans={
  "PROXIMAL_RIGHT":{"y0":1.79,"y1":1.91,"angle":.40,
     "half":.59,"length":.59,"spread":.19,"rise":.12,"width":.13},
  "DISTAL_RIGHT":{"y0":2.63,"y1":2.75,"angle":.52,
     "half":.56,"length":.64,"spread":.15,"rise":.07,"width":.11}}
plan=plans[PANEL]
nrad=Vector((math.cos(plan["angle"]),0.,math.sin(plan["angle"])))
tangent=Vector((-math.sin(plan["angle"]),0.,math.cos(plan["angle"])))

def smooth(x):
    y=max(0.,min(1.,float(x)))
    return y*y*(3-2*y)
def frame(y):
    t=max(0.,min(1.,(y-1.64)/1.97))
    return Vector((.008617273531+.032*math.sin(math.pi*t),y,
       1.599118232727+.065*math.sin(math.pi*t)-.33*t-.12*t*t))
def arc(p):
    return math.atan2(p.z-frame(p.y).z,p.x-frame(p.y).x)
def diff(x,y):
    return abs((x-y+math.pi)%(2*math.pi)-math.pi)

def make_mesh(case_id,y_margin,half_extra,transition_radial,transition_alpha,outer_sweep):
    """Genuinely rebuild M patch in a new BMesh, with two NEW collar rings."""
    new=m.copy();new.data=m.data.copy()
    new.name="V_ACTUAL_QEM_"+PANEL+"_CANDIDATE_"+str(case_id)
    scene.collection.objects.link(new)
    new.matrix_world=m.matrix_world.copy()
    mw=new.matrix_world.copy()
    inv=mw.inverted()
    bm=bmesh.new();bm.from_mesh(new.data)
    bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
    f0=list(bm.faces)
    def center(face):
        return mw@(sum((v.co for v in face.verts),Vector())/len(face.verts))
    matches=[f for f in f0 if
        plan["y0"]-y_margin<center(f).y<plan["y1"]+y_margin
        and diff(arc(center(f)),plan["angle"])<plan["half"]+half_extra]
    remaining=set(matches);groups=[]
    while remaining:
        first=min(remaining,key=lambda f:f.index)
        remaining.remove(first);group={first};queue=[first]
        while queue:
            f=queue.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in remaining:
                        remaining.remove(g);group.add(g);queue.append(g)
        groups.append(group)
    if not groups:return None,{"reject":"no source-M faces"}
    patch=sorted(groups,key=lambda faces:(-len(faces),min(x.index for x in faces)))[0]
    # Directed source-boundary with stable seam anchor.
    boundary=[]
    for f in sorted(patch,key=lambda f:f.index):
        verts=list(f.verts)
        for i in range(len(verts)):
            start,end=verts[i],verts[(i+1)%len(verts)]
            e=bm.edges.get((start,end))
            if sum(near in patch for near in e.link_faces)==1:
                boundary.append((start,end))
    successors={}
    for aa,bb in boundary:
        if aa in successors:
            bm.free();bpy.data.objects.remove(new,do_unlink=True)
            return None,{"reject":"more than one outgoing boundary"}
        successors[aa]=bb
    if not (8<=len(boundary)<=95):
        bm.free();bpy.data.objects.remove(new,do_unlink=True)
        return None,{"reject":"seam size","edges":len(boundary)}
    ordered=[min(successors,key=lambda v:v.index)]
    seen=set(ordered);vertex=ordered[0]
    while True:
        if vertex not in successors:break
        vertex=successors[vertex]
        if vertex==ordered[0]:break
        if vertex in seen:break
        ordered.append(vertex);seen.add(vertex)
    if len(ordered)!=len(boundary):
        bm.free();bpy.data.objects.remove(new,do_unlink=True)
        return None,{"reject":"multiple perimeter loops","seen":len(ordered),"edges":len(boundary)}
    pts=[mw@v.co for v in ordered]
    centroid=sum(pts,Vector())/len(pts)
    # NEW collar topology:
    # ring 1 at y+ .006 with gentle normal projected push;
    # ring 2 at y+ .018 + increasing projected push;
    # ring 3 at y+ .033: transition to sweep. All downstream tapered leaf
    # rings maintain the original perimeter arclength order.
    offsets=[(pts[(i+1)%len(pts)]-pts[i]).length for i in range(len(pts))]
    total=sum(offsets);weights=[0.]
    for d in offsets[:-1]:weights.append(weights[-1]+d)
    angles=[2*math.pi*d/total for d in weights]
    oldverts={v for f in patch for v in f.verts}
    for f in sorted(patch,key=lambda f:f.index):bm.faces.remove(f)
    previous=ordered
    # Two newly inserted geometric collar rings (not an offset of Q).
    rings=[.010,.031,.066,.112,.17,.23,.34,.47,.60,.73,.84,.92,.965]
    for t in rings:
        y_step=plan["length"]*t
        mean=(centroid+Vector((0.,y_step,0.))
             +nrad*plan["spread"]*smooth(t/.50)*outer_sweep
             +Vector((0,0,plan["rise"]*t)))
        width=plan["width"]*max(.018,math.sin(math.pi*t)**.8)
        depth=.023*max(.030,math.sin(math.pi*t)**.68)
        # First two rings: keep each boundary's original Z/X topology and
        # project slightly outward. t>.066: blend to supporting swept ellipses.
        radial=transition_radial*smooth(t/.090)
        blend=smooth((t-.025)/(transition_alpha-.025))
        next_loop=[]
        for i,theta in enumerate(angles):
            inherited=pts[i]+Vector((0,y_step,0))+nrad*radial
            blade=mean+tangent*(width*math.cos(theta))+nrad*(depth*math.sin(theta))
            pp=inherited*(1.-blend)+blade*blend
            next_loop.append(bm.verts.new(inv@pp))
        for i in range(len(previous)):
            j=(i+1)%len(previous)
            bm.faces.new((previous[i],previous[j],next_loop[j],next_loop[i]))
        previous=next_loop
    tip=(centroid+Vector((0,plan["length"],plan["rise"]))+
         nrad*plan["spread"]*outer_sweep)
    vtip=bm.verts.new(inv@tip)
    for i in range(len(previous)):
        bm.faces.new((previous[i],previous[(i+1)%len(previous)],vtip))
    for v in sorted(oldverts,key=lambda v:v.index):
        if v.is_valid and not v.link_faces:bm.verts.remove(v)
    for e in list(bm.edges):
        if e.is_valid and not e.link_faces:bm.edges.remove(e)
    bm.faces.ensure_lookup_table()
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bm.normal_update()
    bm.to_mesh(new.data);bm.free()
    new.data.update()
    return new,{"patch_faces":len(patch),"seam_edges":len(boundary),
                "ring_count":len(rings),"root_world":list(centroid),
                "tip_world":list(tip),"y_margin":y_margin,
                "angular_margin":half_extra,"collar_clearance":transition_radial,
                "full_blade_transition_t":transition_alpha,
                "outer_sweep_multiplier":outer_sweep}

def check_geometry(ob):
    verts=eval_xyz(ob)
    tri=np.asarray([tuple(f.vertices) for f in ob.data.polygons],dtype=np.int32)
    surface=verts[tri];cent=surface.mean(axis=1)
    areas=np.linalg.norm(np.cross(surface[:,1]-surface[:,0],
                                   surface[:,2]-surface[:,0]),axis=1)
    n=len(verts);adj=[[] for _ in range(n)];edges={}
    for xa,xb,xc in tri:
        aa,bb,cc=int(xa),int(xb),int(xc)
        for x,y in ((aa,bb),(bb,cc),(cc,aa)):
            e=(min(x,y),max(x,y))
            edges[e]=edges.get(e,0)+1
            adj[x].append(y);adj[y].append(x)
    connected=0;seen=set()
    for i in range(n):
        if i in seen:continue
        connected+=1;stack=[i];seen.add(i)
        while stack:
            a=stack.pop()
            for b in adj[a]:
                if b not in seen:seen.add(b);stack.append(b)
    # Preserve winding: shared edges must be opposed.
    orientation={}
    for xa,xb,xc in tri:
        aa,bb,cc=int(xa),int(xb),int(xc)
        for x,y in ((aa,bb),(bb,cc),(cc,aa)):
            e=(min(x,y),max(x,y))
            orientation[e]=orientation.get(e,0)+(1 if x<y else -1)
    inverted_winding=sum(v!=0 for v in orientation.values())
    ROI=np.flatnonzero((cent[:,1]>1.5)&(cent[:,2]>.94)&(np.abs(cent[:,0])<.7))
    roi_faces=[tuple(map(int,tri[i])) for i in ROI]
    bvh=BVHTree.FromPolygons([Vector(v) for v in verts],roi_faces,
                            all_triangles=True,epsilon=1e-7)
    overlap=[]
    for i,j in bvh.overlap(bvh):
        if i>=j:continue
        if set(roi_faces[i])&set(roi_faces[j]):continue
        overlap.append((int(ROI[i]),int(ROI[j])))
    qa={
      "vertices":n,"triangles":len(tri),"components":connected,
      "boundary_edges":sum(v==1 for v in edges.values()),
      "nonmanifold_or_boundary_edges":sum(v!=2 for v in edges.values()),
      "edge_winding_invalid":inverted_winding,
      "degenerate_faces":int(np.count_nonzero(areas<1e-10)),
      "minimum_double_face_area":float(areas.min()),
      "ROI_faces":len(ROI),"self_intersections":len(overlap),
      "first_30_overlap_face_pairs":sorted(overlap)[:30],
      "geometry_digest_sha256_rounded6":hashlib.sha256(np.round(verts,6).tobytes()).hexdigest()
    }
    qa["topology_pass"]=(connected==1 and qa["nonmanifold_or_boundary_edges"]==0
                         and qa["edge_winding_invalid"]==0 and qa["degenerate_faces"]==0)
    qa["all_geometry_pass"]=qa["topology_pass"] and qa["self_intersections"]==0
    return qa

# Broad patch and a true two-ring collar. Exclude original failed Q's old
# fixed support rings, and avoid merely varying a shape-key offset.
cases=[
 (.00,.00,.018,.10,1.0),(.00,.00,.035,.10,1.0),
 (.00,.00,.050,.10,1.0),(.00,.00,.070,.10,1.0),
 (.025,.00,.018,.10,1.0),(.025,.00,.035,.10,1.0),
 (.025,.00,.050,.10,1.0),(.025,.00,.070,.10,1.0),
 (.050,.00,.018,.10,1.0),(.050,.00,.035,.10,1.0),
 (.050,.00,.050,.10,1.0),(.050,.00,.070,.10,1.0),
 (.025,.12,.035,.14,1.0),(.050,.12,.035,.14,1.0),
 (.025,.12,.050,.14,1.0),(.050,.12,.050,.14,1.0),
 (.025,.12,.050,.20,1.0),(.050,.12,.050,.20,1.0),
 (.025,.12,.070,.20,1.0),(.050,.12,.070,.20,1.0),
 (.025,.00,.035,.20,1.20),(.050,.00,.035,.20,1.20),
 (.025,.12,.070,.20,1.20),(.050,.12,.070,.20,1.20)
]
rows=[];winner=None;winner_object=None
for idx,(ym,ang,collar,alpha,extension) in enumerate(cases):
    ob,meta=make_mesh(idx,ym,ang,collar,alpha,extension)
    if ob is None:
        rows.append({"id":idx,"settings":list(cases[idx]),"error":meta})
        print("V_TOPOLOGY_SKIP",PANEL,idx,meta)
        continue
    qa=check_geometry(ob)
    row={"id":idx,"settings":list(cases[idx]),
         "root_and_ring_mesh":meta,"QA":qa}
    rows.append(row)
    print("V_TRUE_SEWN_RETOPOLOGY",PANEL,idx,
          "rootEdges",meta["seam_edges"],
          "geometry",qa["all_geometry_pass"],
          "collisions",qa["self_intersections"],
          "component",qa["components"],"windingBad",qa["edge_winding_invalid"])
    score=(0 if qa["topology_pass"] else 1,
           qa["self_intersections"],0 if qa["all_geometry_pass"] else 1,
           abs(ym)+abs(ang)+collar)
    if winner is None or score<winner[0]:
        if winner_object:
            bpy.data.objects.remove(winner_object,do_unlink=True)
        winner=(score,row)
        winner_object=ob
    else:bpy.data.objects.remove(ob,do_unlink=True)
    if qa["all_geometry_pass"]:break
assert winner is not None,("No valid topology candidate",PANEL,rows)
best=winner[1]
obj=winner_object
finalqa=check_geometry(obj)
assert finalqa==best["QA"],"Selected persisted geometry differs from tested actual mesh."
assert hashlib.sha256(eval_xyz(s).tobytes()).hexdigest()==source_sig
assert hashlib.sha256(eval_xyz(m).tobytes()).hexdigest()==M_sig
report={
 "original_reference_sha256":RS,"original_donor_QEM_glb_sha256":GS,
 "source_mesh_unchanged":True,"original_M_mesh_unchanged":True,
 "original_QEM_counts":[29948,59932],"M_base_counts":[31948,63932],
 "panel":PANEL,
 "previous_single_Q_nonshared_tail_intersections":{"PROXIMAL_RIGHT":34,"DISTAL_RIGHT":152}[PANEL],
 "previous_U_best_intersections":{"PROXIMAL_RIGHT":24,"DISTAL_RIGHT":119}[PANEL],
 "construction":"new direct M-skin hole with TWO NEW support collar loops, recalculated seam and swept lamina",
 "candidates_tested":len(rows),"candidates":rows,"selected":best,
 "selected_actual_qa_repeated":finalqa,
 "technical_gate":"PASS" if finalqa["all_geometry_pass"] else "FAIL",
 "canonical_design_visual_gate":"NOT_APPROVED",
 "whole_body_S_morph":"NOT_APPROVED",
 "skin_weights_for_new_topology":"NOT_YET_TESTED",
 "game_production":"REJECT_NOT_APPROVED"
}
(OUT/"REAL_QEM_V_NEW_ROOT_TOPOLOGY_QA.json").write_text(json.dumps(report,indent=2)+"\n")
# Real Blender same-camera outputs; NEVER use generated reference images.
cam=scene.camera;assert cam and cam.type=="CAMERA"
scene.render.engine="BLENDER_WORKBENCH";scene.display.shading.show_cavity=True
scene.render.resolution_x=1060;scene.render.resolution_y=795
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
cam.data.type="ORTHO"
views={
"SIDE":Vector((1,0,0)),"FRONT":Vector((0,-1,0)),
"FRONT34":Vector((1,-1,0)).normalized(),
"REAR34":Vector((1,1,0)).normalized(),"BACK":Vector((0,1,0))}
for name,direction in views.items():
    focus=Vector((0,.20,1.25))
    cam.data.ortho_scale=6.5
    cam.location=focus+direction*9
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,target in (("M_BASE",m),("NEW_V",obj)):
        for item in (s,a,m,obj):item.hide_render=(item!=target)
        scene.render.filepath=str(REVIEW/f"REAL_QEM_{PANEL}_{tag}_{name}.png")
        bpy.ops.render.render(write_still=True)
for name,direction in (("SIDE",Vector((1,0,0))),
                        ("REAR34",Vector((1,1,0)).normalized())):
    focus=Vector((0,(plan["y0"]+plan["y1"])/2+.20,
                  1.65 if PANEL=="PROXIMAL_RIGHT" else 1.50))
    cam.data.ortho_scale=1.6
    cam.location=focus+direction*7
    cam.rotation_euler=(focus-cam.location).to_track_quat("-Z","Y").to_euler()
    for tag,target in (("M_BASE",m),("NEW_V",obj)):
        for item in (s,a,m,obj):item.hide_render=(item!=target)
        scene.render.filepath=str(REVIEW/f"REAL_QEM_{PANEL}_{tag}_{name}_CLOSE.png")
        bpy.ops.render.render(write_still=True)
for x in (s,a,m):x.hide_render=True
obj.hide_render=False
obj.name="S_QEM_V_"+PANEL+"_TRUE_RETOPOLOGY_TRIAL"
bpy.ops.wm.save_as_mainfile(
 filepath=str(OUT/("S-QEM-real-"+PANEL+"-collar-retopo-V-TRIAL.blend")),compress=True)
print("V_FINAL_ACTUAL_QEM",PANEL,report["technical_gate"],
      "before",report["previous_single_Q_nonshared_tail_intersections"],
      "new",finalqa["self_intersections"],"tested",len(rows))
