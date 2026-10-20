"""Read-only R5/candidate reload, scope and structure verification.
Run in Blender with -- TARGET_RELATIVE_PATH LABEL; never saves a model.
"""
import bpy, bmesh, hashlib, json, struct, sys
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
args=globals().get('ARGS') or sys.argv[sys.argv.index('--')+1:]
TARGET=ROOT/args[0];OUT=ROOT/'evidence'/('VERIFY_R6_'+args[1]+'.json')
SOURCE=ROOT/'S_ZERO_CANDIDATE_REVISED_R5.blend'
assert not OUT.exists() and bpy.app.version==(4,3,2)

def region(p):
    x,y,z=p
    return .18<x<1.34 and 1.10<z<2.10 and not (x>1.07 and z>1.78-.75*(x-1.12))

def mesh_hash(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:
        h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));h.update(struct.pack('<I?',p.material_index,p.use_smooth))
    for r in o.matrix_world:h.update(struct.pack('<4f',*r))
    for a in o.data.color_attributes:
        h.update(a.name.encode())
        for d in a.data:h.update(struct.pack('<4f',*d.color))
    return h.hexdigest()

def tree_nodes(tree):
    if not tree:return None
    result={}
    for n in tree.nodes:
        values={}
        for i in n.inputs:
            if not hasattr(i,'default_value'):continue
            v=i.default_value
            if isinstance(v,(str,float,int,bool)) or v is None:values[i.identifier]=v
            elif hasattr(v,'__len__'):values[i.identifier]=list(v)
        result[n.name]={'type':n.type,'inputs':values}
    return {'nodes':result,'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links)}

def studio():
    r={}
    for o in bpy.data.collections['STUDIO'].objects:
        d={'type':o.type,'matrix':[list(row) for row in o.matrix_world]}
        if o.type=='CAMERA':d.update(projection=o.data.type,scale=o.data.ortho_scale,lens=o.data.lens)
        if o.type=='LIGHT':d.update(color=list(o.data.color),energy=o.data.energy,shape=o.data.shape,size=o.data.size)
        if o.type=='MESH':d['mesh']=mesh_hash(o)
        r[o.name]=d
    s=bpy.context.scene;r['view']=[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma]
    r['world']=tree_nodes(s.world.node_tree)
    return r

def protected_faces(mesh,attrs):
    result=[]
    for p in mesh.polygons:
        coords=tuple(tuple(mesh.vertices[i].co) for i in p.vertices)
        if all(region(c) for c in coords):continue
        colors=tuple((n,tuple(tuple(mesh.color_attributes[n].data[li].color) for li in p.loop_indices)) for n in attrs)
        result.append((coords,p.material_index,p.use_smooth,colors))
    return hashlib.sha256(repr(sorted(result)).encode()).hexdigest(),len(result)

hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE,TARGET]}
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
before={o.name:mesh_hash(o) for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH'}
old_studio=studio();materials={m.name:tree_nodes(m.node_tree) for m in bpy.data.materials}
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];old_coords={tuple(v.co) for v in b.data.vertices if not region(v.co)}
attrs=[a.name for a in b.data.color_attributes];old_faces=protected_faces(b.data,attrs)
bpy.ops.wm.open_mainfile(filepath=str(TARGET),load_ui=False)
after={o.name:mesh_hash(o) for o in bpy.data.collections['S_ZERO_CREATURE'].objects if o.type=='MESH'}
removed=sorted(set(before)-set(after));assert removed==['PELVIS_F','PELVIS_N','SACRAL_MANTLE'],removed
protected=sorted(set(before)-set(removed)-{'S_ZERO_BODY_CONTINUOUS'})
assert all(before[n]==after[n] for n in protected)
assert studio()==old_studio
assert all(tree_nodes(bpy.data.materials[n].node_tree)==v for n,v in materials.items())
b=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'];now_coords={tuple(v.co) for v in b.data.vertices}
assert old_coords.issubset(now_coords)
assert protected_faces(b.data,attrs)==old_faces
assert not any(o.type=='ARMATURE' for o in bpy.data.objects) and not bpy.data.actions
records=[]
for o in bpy.data.collections['S_ZERO_CREATURE'].objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data)
    record={'name':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),
        'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'loose_vertices':sum(not v.link_edges for v in bm.verts),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces)}
    assert all(record[k]==0 for k in ['boundary_edges','nonmanifold_edges','loose_vertices','degenerate_faces']),record
    if o==b:
        seen=set();components=[]
        for v in bm.verts:
            if v in seen:continue
            todo=[v];seen.add(v);count=0
            while todo:
                q=todo.pop();count+=1
                for e in q.link_edges:
                    w=e.other_vert(q)
                    if w not in seen:seen.add(w);todo.append(w)
            components.append(count)
        record['connected_components']=components;assert len(components)==1
        polygons=[set(p.vertices) for p in o.data.polygons]
        tree=BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get())
        pairs=set(tuple(sorted(pair)) for pair in tree.overlap(tree) if pair[0]!=pair[1] and not polygons[pair[0]]&polygons[pair[1]])
        local_pairs=[pair for pair in pairs if any(region(o.data.polygons[i].center) for i in pair)]
        record['whole_body_nonadjacent_BVH_candidates']=len(pairs)
        record['pelvis_nonadjacent_BVH_candidates']=len(local_pairs)
        record['pelvis_candidate_pairs']=sorted(local_pairs)[:80]
        record['local_ngons']=sum(len(p.vertices)>4 and all(region(o.data.vertices[i].co) for i in p.vertices) for p in o.data.polygons)
        record['absolute_volume']=abs(bm.calc_volume(signed=True))
    bm.free();records.append(record)
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name] for p in [SOURCE,TARGET])
report={'source':SOURCE.name,'target':str(TARGET.relative_to(ROOT)),'hashes':hashes,'blender':bpy.app.version_string,
    'protected_meshes':protected,'protected_body_vertices_exact':len(old_coords),'protected_body_faces_exact':old_faces[1],
    'original_materials_unchanged':True,'studio_and_cameras_unchanged':True,'armatures':0,'actions':0,
    'merged_pelvic_objects':removed,'meshes':records,
    'limits':'BVH candidates are conservative; closed one-component topology alone is not proof of animation suitability.'}
OUT.write_text(json.dumps(report,indent=2)+'\n')
print('R6_RELOAD',TARGET.name,'meshes',len(records),'vertices',sum(r['vertices'] for r in records),'faces',sum(r['faces'] for r in records))
print('BODY',next(r for r in records if r['name']==b.name))
