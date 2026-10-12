"""EvoWild S / H0b experimental INTEGRATED SHOULDER SURFACE sculpt.

Inputs: exact accepted S original PNG and frozen original Hunyuan 3-view
BLEND (not H0 REJECT). Never import H0 external shell/pads.
Sculpt existing real Hunyuan single connected skin mesh using editable local
shape key, piecewise planes + narrow shoulder and chest grooves. Assign plate
faces on *that same mesh*. No new mesh, proxies, pasted or floating armor.
Compare actual unaltered BASE vs H0b from exactly same real Blender camera.
Visual approval is NOT inferred from geometry metrics. H1 explicitly blocked.
"""
import bpy,math,json,hashlib
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'art/s-creature/references/00_s_type_modeling_image_v1.png').is_file())
EXP=ROOT/'art/s-creature/experiments/canonical-cleanroom-fullbody-20261011'
SRC=EXP/'hunyuan2mv-original-source-20261012/HUNYUAN2MV_S_THREEVIEW_REAL_ASSET_UNAPPROVED.blend'
REF=ROOT/'art/s-creature/references/00_s_type_modeling_image_v1.png'
OUT=EXP/'h0b-integrated-shoulder-20261012'
REV=OUT/'review';REV.mkdir(parents=True,exist_ok=True)
SRC_SHA='6651109695536db026d9b52fe10c3fa829cab82915cda1955a5f56eedcec4345'
REF_SHA='93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6'
assert hashlib.sha256(REF.read_bytes()).hexdigest()==REF_SHA
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==SRC_SHA
assert REF.stat().st_size==1982782
bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene=bpy.context.scene
bodies=[o for o in scene.objects if o.type=='MESH']
assert len(bodies)==1 and len(bodies[0].data.vertices)==38802
body=bodies[0];body.name='S_H0b_Original_Hunyuan_SINGLE_INTEGRATED_SURFACE'
me=body.data
assert len(me.polygons)==77684
source=np.asarray([list(body.matrix_world@v.co) for v in me.vertices],dtype=np.float64)
origin_hash=hashlib.sha256(source.tobytes()).hexdigest()
x=source[:,0];y=source[:,1];z=source[:,2]
# Model is narrow: X world centered at -0.0355. All anatomical
# Y/Z ROI located by actual H0 source and unchanged shoulder photo.
cx=-.0355
assert np.isfinite(source).all()
side_distance=np.abs(x-cx)
assert source[:,1].min()<-.6 and source[:,1].max()>.495
POLYS={
 'SHOULDER_MAIN':[(-.502,-.092),(-.528,.030),(-.461,.127),
                 (-.377,.189),(-.281,.174),(-.245,.100),
                 (-.299,-.030),(-.390,-.132)],
 'SHOULDER_CREST':[(-.378,.143),(-.306,.208),(-.201,.205),
                    (-.170,.156),(-.252,.111)],
 'THORAX_PLANE':[(-.305,.047),(-.222,.096),(-.117,.130),
                 (-.038,.079),(-.082,-.023),(-.206,-.078)],
}
# These are experimental anatomical surface-region outlines, NOT copied
# pixels or an approved creative reinterpretation. The original PNG
# remains the only judge of actual correct plate directions.
def poly_mask_and_distance(ys,zs,polygon):
    inside=np.zeros(len(ys),dtype=bool)
    minimum=np.full(len(ys),1e9,dtype=np.float64)
    for i,(u,v) in enumerate(polygon):
        p,q=polygon[(i+1)%len(polygon)]
        vx=p-u;vy=q-v
        h=np.clip(((ys-u)*vx+(zs-v)*vy)/(vx*vx+vy*vy+1e-20),0,1)
        length=np.sqrt((ys-u-h*vx)**2+(zs-v-h*vy)**2)
        minimum=np.minimum(minimum,length)
        inside^=((v>zs)!=(q>zs))&(ys<((p-u)*(zs-v)/(q-v+1e-15)+u))
    return inside,np.where(inside,minimum,-minimum)
def smoothstep(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
def make_fields(ys,zs):
    vals={}
    for key,poly in POLYS.items():
        vals[key]=poly_mask_and_distance(ys,zs,poly)
    return vals
vf=make_fields(y,z)
face_xyz=np.asarray([source[list(poly.vertices)].mean(axis=0) for poly in me.polygons])
ff=make_fields(face_xyz[:,1],face_xyz[:,2])
mat_labels={'BASE':0,'SHOULDER_MAIN':1,'SHOULDER_CREST':2,'THORAX_PLANE':3}
materials=[]
def mat(name,color):
    item=bpy.data.materials.new(name);item.diffuse_color=(*color,1.)
    item.use_nodes=True
    p=item.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1.0)
    p.inputs['Roughness'].default_value=.74
    return item
materials.append(mat('H0b_Neutral_source_body',(.22,.26,.32)))
materials.append(mat('H0b_Pearl_shoulders_ON_SAME_MESH',(.87,.89,.91)))
materials.append(mat('H0b_Cool_cream_crest_ON_SAME_MESH',(.71,.75,.83)))
materials.append(mat('H0b_Chest_edge_slate_ON_SAME_MESH',(.39,.46,.60)))
me.materials.clear()
for mm in materials:me.materials.append(mm)
# Assign same original faces; no overlays. Armor material is a property of
# contiguous body triangles and must not be counted as a new armor mesh.
face_materials=np.zeros(len(me.polygons),dtype=np.int32)
for name in ('THORAX_PLANE','SHOULDER_MAIN','SHOULDER_CREST'):
    inside,dist=ff[name]
    selected=inside & (np.abs(face_xyz[:,0]-cx)>.105)
    face_materials[selected]=mat_labels[name]
assert np.count_nonzero(face_materials)>250
for i,face in enumerate(me.polygons):
    face.material_index=int(face_materials[i])
    face.use_smooth=True
assert len([o for o in scene.objects if o.type=='MESH'])==1
bpy.context.view_layer.update()
basis=body.shape_key_add(name='BASIS_SOURCE_HUNYUAN_UNCHANGED')
sculpt=body.shape_key_add(name='H0b_INTEGRATED_SHOULDER_AND_CHEST_ONLY')
dxyz=np.zeros_like(source)
# Side-to-side real surface displacement. Region's INNER contour yields a
# FLATTENED plate relief with a relatively abrupt visible ridge near roots.
# Edge grooves are NEGATIVE relief on the original skin; no disconnected
# armor objects can float or intersect the torso.
half=side_distance/(side_distance+.06)
lateral_gate=smoothstep((side_distance-.080)/.095)
body_gate=smoothstep((z+.19)/.085)
for name,peak,bulge,rootgroove in [
    ('SHOULDER_MAIN',.0205,.0025,.0035),
    ('SHOULDER_CREST',.0135,.0010,.0028),
    ('THORAX_PLANE',.0095,.0025,.0022)]:
    inside,sd=vf[name]
    # A narrow ridge leading into a broad nearly planar shoulder surface:
    # profile is broad-flat, unlike an ellipsoid with a raised center.
    interior=smoothstep(sd/.020)
    lip=np.exp(-.5*(sd/.010)**2)
    piece=(peak*interior + bulge*interior*np.tanh((y+.36)*8.5)
          -rootgroove*lip)
    piece*=lateral_gate*body_gate
    if name=='SHOULDER_MAIN':
        # Broad swept shoulder plane that tapers down into the chest,
        # not a spherical lump. The additive Z crease forms directional
        # blade silhouette rather than a glued-on petal.
        dxyz[:,2]+= .006*interior*lateral_gate*body_gate*smoothstep((z-.015)/.11)
    dxyz[:,0]+=np.sign(x-cx)*piece
# Gentle integrated anterior chest underside tuck (also native mesh).
front_chest=np.exp(-((y+.452)/.098)**4)*np.exp(-((z+.072)/.135)**4)
front_chest*=smoothstep((side_distance-.025)/.075)
dxyz[:,1]-=.007*front_chest
# No changes to hips, legs, head, horn, tail: lock by strict ROI, even where
# the proposed fields' mathematical support would otherwise leak.
allow=(y>-.588)&(y<-.015)&(z>-.185)&(z<.245)
dxyz*=allow[:,None]
assert np.count_nonzero(np.linalg.norm(dxyz,axis=1)>1e-7)>350
inverse_rotation=body.matrix_world.inverted().to_3x3()
for i,v in enumerate(me.vertices):
    local=inverse_rotation@Vector(tuple(dxyz[i]))
    sculpt.data[i].co=v.co+local
sculpt.value=1.0
bpy.context.view_layer.update()
def evaluated_xyz():
    ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=ob.to_mesh()
    try:return np.asarray([list(ob.matrix_world@v.co) for v in mesh.vertices],dtype=np.float64)
    finally:ob.to_mesh_clear()
candidate=evaluated_xyz()
changed=np.linalg.norm(candidate-source,axis=1)
tri=np.asarray([list(p.vertices) for p in me.polygons],dtype=np.int32)
def area_n(p):
    f=p[tri];n=np.cross(f[:,1]-f[:,0],f[:,2]-f[:,0])
    a=np.linalg.norm(n,axis=1);return n,a
norm0,area0=area_n(source)
norm1,area1=area_n(candidate)
area_ratio=area1/np.maximum(area0,1e-12)
quality={
 "faces_normal_flipped":int(np.count_nonzero(np.sum(norm0*norm1,axis=1)<0)),
 "faces_degenerate":int(np.count_nonzero(area1<1e-10)),
 "faces_area_below_half_source":int(np.count_nonzero(area_ratio<.5)),
 "faces_area_above_twice_source":int(np.count_nonzero(area_ratio>2)),
 "max_face_area_ratio":float(np.max(area_ratio)),
 "min_face_area_ratio":float(np.min(area_ratio)),
}
assert not quality["faces_normal_flipped"] and not quality["faces_degenerate"],quality
# Count self-BVH intersections confined shoulder+chest, ignore adjacency.
idx=np.flatnonzero((face_xyz[:,1]>-.60)&(face_xyz[:,1]<.0)&
                    (face_xyz[:,2]>-.19)&(face_xyz[:,2]<.26))
local_faces=[tuple(map(int,tri[i])) for i in idx]
def intersections(points):
    tree=BVHTree.FromPolygons([Vector(v) for v in points],
           local_faces,all_triangles=True,epsilon=1e-7)
    pairs=set()
    for i,j in tree.overlap(tree):
        if i>=j:continue
        if set(local_faces[i])&set(local_faces[j]):continue
        pairs.add((int(idx[i]),int(idx[j])))
    return pairs
base_pairs=intersections(source);new_pairs=intersections(candidate)
technical_pass=(
   not quality["faces_normal_flipped"] and not quality["faces_degenerate"]
   and quality["faces_area_below_half_source"]==0
   and quality["faces_area_above_twice_source"]==0
   and len(new_pairs-base_pairs)==0
)
preserved=(len(me.vertices)==38802 and len(me.polygons)==77684
  and np.max(changed[~allow])<1e-6)
assert preserved,("modified non-shoulder source geometry!",np.max(changed[~allow]))
scene['H0b_morphology_review']='PENDING_VISUAL_REVIEW'
scene['H0b_reference_SHA256']=REF_SHA
scene['H0b_source_BLENDER_SHA256']=SRC_SHA
scene['H0b_current_status']='UNAPPROVED_FOR_GAME'
scene['H0b_gait_H1_allowed']=False
scene['H0b_integrated_body_mesh_count']=1
scene['H0b_no_added_mesh_armor']=True
report={
 "original_S_modeling_png_SHA256":REF_SHA,
 "original_Hunyuan_blend_SHA256":SRC_SHA,
 "original_Hunyuan_geometry_SHA256":origin_hash,
 "actual_Hunyuan_mesh_retained":True,
 "original_Hunyuan_vertices":38802,"original_Hunyuan_triangles":77684,
 "edited_physical_mesh_objects":1,"additional_mesh_armor_objects":0,
 "material_plate_faces_NATIVE_SAME_BODY_MESH":int(np.count_nonzero(face_materials)),
 "native_body_edit_moved_vertices":int(np.count_nonzero(changed>1e-6)),
 "native_body_edit_max_world_displacement":float(np.max(changed)),
 "only_shoulder_chest_modified":True,
 "hips_limbs_head_crest_tail_unchanged":bool(np.max(changed[~allow])<1e-6),
 "quality":quality,
 "source_shoulder_ROI_intersections":len(base_pairs),
 "candidate_shoulder_ROI_intersections":len(new_pairs),
 "new_shoulder_ROI_intersections":len(new_pairs-base_pairs),
 "technical_mesh_gate":"PASS_LIMITED" if technical_pass else "FAIL",
 "original_visual_S_similarity_review":"NOT_YET_ACCEPTED",
 "rejected_H0_external_shells_imported":False,
 "accepted_as_new_H0_base":False,
 "game_morphology_approved":False,
 "next_H1_leg_pass_permitted":False,
 "main_modified":False
}
(OUT/'H0b_REAL_NATIVE_SURFACE_QA.json').write_text(json.dumps(report,indent=2)+'\n')
# Actual same-scene, same-camera renders for full source vs modified.
cam=scene.camera
assert cam and cam.type=='CAMERA'
cam.data.type='ORTHO'
cam.data.ortho_scale=2.16
center=Vector((-.0355,.035,-.0354))
scene.render.engine='BLENDER_WORKBENCH'
sh=scene.display.shading
sh.light='STUDIO'
sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True
sh.background_type='WORLD'
if scene.world is None:scene.world=bpy.data.worlds.new('H0b_Review')
scene.world.color=(.38,.38,.38)
scene.render.resolution_x=1440
scene.render.resolution_y=1080
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
views={'SIDE':(1,0,0),'FRONT':(0,-1,0),'FRONT34':(1,-1,0),
       'REAR34':(1,1,0),'BACK':(0,1,0)}
for mode in ('MATERIAL','SINGLE'):
    sh.color_type=mode
    sh.single_color=(.55,.55,.55)
    for variant in ('BASE','H0b'):
        sculpt.value=0.0 if variant=='BASE' else 1.0
        for j,poly in enumerate(me.polygons):
            poly.material_index=0 if variant=='BASE' else int(face_materials[j])
        bpy.context.view_layer.update()
        for view,d in views.items():
            cam.location=center+Vector(d).normalized()*5
            cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
            suffix='_CLAY' if mode=='SINGLE' else ''
            scene.render.filepath=str(REV/f'{variant}_{view}{suffix}.png')
            bpy.ops.render.render(write_still=True)
# Saved model must open as revised single integrated mesh in Blender.
sculpt.value=1.0
for j,poly in enumerate(me.polygons):poly.material_index=int(face_materials[j])
scene.display.shading.color_type='MATERIAL'
cam.location=center+Vector(views['FRONT34']).normalized()*5
cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(REV/'H0b_FRONT34.png')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'S_H0b_original_Hunyuan_integrated_shoulder_TRIAL.blend'),compress=True)
print('H0b_REAL_INTEGRATED_SHOULDER_DONE',json.dumps(report))
