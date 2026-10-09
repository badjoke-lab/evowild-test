"""Read-only source-verified QEM leg-zone scout; NOT an approved rig."""
from pathlib import Path
import bpy, hashlib, json, statistics
from mathutils import Vector, Matrix

BASE=Path(__file__).resolve().parents[1]
PATH=BASE/'experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb'
OUT=BASE/'experiments/qem-deformation-feasibility-20261010/gate0-landmark-survey'
EXPECTED='e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f'
AUTH=BASE/'references/00_s_type_modeling_image_v1.png'
AUTH_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert hashlib.sha256(PATH.read_bytes()).hexdigest()==EXPECTED,'QEM donor hash mismatch'
assert hashlib.sha256(AUTH.read_bytes()).hexdigest()==AUTH_SHA,'S authority hash mismatch'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(PATH))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(meshes)==1, f'Expected one mesh, got {len(meshes)}'
obj=meshes[0]
points=[obj.matrix_world@v.co for v in obj.data.vertices]
lo=Vector([min(v[i] for v in points) for i in range(3)])
hi=Vector([max(v[i] for v in points) for i in range(3)])
span=hi-lo
assert span.y>span.x*2 and span.z>span.x*1.5,'Unexpected donor axes'
scale=2.55/span.z
transform=Matrix.Translation(Vector((-(lo.x+hi.x)*scale/2, -(lo.y+hi.y)*scale/2, -lo.z*scale)))@Matrix.Scale(scale,4)
obj.matrix_world=transform@obj.matrix_world
bpy.context.view_layer.update()
points=[obj.matrix_world@v.co for v in obj.data.vertices]
min_z=min(p.z for p in points);max_z=max(p.z for p in points)
mid_y=statistics.median(p.y for p in points)
min_y,max_y=min(p.y for p in points),max(p.y for p in points)
landmarks=[]
colors=[(.82,.18,.15,1),(.17,.39,.85,1),(.88,.58,.12,1),(.29,.70,.45,1)]
for fore,side,name in [(True,True,'FORE_L'),(True,False,'FORE_R'),(False,True,'HIND_L'),(False,False,'HIND_R')]:
    partition=[p for p in points if (p.y<mid_y)==fore and (p.x>=0)==side]
    ground=[p for p in partition if p.z<min_z+.28*(max_z-min_z)]
    if len(ground)<15:
        landmarks.append({'label':name,'status':'UNRESOLVED','low_z_count':len(ground)});continue
    sorted_ground=sorted(ground,key=lambda p:p.z)
    foot_set=sorted_ground[:max(15,len(sorted_ground)//7)]
    foot=Vector((statistics.median(p.x for p in foot_set),statistics.median(p.y for p in foot_set),statistics.median(p.z for p in foot_set)))
    near_y=[p for p in partition if abs(p.y-foot.y)<.36 and p.z>min_z+.25*(max_z-min_z) and p.z<min_z+.72*(max_z-min_z)]
    middle=None
    if len(near_y)>=15:
        middle=Vector((statistics.median(p.x for p in near_y),statistics.median(p.y for p in near_y),statistics.median(p.z for p in near_y)))
    landmarks.append({'label':name,'status':'CANDIDATE_REGION_UNVERIFIED','foot_xyz':list(foot),'middle_xyz':list(middle) if middle else None,'low_z_count':len(ground),'middle_surface_count':len(near_y),'warning':'surface samples are not approved knee/elbow/hock locations'})
    for kind,loc,radius in [('foot',foot,.055),('middle',middle,.065)]:
        if loc is None:continue
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=radius,location=loc)
        marker=bpy.context.object;marker.name=f'UNVERIFIED_{name}_{kind}'
        m=bpy.data.materials.new(f'UNVERIFIED_{name}_{kind}_mat');m.diffuse_color=colors[len(landmarks)-1]
        marker.data.materials.append(m)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.render.resolution_x=960;scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(.05,.055,.06)
mat=bpy.data.materials.new('QEM_ORIGINAL_GREY_UNCHANGED');mat.diffuse_color=(.73,.77,.80,1)
obj.data.materials.clear();obj.data.materials.append(mat)
cam_data=bpy.data.cameras.new('QEM_SAME_CAMERA_JOINT_REGIONS')
cam=bpy.data.objects.new('QEM_SAME_CAMERA_JOINT_REGIONS',cam_data)
scene.collection.objects.link(cam);scene.camera=cam
cam_data.type='ORTHO';cam_data.ortho_scale=max(5.25,(max_y-min_y)*1.12)
look=Vector((0,0,1.27))
directions={'side':Vector((1,0,0)),'front':Vector((0,-1,0)),'front34':Vector((1,-1,0)).normalized(),'rear34':Vector((1,1,0)).normalized(),'back':Vector((0,1,0))}
for view,d in directions.items():
    cam.location=look+d*9
    cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/f'S_QEM_joint_zones_{view}.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'S_QEM_joint_survey_UNRIGGED.blend'),compress=True)
result={'authority_sha256':AUTH_SHA,'source_qem_sha256':EXPECTED,'source_mesh_unchanged':True,'vertices':len(obj.data.vertices),'triangles':len(obj.data.polygons),'normalization_height':2.55,'original_span_xyz':list(span),'normalized_bbox_xyz':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]},'fore_vs_hind_split_y':'median surface sample coordinate, NOT anatomy','probe_landmarks':landmarks,'review_views':list(directions),'gate':'JOINT_LANDMARKS_REQUIRE_VISUAL_VALIDATION','full_rig_ready':False,'deformation_proven':False,'morphology_approved':False,'note':'Markers and guide material exist only in review .blend and renders; source GLB is unchanged.'}
(OUT/'QEM_JOINT_SURVEY.json').write_text(json.dumps(result,indent=2)+'\n')
print('QEM_JOINT_SURVEY_DONE',len(landmarks),json.dumps([{'label':x['label'],'status':x['status']} for x in landmarks]))
