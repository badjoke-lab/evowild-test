"""Fresh Gate A v5 cage from empty scene. No v4/v12 morphology input."""
import bpy,bmesh,math,os,json,hashlib
from mathutils import Vector

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
cage=bpy.data.collections.new('S_REBUILD_GATE_A'); scene.collection.children.link(cage)
review=bpy.data.collections.new('S_REBUILD_REVIEW'); scene.collection.children.link(review)

verts=[]; faces=[]; smooth=[]
def vertex(p): verts.append(tuple(p)); return len(verts)-1
def face(ids,is_smooth=True): faces.append(tuple(ids)); smooth.append(is_smooth)

# One continuous head-neck-thorax-waist-pelvis-tail cage.
stations=[
 (-1.00,1.255,1.205,.018),(-.92,1.295,1.195,.043),
 (-.82,1.345,1.185,.070),(-.72,1.365,1.180,.086),
 (-.63,1.325,1.125,.080),(-.50,1.255,1.045,.075),
 (-.34,1.195,.970,.084),(-.18,1.170,.885,.104),
 (-.05,1.175,.815,.138),(.12,1.155,.765,.158),
 (.28,1.105,.825,.132),(.44,1.060,.885,.086),
 (.59,1.090,.900,.102),(.72,1.140,.885,.128),
 (.84,1.105,.870,.116),(.96,1.035,.895,.074),
 (1.24,.900,.755,.046),(1.52,.700,.610,.027),
 (1.76,.535,.510,.004)]
rings=[]
for y,top,bottom,width in stations:
    ring=[]
    for k in range(8):
        a=k*math.tau/8
        ring.append(vertex((width*math.cos(a),y,(top+bottom)/2+(top-bottom)/2*math.sin(a))))
    rings.append(ring)
face(tuple(reversed(rings[0])))

# Remove selected dorsal-lateral skull panels and extend them into six narrow rear-swept laminae.
root_specs=[(2,1),(2,0),(3,0),(2,2),(2,3),(3,3)]
root_quads={}
for r in range(len(rings)-1):
    for k in range(8):
        ids=(rings[r][k],rings[r+1][k],rings[r+1][(k+1)%8],rings[r][(k+1)%8])
        if (r,k) in root_specs: root_quads[(r,k)]=ids
        else: face(ids)
face(rings[-1])

crest_defs={
 (1,0):(2,1,[(.050,-.66,1.345,.024,.040),(.058,-.40,1.425,.020,.028),(.064,-.10,1.500,.004,.004)]),
 (1,1):(2,0,[(.070,-.65,1.300,.026,.038),(.075,-.39,1.355,.020,.026),(.079,-.10,1.400,.004,.004)]),
 (1,2):(3,0,[(.081,-.61,1.260,.024,.034),(.084,-.36,1.295,.019,.024),(.086,-.08,1.320,.004,.004)]),
 (-1,0):(2,2,[(.050,-.66,1.345,.024,.040),(.058,-.40,1.425,.020,.028),(.064,-.10,1.500,.004,.004)]),
 (-1,1):(2,3,[(.070,-.65,1.300,.026,.038),(.075,-.39,1.355,.020,.026),(.079,-.10,1.400,.004,.004)]),
 (-1,2):(3,3,[(.081,-.61,1.260,.024,.034),(.084,-.36,1.295,.019,.024),(.086,-.08,1.320,.004,.004)])
}
crest_meta=[]
for (sign,level),(r,k,cross) in crest_defs.items():
    prev=list(root_quads[(r,k)])
    for x,y,z,t,d in cross:
        pts=[(sign*(x-t),y,z+d),(sign*(x+t),y,z+d),(sign*(x+t),y,z-d),(sign*(x-t),y,z-d)]
        candidates=[]
        for pp in (pts,list(reversed(pts))):
            for shift in range(4):
                order=pp[shift:]+pp[:shift]
                cost=sum((Vector(verts[a])-Vector(b)).length_squared for a,b in zip(prev,order))
                candidates.append((cost,order))
        order=min(candidates,key=lambda q:q[0])[1]
        cur=[vertex(p) for p in order]
        for j in range(4): face((prev[j],cur[j],cur[(j+1)%4],prev[(j+1)%4]),False)
        prev=cur
    face(tuple(reversed(prev)),False)
    crest_meta.append({'side':sign,'layer':level,'root':[r,k],'tip_y':cross[-1][1],'tip_z':cross[-1][2]})

mesh=bpy.data.meshes.new('S_rebuild_v5_core_cage')
mesh.from_pydata(verts,[],faces); mesh.update()
core=bpy.data.objects.new('S_rebuild_core_head_crest_neck_torso_tail',mesh); cage.objects.link(core)
for p,s in zip(mesh.polygons,smooth): p.use_smooth=s
bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()

def loft(name,chain,sides=8):
    vs=[]; fs=[]
    for i,(center,wx,wy) in enumerate(chain):
        c=Vector(center)
        tangent=Vector(chain[min(i+1,len(chain)-1)][0])-Vector(chain[max(i-1,0)][0])
        tangent.normalize()
        lateral=Vector((1,0,0)); lateral=(lateral-tangent*lateral.dot(tangent)).normalized()
        sagittal=tangent.cross(lateral).normalized()
        for k in range(sides):
            a=k*math.tau/sides
            vs.append(tuple(c+lateral*(wx*math.cos(a))+sagittal*(wy*math.sin(a))))
    for i in range(len(chain)-1):
        for k in range(sides):
            fs.append((i*sides+k,(i+1)*sides+k,(i+1)*sides+(k+1)%sides,i*sides+(k+1)%sides))
    fs.append(tuple(reversed(range(sides))))
    fs.append(tuple((len(chain)-1)*sides+k for k in range(sides)))
    m=bpy.data.meshes.new(name+'_cage'); m.from_pydata(vs,[],fs); m.update()
    o=bpy.data.objects.new(name,m); cage.objects.link(o)
    for p in m.polygons:p.use_smooth=True
    bm=bmesh.new(); bm.from_mesh(m); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(m); bm.free()
    return o

for sign,label in [(-1,'L'),(1,'R')]:
    fore=[
      ((sign*.125,-.035,1.030),.080,.108),
      ((sign*.150,.020,.930),.076,.092),
      ((sign*.168,.095,.820),.061,.073),
      ((sign*.175,.155,.715),.049,.057),
      ((sign*.166,.035,.575),.036,.044),
      ((sign*.154,-.105,.410),.029,.035),
      ((sign*.148,-.215,.245),.022,.028),
      ((sign*.148,-.255,.125),.019,.024),
      ((sign*.150,-.270,.058),.030,.029)]
    hind=[
      ((sign*.112,.700,1.030),.089,.120),
      ((sign*.145,.610,.945),.086,.111),
      ((sign*.170,.495,.855),.074,.090),
      ((sign*.184,.390,.755),.058,.068),
      ((sign*.178,.575,.605),.046,.055),
      ((sign*.166,.775,.455),.037,.046),
      ((sign*.158,.955,.315),.030,.038),
      ((sign*.153,1.000,.205),.022,.028),
      ((sign*.150,.900,.060),.030,.029)]
    loft('S_forelimb_'+label,fore)
    loft('S_hindlimb_'+label,hind)
    for front,ybase in [(True,-.270),(False,.900)]:
        for toe in (-1,0,1):
            x=sign*.150+toe*.022
            length=.088 if toe==0 else .072
            loft(('S_fore' if front else 'S_hind')+'_toe_'+label+'_'+str(toe),[
              ((x,ybase,.060),.010,.014),
              ((x+toe*.005,ybase-.028,.033),.012,.014),
              ((x+toe*.009,ybase-length,.019),.007,.010),
              ((x+toe*.009,ybase-length-.009,.018),.002,.003)],sides=6)

# Gate A review scene only.
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'; scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE'; scene.display.shading.single_color=(.66,.66,.66)
scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=False
scene.display.shading.background_type='WORLD'
scene.world=bpy.data.worlds.new('Neutral review world'); scene.world.color=(.045,.052,.061)
scene.view_settings.view_transform='Standard'
scene.render.resolution_x=1024; scene.render.resolution_y=768; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False

target=Vector((0,.39,.84))
for stem,location in [('side',(6,.39,.84)),('front',(0,-6,.84)),('front34',(4.4,-4.4,1.95)),('rear34',(-4.4,4.4,1.95)),('back',(0,6,.84))]:
    data=bpy.data.cameras.new('S_REBUILD_CAM_'+stem.upper()); data.type='ORTHO'
    data.ortho_scale=3.30 if stem in ('side','front34','rear34') else 2.65
    o=bpy.data.objects.new(data.name,data); review.objects.link(o); o.location=location
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
scene.camera=bpy.data.objects['S_REBUILD_CAM_FRONT34']

counts={o.name:len(o.data.vertices) for o in cage.objects if o.type=='MESH'}
def digest():
    return hashlib.sha256(b''.join(repr(tuple(v.co)).encode() for o in sorted(cage.objects,key=lambda o:o.name) if o.type=='MESH' for v in o.data.vertices)).hexdigest()
report={
 'gate':'A','status':'REVIEW_PENDING','output':'S-rebuild-v5.blend',
 'built_from':'empty_scene','v4_used_as_geometry_source':False,'v12_used_as_geometry_source':False,
 'source_lock':'S_MODELING_IMAGE_LOCK.md','total_cage_vertices':sum(counts.values()),'mesh_objects':counts,
 'crest':{'type':'six narrow skull-rooted rear-swept laminar plates','central_sagittal_horn':False,'metadata':crest_meta},
 'toes_per_foot':3,'no_materials':len(bpy.data.materials)==0,'no_animation':len(bpy.data.actions)==0,
 'no_armature':not any(o.type=='ARMATURE' for o in bpy.data.objects),'no_cue_band':True,'final_retopology':False,
 'geometry_sha256':digest(),
 'notes':['Fresh Gate A structural reset; v4 and v12 morphology not used.','No Gate A acceptance claimed.']
}
assert report['total_cage_vertices']<1600 and report['no_materials'] and report['no_animation'] and report['no_armature']
json.dump(report,open(os.path.join(OUT,'S-rebuild-v5-gate-A.json'),'w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'S-rebuild-v5.blend'),compress=True)
print('V5_SAVED',json.dumps(report))
