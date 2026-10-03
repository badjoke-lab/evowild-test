"""Gate B v3: shoulder/chest plane massing only on core thorax rings 8-10."""
import bpy,bmesh,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output')
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT,'S-gateB-v2.blend'))
cage=bpy.data.collections['S_REBUILD_GATE_A']
core=bpy.data.objects['S_rebuild_core_head_crest_neck_torso_tail']
mesh=core.data
assert len(mesh.vertices)==152, len(mesh.vertices)

def digest():
    return hashlib.sha256(b''.join(
        repr(tuple(v.co)).encode()
        for o in sorted(cage.objects,key=lambda o:o.name)
        if o.type=='MESH'
        for v in o.data.vertices
    )).hexdigest()

source_hash=digest()
source_coords={o.name:[tuple(v.co) for v in o.data.vertices] for o in cage.objects if o.type=='MESH'}
source_topology={o.name:[tuple(p.vertices) for p in o.data.polygons] for o in cage.objects if o.type=='MESH'}

# Eight vertices per ring, inherited from the Gate A core loft.
# Only X/Z are changed; Y remains exact.
# k=0/4 lateral, 2 dorsal, 6 ventral, diagonals in between.
def reshape_ring(ring,lateral_scale,diag_scale,dorsal_dz,ventral_dz):
    base=ring*8
    pts=[mesh.vertices[base+k].co.copy() for k in range(8)]
    cx=sum(p.x for p in pts)/8.0
    cz=sum(p.z for p in pts)/8.0
    for k,p in enumerate(pts):
        q=p.copy()
        dx=p.x-cx
        if k in (0,4):
            q.x=cx+dx*lateral_scale
        elif k in (1,3,5,7):
            q.x=cx+dx*diag_scale
        # plane shaping: slightly flatter dorsal cap and lifted ventral chest.
        if k==2:
            q.z += dorsal_dz
        elif k in (1,3):
            q.z += dorsal_dz*0.45
        elif k==6:
            q.z += ventral_dz
        elif k in (5,7):
            q.z += ventral_dz*0.58
        # Preserve longitudinal station exactly.
        q.y=p.y
        mesh.vertices[base+k].co=q

reshape_ring(8,1.03,0.96, 0.006,0.018)
reshape_ring(9,0.98,0.91, 0.004,0.035)
reshape_ring(10,0.97,0.93,0.002,0.018)

mesh.update()
bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()

# Hard locks: all core vertices outside rings 8-10 exact; every non-core mesh exact.
changed=set(range(8*8,11*8))
for i,co in enumerate(source_coords[core.name]):
    if i not in changed:
        assert tuple(mesh.vertices[i].co)==co, f'locked core vertex changed {i}'
for o in cage.objects:
    if o.type!='MESH' or o.name==core.name:
        continue
    assert [tuple(v.co) for v in o.data.vertices]==source_coords[o.name], o.name+' changed'
assert all(
    [tuple(p.vertices) for p in o.data.polygons]==source_topology[o.name]
    for o in cage.objects if o.type=='MESH'
), 'Topology changed'
assert len(bpy.data.materials)==0
assert len(bpy.data.actions)==0
assert not any(o.type=='ARMATURE' for o in bpy.data.objects)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-gateB-v3.blend'),compress=True)
report={
 'gate':'B','pass':'v3','status':'REVIEW_PENDING','source':'S-gateB-v2.blend',
 'scope':'core thorax rings 8-10 only',
 'source_geometry_sha256':source_hash,'geometry_sha256':digest(),
 'changed_core_rings':[8,9,10],
 'all_other_core_vertices_unchanged':True,
 'all_noncore_meshes_unchanged':True,
 'topology_preserved':True,
 'no_materials':True,'no_animation':True,'no_armature':True,
 'changes':[
   'Lifted the ventral anterior thorax locally to strengthen the rise into the accepted waist',
   'Reduced diagonal chest roundness while preserving moderate shoulder width',
   'Kept all longitudinal ring stations unchanged so overall body length and posture stay fixed'
 ],
 'limitations':['Gate B v3 review pending','No production welding/retopology']
}
json.dump(report,open(os.path.join(OUT,'S-gateB-v3.json'),'w'),indent=2)
print('GATE_B_V3_SAVED',json.dumps(report))
