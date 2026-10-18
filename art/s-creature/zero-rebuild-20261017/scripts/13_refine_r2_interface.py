"""Revise trial A after real SIDE/FRONT/FRONT34 review.

Reduce excessive crown spread using R1 coordinates; feather only the local
white/graphite material joins on the already welded shoulder surface. This
material interpolation does not replace or mask disconnected geometry.
"""
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'verification/S_ZERO_R2_TRIAL_B.blend'
assert Path(bpy.data.filepath).name=='S_ZERO_R2_TRIAL_A.blend'
assert not OUT.exists()
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
crowns=[f'CROWN_{part}_{side}' for side in ['N','F'] for part in ['MAIN','BLUE','IVORY_RIDGE']]
originals={}
with bpy.data.libraries.load(str(ROOT/'S_ZERO_CANDIDATE_REVISED_R1.blend'),link=False) as (src,dst):
    dst.objects=list(crowns)
for original in dst.objects:
    key=next(n for n in crowns if original.name==n or original.name.startswith(n+'.'))
    originals[key]=[v.co.copy() for v in original.data.vertices]
    bpy.data.objects.remove(original,do_unlink=True)
outline=[(-2.19,2.19),(-1.98,2.43),(-1.65,2.64),(-1.18,2.83),(-.62,3.00),(-.08,3.11),(-.70,2.89),(-1.25,2.67),(-1.69,2.42),(-1.98,2.23)]
for name in crowns:
    ob=bpy.data.objects[name]
    side=-1 if name.endswith('_N') else 1
    for v,old in zip(ob.data.vertices,originals[name]):
        x,y,z=old
        t=max(0,min(1,(z-2.19)/.92))
        hits=[]
        for (x1,z1),(x2,z2) in zip(outline,outline[1:]+outline[:1]):
            if min(z1,z2)<=z<=max(z1,z2) and abs(z2-z1)>1e-6:
                hits.append(x1+(x2-x1)*(z-z1)/(z2-z1))
        lo,hi=(min(hits),max(hits)) if hits else (0,0)
        q=max(0,min(1,(x-lo)/max(.001,hi-lo)))
        envelope=math.sin(math.pi*t)**1.35
        v.co=old
        v.co.y+=side*envelope*(.005+.065*(.5-q))
    ob.data.update()

# Area-weighted colors at the white/graphite interface, interpolated on real
# geometry only. All non-interface faces retain their original material slots.
mesh=body.data
colors=[]
for m in mesh.materials:
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    colors.append(Vector(bs.inputs['Base Color'].default_value[:3]))
vertex_faces=[[] for _ in mesh.vertices]
neighbors=[set() for _ in mesh.vertices]
for p in mesh.polygons:
    for v in p.vertices:vertex_faces[v].append(p)
for e in mesh.edges:
    a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
boundary=set()
for i,faces in enumerate(vertex_faces):
    mats={p.material_index for p in faces}
    if 0 in mats and len(mats)>1:
        boundary.add(i)
support=set(boundary)
for _ in range(3):
    support.update(v for i in list(support) for v in neighbors[i])
vertex_colors=[]
for faces in vertex_faces:
    weights=[max(1e-9,p.area) for p in faces]
    vertex_colors.append(sum((colors[p.material_index]*w for p,w in zip(faces,weights)),Vector())/sum(weights))
for _ in range(3):
    updated=list(vertex_colors)
    for i in support:
        if neighbors[i]:
            avg=sum((vertex_colors[j] for j in neighbors[i]),Vector())/len(neighbors[i])
            updated[i]=vertex_colors[i].lerp(avg,.55)
    vertex_colors=updated
name='R2 local shoulder palette'
attr=mesh.color_attributes.new(name=name,type='FLOAT_COLOR',domain='CORNER')
material=bpy.data.materials.new('S | R2 welded shoulder transition')
material.use_nodes=True
bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Metallic'].default_value=.12
bs.inputs['Roughness'].default_value=.42
node=material.node_tree.nodes.new('ShaderNodeVertexColor')
node.layer_name=name
material.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
mesh.materials.append(material)
slot=len(mesh.materials)-1
changed_faces=[]
for p in mesh.polygons:
    old_color=colors[p.material_index]
    if not any(i in support for i in p.vertices):
        continue
    changed_faces.append(p.index)
    for li in p.loop_indices:
        i=mesh.loops[li].vertex_index
        col=vertex_colors[i] if i in support else old_color
        attr.data[li].color=(*col,1)
    p.material_index=slot
mesh.update()
bpy.context.scene['stage']='R2_TRIAL_B'
bpy.context.scene['candidate_status']='REVISE; narrowed frontal crown and local welded shoulder transition awaiting real review'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
(ROOT/'evidence/REVISION_R2_TRIAL_B.json').write_text(json.dumps({
    'source_trial':'verification/S_ZERO_R2_TRIAL_A.blend','output':str(OUT.relative_to(ROOT)),
    'trial_a_decision':'REVISE: frontal crown too wide; jagged white/graphite join after actual union',
    'crown_adjustment':'R1 original coordinates, delta Y sin(pi*t)^1.35 * (0.005 + 0.065*(0.5-q)); X/Z unchanged',
    'body_geometry_changed_from_trial_a':False,'material_transition_boundary_vertices':len(boundary),
    'material_transition_faces':len(changed_faces),'palette':'Same original pearl/ivory/slate/graphite linear colors',
    'method':'Local per-corner color interpolation on continuous welded shoulder geometry only',
    'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},indent=2)+'\n')
print('TRIAL_B_SAVED',len(changed_faces),'local transition faces')
