"""Analyze actual V4 compressed and rotated faces against actual immutable V3.

Render V4 face-distortion maps without changing or re-saving any source .blend.
The heatmap is a geometric diagnostic, NOT an art-directed V5 sculpt.
"""
import bpy, hashlib, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path.cwd()
STATION=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
V3=STATION/'review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend'
V4=STATION/'review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend'
OUT=STATION/'review-v5-diagnostic'
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
protected={str(p.relative_to(ROOT)):sha(p) for p in (REF,V3,V4)}
expected={
 str(REF.relative_to(ROOT)):'93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6',
 str(V3.relative_to(ROOT)):'820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec',
 str(V4.relative_to(ROOT)):'38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e',
}
assert protected==expected,(protected,expected)
assert bpy.app.version[:3]==(4,3,2),bpy.app.version_string

bpy.ops.wm.open_mainfile(filepath=str(V4))
body=bpy.data.objects['S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4']
mesh=body.data
assert mesh.name=='geometry_0' and len(mesh.vertices)==38802 and len(mesh.polygons)==77684
v4=np.array([v.co[:] for v in mesh.vertices],dtype=np.float64)
faces=np.array([p.vertices[:] for p in mesh.polygons],dtype=np.int32)
with bpy.data.libraries.load(str(V3),link=False) as (source,target):
    assert 'geometry_0' in source.meshes
    target.meshes=['geometry_0']
m3=target.meshes[0]
v3=np.array([v.co[:] for v in m3.vertices],dtype=np.float64)
f3=np.array([p.vertices[:] for p in m3.polygons],dtype=np.int32)
assert np.array_equal(faces,f3) and v3.shape==v4.shape
bpy.data.meshes.remove(m3)

def face_geometry(vertices):
    a=vertices[faces[:,1]]-vertices[faces[:,0]]
    b=vertices[faces[:,2]]-vertices[faces[:,0]]
    cross=np.cross(a,b)
    magnitude=np.linalg.norm(cross,axis=1)
    return cross,magnitude
n3,a3=face_geometry(v3)
n4,a4=face_geometry(v4)
valid=(a3>1e-12)&(a4>1e-12)
ratio=np.ones(len(faces),dtype=float)
ratio[valid]=a4[valid]/a3[valid]
cos=np.ones(len(faces),dtype=float)
cos[valid]=np.clip(np.sum(n3[valid]*n4[valid],axis=1)/(a3[valid]*a4[valid]),-1,1)
turn=np.degrees(np.arccos(cos))
centers=(v4[faces[:,0]]+v4[faces[:,1]]+v4[faces[:,2]])/3
c_world=np.array([(body.matrix_world@Vector(c))[:] for c in centers])
# Broad shoulder compartment is intentionally approximate. Captures compressions.
scope=(c_world[:,1]>-.59)&(c_world[:,1]<-.045)&(c_world[:,2]>-.4)&(c_world[:,2]<.25)
changed=np.linalg.norm(v4-v3,axis=1)
categories=np.zeros(len(faces),dtype=np.int32)
categories[(valid&scope)&(turn>=25)] = 3
categories[(valid&scope)&(ratio<.75)] = 2
categories[(valid&scope)&(ratio<.45)] = 1
# RED means compressed to <45% of V3 area; orange <75%; purple = face rotation >=25 degrees.
def record(i):
    i=int(i)
    return dict(face=i, vertices=faces[i].tolist(),
                world_center_xyz=[float(v) for v in c_world[i]],
                v3_area=float(a3[i]/2),v4_area=float(a4[i]/2),
                area_ratio=float(ratio[i]),normal_change_deg=float(turn[i]),
                max_vertex_move=float(changed[faces[i]].max()),shoulder_scope=bool(scope[i]))
ranked=np.argsort(np.where(valid&scope,ratio,100.0))[:60]
turn_order=np.argsort(np.where(valid&scope,-turn,100.0))[:30]
stats={
 'run_purpose':'Face distortion localization for V5 interactive art-directed sculpt; no geometry edits.',
 'source_v3_sha256':protected[str(V3.relative_to(ROOT))],
 'source_v4_sha256':protected[str(V4.relative_to(ROOT))],
 'reference_sha256':protected[str(REF.relative_to(ROOT))],
 'blender_version':bpy.app.version_string,
 'mesh':'geometry_0','vertices':int(len(v4)),'faces':int(len(faces)),
 'changed_vertices_v3_to_v4':int(np.count_nonzero(changed)),
 'total_faces_shoulder_scope':int(scope.sum()),
 'shoulder_faces_area_ratio_under_0_45':int(np.count_nonzero(valid&scope&(ratio<.45))),
 'shoulder_faces_area_ratio_under_0_6':int(np.count_nonzero(valid&scope&(ratio<.6))),
 'shoulder_faces_normal_turn_over_25deg':int(np.count_nonzero(valid&scope&(turn>=25))),
 'minimum_shoulder_face_area_ratio':float(ratio[valid&scope].min()),
 'minimum_global_area_ratio':float(ratio[valid].min()),
 'top_compressed_shoulder_faces':[record(i) for i in ranked],
 'top_rotated_shoulder_faces':[record(i) for i in turn_order],
 'new_degenerate_faces':int(np.count_nonzero((a3>1e-12)&(a4<=1e-12))),
 'new_flipped_faces':int(np.count_nonzero((np.sum(n3*n4,axis=1)<0)&valid)),
 'heatmap_palette':{'normal':0,'severe_area_compression':1,'moderate_area_compression':2,'normal_turn_over_25deg':3},
 'caution':'A face-area or normal difference is not direct proof of self-intersection, slit, or artistic mismatch.'
}
assert stats['new_degenerate_faces']==0 and stats['new_flipped_faces']==0
(OUT/'V4_COMPRESSED_FACE_DIAGNOSTIC.json').write_text(json.dumps(stats,indent=2)+'\n')

# Render heatmaps on V4 geometry IN MEMORY ONLY; do not save a blend.
scene=bpy.context.scene
for layer in scene.view_layers:
    layer.material_override=None
for ob in scene.objects:
    ob.hide_render=(ob!=body)
body.hide_render=False
for coll in bpy.data.collections:coll.hide_render=False
def show_coll(l):
    l.exclude=False
    for child in l.children:show_coll(child)
for layer in scene.view_layers:show_coll(layer.layer_collection)
colors=[(.31,.34,.39,1),(.83,.06,.06,1),(.96,.48,.07,1),(.49,.18,.84,1)]
materials=[]
for label,color in zip(('NORMAL','SEVERE_COMPRESSED','MODERATE_COMPRESSED','ROTATED'),colors):
    mat=bpy.data.materials.new('V5_DIAGNOSTIC_'+label)
    mat.use_nodes=True
    principled=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    principled.inputs['Base Color'].default_value=color
    principled.inputs['Roughness'].default_value=.78
    materials.append(mat)
mesh.materials.clear()
for mat in materials:mesh.materials.append(mat)
for poly,kind in zip(mesh.polygons,categories):poly.material_index=int(kind)
world=bpy.data.worlds.new('V5_DIAGNOSTIC_WORLD')
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.22,.23,.25,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7
scene.world=world
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=14
scene.render.resolution_x=1200
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.use_compositing=False
scene.render.use_sequencer=False
scene.view_settings.view_transform='Standard'
scene.view_settings.look='Medium High Contrast'
for label,location,power,area in [('KEY',(2,-3,3),480,3),('FILL',(-3,-1,1),150,3)]:
    data=bpy.data.lights.new('V5_DIAG_'+label,'AREA')
    data.energy=power;data.size=area
    obj=bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.location=location
    obj.rotation_euler=(Vector((0,-.2,0))-obj.location).to_track_quat('-Z','Y').to_euler()
for name,xyz in (('SIDE',(1,0,0)),('FRONT',(0,-1,0)),('FRONT34',(1,-1,0))):
    d=Vector(xyz).normalized()
    camd=bpy.data.cameras.new('V5_DIAG_CAMERA_'+name)
    cam=bpy.data.objects.new(camd.name,camd)
    scene.collection.objects.link(cam)
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
    cam.location=Vector((-.035,-.32,-.045))+d*5
    camd.type='ORTHO';camd.ortho_scale=.85
    scene.camera=cam
    scene.render.filepath=str(OUT/('V4_FACE_DISTORTION_'+name+'.png'))
    bpy.ops.render.render(write_still=True)
    assert Path(scene.render.filepath).is_file()
assert {str(p.relative_to(ROOT)):sha(p) for p in (REF,V3,V4)}==protected
print('S_V5_V4_REAL_SURFACE_DIAGNOSTIC_PASS',json.dumps({k:v for k,v in stats.items() if not k.startswith('top_')}),flush=True)
