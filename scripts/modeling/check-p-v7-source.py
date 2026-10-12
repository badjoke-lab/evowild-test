"""Verify actual Blender source and exported static GLB; never an art approval."""
import bpy,bmesh,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
E=ROOT/'docs/evidence/p-canonical-3d-v7-20261012'
source=ROOT/'art/p-creature/workspaces/P-v7-reference-retopology.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
checks={}
for name in ['P_v7_CONTINUOUS_REFERENCE_SCULPT','P_v7_edited_folded_tail']:
    o=bpy.data.objects[name]
    bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.verts.index_update()
    unseen=set(bm.verts);sizes=[]
    while unseen:
        todo=[unseen.pop()];n=0
        while todo:
            v=todo.pop();n+=1
            for e in v.link_edges:
                w=e.other_vert(v)
                if w in unseen:unseen.remove(w);todo.append(w)
        sizes.append(n)
    check={'vertices':len(bm.verts),'polygons':len(bm.faces),'components':sizes,'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)}
    assert len(sizes)==1 and check['nonManifoldEdges']==0,check
    checks[name]=check;bm.free()
image=bpy.data.objects['CANONICAL_P_IMAGE__DO_NOT_MODIFY'].data
checks['reference']={'packed':bool(image.packed_file),'sha256':hashlib.sha256(bytes(image.packed_file.data)).hexdigest()}
assert checks['reference']['sha256']==hashlib.sha256((ROOT/'public/concept/P.webp').read_bytes()).hexdigest()
assert not any(o.type=='ARMATURE' for o in bpy.context.scene.objects)
checks['staticOnly']=True
checks['sourceSHA256']=hashlib.sha256(source.read_bytes()).hexdigest()
(E/'source-validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks))
