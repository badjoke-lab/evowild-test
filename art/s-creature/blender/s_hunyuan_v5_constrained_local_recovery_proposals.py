"""Read-only proposal search for V5 locally recovering compressed V4 shoulder faces.

Uses true Blender 4.3.2 meshes (V3 and V4), computes discrete mesh-neighborhood
interpolations, rejects geometry regressions BEFORE anyone touches the live GUI.
NO blend save, NO live edits, NO automatic art KEEP.
"""
import bpy, json, hashlib
from collections import deque
from pathlib import Path
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
STATION=ROOT/"art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012"
V3=STATION/"review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend"
V4=STATION/"review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend"
REF=ROOT/"art/s-creature/references/00_s_type_modeling_image_v1.png"
OUT=STATION/"review-v5-proposals"
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p) for p in (V3,V4,REF)}
assert protected[str(V3.relative_to(ROOT))]=="820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec"
assert protected[str(V4.relative_to(ROOT))]=="38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e"
assert protected[str(REF.relative_to(ROOT))]=="93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6"
assert bpy.app.version[:3]==(4,3,2),bpy.app.version_string
bpy.ops.wm.open_mainfile(filepath=str(V4))
obj=bpy.data.objects["S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4"]
mesh=obj.data
v4=np.array([tuple(v.co) for v in mesh.vertices],dtype=np.float32)
faces=np.array([tuple(p.vertices) for p in mesh.polygons],dtype=np.int32)
edges=np.array([tuple(e.vertices) for e in mesh.edges],dtype=np.int32)
with bpy.data.libraries.load(str(V3),link=False) as (s,t):
    assert "geometry_0" in s.meshes
    t.meshes=["geometry_0"]
m3=t.meshes[0]
v3=np.array([tuple(v.co) for v in m3.vertices],dtype=np.float32)
f3=np.array([tuple(p.vertices) for p in m3.polygons],dtype=np.int32)
assert (len(v4),len(faces))==(38802,77684)
assert np.array_equal(faces,f3)
bpy.data.meshes.remove(m3)
world=np.array([(obj.matrix_world@Vector(c))[:] for c in v4],dtype=np.float64)
centers=(world[faces[:,0]]+world[faces[:,1]]+world[faces[:,2]])/3
scope=(centers[:,1]>-.59)&(centers[:,1]<-.045)&(centers[:,2]>-.4)&(centers[:,2]<.25)
vertex_allowed=(world[:,1]>-.615)&(world[:,1]<-.025)&(world[:,2]>-.42)&(world[:,2]<.27)

def face_geometry(x):
    arr=x.astype(np.float64)
    cross=np.cross(arr[faces[:,1]]-arr[faces[:,0]],arr[faces[:,2]]-arr[faces[:,0]])
    return cross,np.linalg.norm(cross,axis=1)
n3,a3=face_geometry(v3)
n4,a4=face_geometry(v4)
valid=(a3>1e-12)&(a4>1e-12)
ratio4=np.ones(len(faces),dtype=float)
ratio4[valid]=a4[valid]/a3[valid]
baseline_severe=int(np.count_nonzero(valid&scope&(ratio4<.45)))
baseline_min=float(ratio4[valid].min())
assert baseline_severe==40,(baseline_severe,baseline_min)
assert abs(baseline_min-0.2506820839971658)<.0001,baseline_min

seed_faces=np.where(valid&scope&(ratio4<.45)&(a3>2e-8))[0]
# Force inclusion of the documented bilateral high-impact clusters.
for i in (65666,65664,12157,12159):
    assert i in seed_faces,i
seeds=set(int(v) for v in faces[seed_faces].ravel())
neighbor=[set() for _ in range(len(v4))]
for a,b in edges:
    a=int(a);b=int(b)
    neighbor[a].add(b);neighbor[b].add(a)
dist=np.full(len(v4),-1,dtype=np.int32)
queue=deque()
for i in seeds:
    dist[i]=0;queue.append(i)
while queue:
    u=queue.popleft()
    if dist[u]>=9:continue
    for v in neighbor[u]:
        if dist[v]<0:
            dist[v]=dist[u]+1
            queue.append(v)
results=[]
winning=None

for rings in (2,3,4,5,6,7,8):
    # Only the actual topology-adjacent region; no arbitrary 3D radial bulbs.
    weight=np.zeros(len(v4),dtype=np.float64)
    supported=(dist>=0)&(dist<=rings)&vertex_allowed
    weight[supported]=((rings+1-dist[supported])/(rings+1))**2
    for alpha in (.08,.12,.18,.25,.32,.4,.5,.6,.7):
        after=(v4.astype(np.float64)+(v3-v4)*weight[:,None]*alpha).astype(np.float32)
        changed=np.any(after!=v4,axis=1)
        move=np.linalg.norm(after.astype(np.float64)-v4,axis=1)
        maxmove=float(move.max())
        if maxmove>.016:continue
        n,a=face_geometry(after)
        goodvalid=valid&(a>1e-12)
        baddeg=int(np.count_nonzero(valid&(a<=1e-12)))
        flipped=int(np.count_nonzero(goodvalid&((np.sum(n*n4,axis=1)<=0)|(np.sum(n*n3,axis=1)<=0))))
        ratio=np.ones(len(faces),dtype=float);ratio[goodvalid]=a[goodvalid]/a3[goodvalid]
        minratio=float(ratio[goodvalid].min())
        count45=int(np.count_nonzero(goodvalid&scope&(ratio<.45)))
        normal=np.clip(np.sum(n*n3,axis=1)/(np.maximum(a*a3,1e-30)),-1,1)
        count25=int(np.count_nonzero(goodvalid&scope&(normal<np.cos(np.deg2rad(25)))))
        changed_outside=int(np.count_nonzero(changed&~vertex_allowed))
        ok=(baddeg==0 and flipped==0 and minratio>=baseline_min-1e-6
            and count45<baseline_severe and changed_outside==0
            and np.count_nonzero(changed)>15)
        rec=dict(rings=rings,alpha=alpha,minimum_ratio=minratio,
                 severe_faces_lt_045=count45,remaining_severe_delta=count45-baseline_severe,
                 shoulder_normal_turn_gt25=count25,new_degenerate=baddeg,
                 face_orientation_conflicts=flipped,
                 moved_vertices=int(np.count_nonzero(changed)),
                 outside_vertex_roi_moved=changed_outside,
                 max_move=maxmove,geometry_gate="PASS" if ok else "REJECT")
        results.append(rec)
        if ok:
            # Priority: recover more badly compressed faces, improve weakest,
            # minimize disturbance and avoid full V3 reversion.
            score=(baseline_severe-count45)*5+(minratio-baseline_min)*40-maxmove*120
            if winning is None or score>winning[0]:
                winning=(score,rec,after,changed)
assert {str(p.relative_to(ROOT)):sha(p) for p in (V3,V4,REF)}==protected
summary=dict(result="NO_SCULPT_DONE_READONLY_PROPOSAL_SEARCH",blender_version=bpy.app.version_string,
             original_v4_hash=protected[str(V4.relative_to(ROOT))],protected_sha256=protected,
             global_min_v4=baseline_min,severe_face_count_v4=baseline_severe,
             material_severe_face_seeds=len(seed_faces),targeted_seed_vertices=len(seeds),
             candidates_tested=len(results),safe_candidates=sum(x["geometry_gate"]=="PASS" for x in results),
             trial_summary=results,
             caveat="Only geometry feasibility. Candidate must be visualized in live Blender MCP and rejected if shape is worse; no KEEP, no final V5.")
if winning:
    _,best,coords,changed=winning
    summary["best_candidate"]=best
    assert best["geometry_gate"]=="PASS"
    np.savez_compressed(OUT/"V5_RECOVERY_GEOMETRIC_PROPOSAL.npz",
                        indices=np.where(changed)[0].astype(np.int32),
                        coordinates=coords[changed],original_v4_coordinates=v4[changed],
                        original_v3_coordinates=v3[changed])
    summary["candidate_npz"]="V5_RECOVERY_GEOMETRIC_PROPOSAL.npz"
else:
    summary["best_candidate"]=None
    summary["failure"]="All trials worsened another face or failed topology gate. Need more deliberate manual vertex repositioning in Blender MCP."
(OUT/"V5_LOCAL_RECOVERY_CANDIDATE_SEARCH.json").write_text(json.dumps(summary,indent=2)+"\n")
print("V5_CONSTRAINED_PROPOSAL_SEARCH_DONE",json.dumps({k:v for k,v in summary.items() if k!="trial_summary"}),flush=True)
