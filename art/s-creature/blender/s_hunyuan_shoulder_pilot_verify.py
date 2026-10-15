"""Real BMesh/BVH checks; this script makes no model changes."""
import bpy,bmesh,json,numpy as np,hashlib
from mathutils.bvhtree import BVHTree
from collections import Counter
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT'];ROOT=pilot['ROOT']

def xyz(mesh):return np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
def points_counter(points):return Counter(tuple(v) for v in points)
def outside(points):
    x,y,z=points.T
    return ~((y>-.66)&(y<-.02)&(z>-.35)&(z<.27)&(np.abs(x+.03588832542300224)>.012))
def geometry(mesh):
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.faces.ensure_lookup_table()
    t=BVHTree.FromBMesh(bm,epsilon=0)
    pairs=[(a,b) for a,b in t.overlap(t) if a<b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)]
    def tri_signature(f):return tuple(sorted(tuple(v.co) for v in f.verts))
    contact_signatures={tuple(sorted((tri_signature(bm.faces[a]),tri_signature(bm.faces[b])))) for a,b in pairs}
    contacts=[{'a':[list(v.co) for v in bm.faces[a].verts],'b':[list(v.co) for v in bm.faces[b].verts]} for a,b in pairs]
    remaining=set(bm.verts);components=0
    while remaining:
        seed=remaining.pop();stack=[seed];components+=1
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                o=e.other_vert(v)
                if o in remaining:remaining.remove(o);stack.append(o)
    winding=sum(len(e.link_loops)==2 and e.link_loops[0].vert==e.link_loops[1].vert for e in bm.edges)
    report={'vertices':len(bm.verts),'edges':len(bm.edges),'triangles':len(bm.faces),'connected_components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'loose_vertices':sum(not v.link_edges for v in bm.verts),'degenerate_triangles_area_lt_1e_minus_12':sum(f.calc_area()<1e-12 for f in bm.faces),'inconsistent_winding_edges':winding,'signed_volume':bm.calc_volume(signed=True),'nonadjacent_bvh_contacts':len(pairs),'contact_coordinates':contacts}
    bm.free();return report,contact_signatures

base=xyz(pilot['baseline']);current=xyz(body.data)
a,contacts0=geometry(pilot['baseline']);b,contacts1=geometry(body.data)
unchanged=points_counter(base[outside(base)])==points_counter(current[outside(current)])
positive=lambda v:v[v[:,0]>-.02388832542300224]
right_unchanged=points_counter(positive(xyz(pilot['right_final'])))==points_counter(positive(current))
protected=json.loads((OUT/'PROTECTED_BEFORE.json').read_text())
hashes_ok=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in protected.items())
region=lambda v:v[(v[:,1]>-.50)&(v[:,1]<-.22)&(v[:,2]>-.12)&(v[:,2]<.14)]
width=lambda v:float(np.quantile(region(v)[:,0],.975)-np.quantile(region(v)[:,0],.025))
report={'baseline':a,'candidate':b,'outside_shoulder_roi_coordinates_exact':unchanged,'right_shoulder_unchanged_by_opposite_side_work':right_unchanged,'new_nonadjacent_bvh_contacts':len(contacts1-contacts0),'resolved_nonadjacent_bvh_contacts':len(contacts0-contacts1),'protected_hashes_unchanged':hashes_ok,'protected_files_checked':len(protected),'frontal_shoulder_width_quantile_baseline':width(base),'frontal_shoulder_width_quantile_candidate':width(current),'topology_changed':True,'blender_version':bpy.app.version_string,'bvh_limit':'BVHTree surface overlap test excluding triangle pairs sharing vertices; not a formal proof of no tangencies/coplanar contacts','global_creature_art_approved':False}
(OUT/'FINAL_GEOMETRY_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
assert unchanged and right_unchanged and hashes_ok
assert b['nonmanifold_edges']==a['nonmanifold_edges']==0
assert b['connected_components']==a['connected_components']
assert b['inconsistent_winding_edges']==0
assert b['degenerate_triangles_area_lt_1e_minus_12']==a['degenerate_triangles_area_lt_1e_minus_12']
assert not contacts1-contacts0
print(json.dumps({k:v for k,v in report.items() if k not in ['baseline','candidate']},indent=2))
print('COUNTS', {k:v for k,v in b.items() if k!='contact_coordinates'})
