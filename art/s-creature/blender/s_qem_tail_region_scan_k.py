"""Locate a SINGLE open tail root for original-QEM core rebuild.
No generation; inspect actual original mesh polygon connected components and
boundary loops before committing to real topology replacement.
"""
import bpy,bmesh,numpy as np,json,hashlib
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments/qem-deformation-gate-20261010/tail-core-rebuild-k-v1"
OUT.mkdir(parents=True,exist_ok=True)
ref=ROOT/"references/00_s_type_modeling_image_v1.png"
donor=ROOT/"experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb"
assert hashlib.sha256(ref.read_bytes()).hexdigest()=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert hashlib.sha256(donor.read_bytes()).hexdigest()=="e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f"
s=bpy.data.objects["QEM_IMMUTABLE_DONOR"]
assert len(s.data.vertices)==29948 and len(s.data.polygons)==59932
bm=bmesh.new()
bm.from_mesh(s.data)
bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();bm.edges.ensure_lookup_table()
matrix=s.matrix_world.copy()
centroids=np.array([[v.x,v.y,v.z] for v in
  (matrix@(sum((vert.co for vert in f.verts),Vector())/len(f.verts)) for f in bm.faces)])
faces=list(bm.faces)
def islands(S):
    remaining=set(S)
    comps=[]
    while remaining:
        q=remaining.pop();group={q};stack=[q]
        while stack:
            f=stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if g in remaining:
                        remaining.remove(g);group.add(g);stack.append(g)
        comps.append(group)
    return sorted(comps,key=len,reverse=True)
def boundary(group):
    s=set(group)
    edges=[e for f in s for e in f.edges if sum(ff in s for ff in e.link_faces)==1]
    unique=list(set(edges))
    vmap={}
    for e in unique:
        a,b=e.verts
        vmap.setdefault(a,[]).append(b)
        vmap.setdefault(b,[]).append(a)
    valence={len(x):sum(len(z)==len(x) for z in vmap.values()) for x in vmap.values()}
    remaining=set(vmap)
    loops=[]
    while remaining:
        first=remaining.pop()
        group={first}
        stack=[first]
        while stack:
            v=stack.pop()
            for nxt in vmap[v]:
                if nxt in remaining:
                    remaining.remove(nxt);group.add(nxt);stack.append(nxt)
        loops.append(group)
    return unique,loops,sorted(set(len(n) for n in vmap.values()))
records=[]
for y_cut in (1.50,1.58,1.64,1.70,1.76,1.82,1.88,1.94):
    for z_floor in (1.12,1.22,1.32,1.42):
        for x_max in (.30,.42):
            selected=[faces[i] for i,v in enumerate(centroids)
                       if v[1]>y_cut and v[2]>z_floor and abs(v[0])<x_max]
            comps=islands(selected)
            if not comps:continue
            groups=sorted(comps,key=lambda gg:max(centroids[f.index,1] for f in gg),reverse=True)
            # Tipmost connected candidate is the actual posterior tail portion.
            component=groups[0]
            ids=[f.index for f in component]
            c=centroids[ids]
            edge,loops,valence=boundary(component)
            lv=[matrix@v.co for v in (loops[0] if loops else [])]
            loop_bounds={"ymin":min(v.y for v in lv),"ymax":max(v.y for v in lv),
                         "zmin":min(v.z for v in lv),"zmax":max(v.z for v in lv),
                         "xmin":min(v.x for v in lv),"xmax":max(v.x for v in lv)} if lv else {}
            row={"y_cut":y_cut,"z_floor":z_floor,"xmax":x_max,
                 "all_candidate_components":len(comps),
                 "tip_component_faces":len(component),
                 "tip_max_y":float(c[:,1].max()),
                 "tip_min_y":float(c[:,1].min()),
                 "tip_max_z":float(c[:,2].max()),
                 "tip_min_z":float(c[:,2].min()),
                 "boundary_edges":len(edge),
                 "boundary_loops":len(loops),
                 "loop_lengths":sorted([len(l) for l in loops],reverse=True)[:12],
                 "boundary_valences":valence,
                 "first_loop_bounds":loop_bounds,
                 "one_closed_seam":len(loops)==1 and valence==[2],
                 "all_tip_vertex_indices_near_boundary":sorted(v.index for v in loops[0])[:10] if loops else []}
            records.append(row)
            if row["one_closed_seam"]:
                print("POTENTIAL_SINGLE_SEAM",json.dumps(row))
records.sort(key=lambda r:(not r["one_closed_seam"],
                           -r["tip_component_faces"],
                           abs(r["y_cut"]-1.65)))
report={"authority_sha":"93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6",
"original_donor_sha":"e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f",
"original_vertices":len(s.data.vertices),"original_triangles":len(s.data.polygons),
"candidate_count":len(records),
"top_candidates":records[:30],
"all_candidates":records,
"any_clean_single_root_seam":any(x["one_closed_seam"] for x in records),
"source_unchanged":True,
"asset_approved":False,
"build_criteria":"Locate a SINGLE loop connected to original tail before replacing core."}
(OUT/"REAL_QEM_TAIL_BASE_SECTION_SCAN.json").write_text(json.dumps(report,indent=2)+"\n")
print("TAIL_REGION_SCAN",json.dumps({"count":len(records),
"single_seams":sum(x["one_closed_seam"] for x in records),
"top":records[:5]},indent=2))
bm.free()
