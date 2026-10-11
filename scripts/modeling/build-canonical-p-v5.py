"""P v5: joined, voxel-remeshed anatomy, sculpted relief and blended skinning.

blender -b -t 4 --python scripts/modeling/build-canonical-p-v5.py -- --no-render
P.webp is the sole morphological authority. v4 supplies only unchanged secondary
head/feet/tail construction helpers. No v1-v4 outputs are written by this script.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector, Matrix

# Evaluate construction only, before v4 painting, rigging or any file export.
seed = Path(__file__).with_name('build-canonical-p-v4.py').read_text()
exec(compile(seed.split('# Vertex-painted colour transitions')[0], '<v4-secondary-construction>', 'exec'))
OUT = ROOT / 'public/models/evowild-p'
EVIDENCE = ROOT / 'docs/evidence/p-canonical-3d-v5-20261011'
OFFLINE = ROOT / 'work/p-canonical-v5/blender-renders'
EVIDENCE.mkdir(parents=True, exist_ok=True)
OFFLINE.mkdir(parents=True, exist_ok=True)

# Remove separate muscle shells. They must never survive as intersecting geometry.
discard = ('Dorsal oxblood', 'Scapular red', 'Shoulder ridge', 'Rear chest lobe',
           'Pelvic red', 'Pectoral slate', 'Thoracic ventral', 'Neck red sweep',
           'Integrated forelimb', 'Forearm dark', 'Haunch red', 'Articulated joint')
for obj in list(parts):
    if obj.name.startswith(discard):
        parts.remove(obj)
        bpy.data.objects.remove(obj, do_unlink=True)

# Broad shoulder-to-elbow union guides. These are temporary volumes, never separate
# final muscles. Their intersections are removed by the voxel union below.
for side in [-1, 1]:
    tag = 'FL' if side < 0 else 'FR'
    loft('Union guide shoulder to elbow '+tag, [
        (-.81,side*.35,2.48,.25,.25),
        (-.74,side*.49,2.31,.34,.32),
        (-.71,side*.55,2.05,.33,.34),
        (-.66,side*.57,1.80,.30,.30),
        (-.60,side*.583,1.56,.24,.25),
        (-.60,side*.583,1.30,.17,.18),
        (-.60,side*.583,1.12,.13,.14)], skin, tag+'_upper', 20, 2)

join_parts=[o for o in parts if o['anatomy'] in ['body','neck','FL_upper','FR_upper','FL_lower','FR_lower','HL_upper','HR_upper','HL_lower','HR_lower']]
bpy.ops.object.select_all(action='DESELECT')
for obj in join_parts:
    obj.select_set(True)
    parts.remove(obj)
bpy.context.view_layer.objects.active=join_parts[0]
bpy.ops.object.join()
anatomy=bpy.context.object
anatomy.name='P_v5_continuous_chest_shoulders_limbs'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
anatomy.data.remesh_voxel_size=.026
anatomy.data.remesh_voxel_adaptivity=0
bpy.ops.object.voxel_remesh()
smooth=anatomy.modifiers.new('Relax voxel union without part boundaries','SMOOTH')
smooth.factor=1.2; smooth.iterations=6
bpy.ops.object.modifier_apply(modifier=smooth.name)

def gauss(x,c,w): return math.exp(-((x-c)/w)**2)
def ss(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)
def path_distance(co, points):
    best=100
    for a,b in zip(points,points[1:]):
        a=Vector(a);b=Vector(b);d=b-a
        t=max(0,min(1,(co-a).dot(d)/d.length_squared))
        best=min(best,(co-(a+t*d)).length)
    return best
pectoral=[(-1.25,.12,1.96),(-1.18,.35,1.79),(-.98,.49,1.58),(-.73,.40,1.40),(-.50,.20,1.35)]

# Sculpt the continuous surface: broad pectoral keel, scapular fan, deltoid/triceps
# sweep and the shallow axillary fold. All displacements operate on the SAME mesh.
# This deliberately avoids inset shell edges or independent sphere-like muscles.
anatomy.data.update()
sculpt_normals=[v.normal.copy() for v in anatomy.data.vertices]
for v in anatomy.data.vertices:
    x,y,z=v.co; ay=abs(y); side=1 if y>=0 else -1
    lateral=ss(.18,.46,ay)
    # Shorten the barrel impression by lifting the abdomen behind the chest.
    v.co.z += (.13*gauss(x,.25,.58)+.065*gauss(x,-.65,.44))*(1-ss(1.40,1.85,z))
    v.co.y *= 1-.12*gauss(x,.24,.47)*gauss(z,1.72,.40)
    fan=.09*gauss(x,-.65,.38)*gauss(z,2.27,.39)
    upper=.065*gauss(x,-.61,.22)*gauss(z,1.79,.34)
    # Anatomical break is a shallow groove in connected skin, not a severed edge.
    fold=-.043*gauss(x,-.29+.10*(z-1.8),.072)*gauss(z,1.96,.36)
    deltoid=-.032*gauss(z,2.14+.45*(x+.65),.050)*gauss(x,-.69,.30)
    v.co.y += side*lateral*(fan+upper+fold+deltoid)
    # Sternum/paired pectorals flow outward into the front of each upper arm.
    front=gauss(x,-1.08,.29)*gauss(z,1.73,.32)
    v.co.x -= .075*front*(.65+.35*gauss(ay,.25,.22))
    v.co.z -= .035*gauss(x,-.91,.28)*gauss(y,0,.13)*gauss(z,1.47,.20)
    # Paired sloping breast planes and their common sternal depression. A carved
    # crease replaces the old separate slate pectoral shells.
    breast=gauss(x,-1.03,.35)*gauss(z,1.77,.31)
    v.co.x -= .095*breast*gauss(ay,.30,.18)
    v.co.x += .055*breast*gauss(y,0,.065)
    pd=path_distance(Vector((x,ay,z)),pectoral)
    v.co -= sculpt_normals[v.index]*(.028*math.exp(-(pd/.085)**2))

relax=anatomy.modifiers.new('Soften sculpt sampling at the pectoral crease','SMOOTH')
relax.factor=.45;relax.iterations=3
bpy.ops.object.modifier_apply(modifier=relax.name)

# Reduce the uniform voxel tessellation without changing the connected surface.
dec=anatomy.modifiers.new('Review mesh reduction','DECIMATE');dec.ratio=.68
bpy.ops.object.modifier_apply(modifier=dec.name)
for p in anatomy.data.polygons:p.use_smooth=True
anatomy.data.update()

paint=material('P v5 continuous painted skin',(1,1,1),.74)
bs=paint.node_tree.nodes.get('Principled BSDF')
vc=paint.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='P_color'
paint.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
anatomy.data.materials.clear();anatomy.data.materials.append(paint)
attr=anatomy.data.color_attributes.new(name='P_color',type='FLOAT_COLOR',domain='CORNER')
for loop in anatomy.data.loops:
    x,y,z=anatomy.data.vertices[loop.vertex_index].co;ay=abs(y)
    dorsal=ss(1.99-.30*(x+.6),2.17-.30*(x+.6),z)
    shoulder=gauss(x,-.66,.46)*ss(1.28,1.64,z)*ss(.34,.64,ay)
    haunch=gauss(x,.96,.34)*ss(1.03,1.47,z)*ss(.31,.55,ay)
    redmix=max(dorsal,shoulder,haunch)
    # Broad gray breast continues into proximal forearm rather than separate plates.
    gray=gauss(x,-.99,.53)*(1-ss(1.89,2.18,z))
    gray=max(gray,(1-ss(.95,1.30,z))*.8)
    base=tuple(a*(1-gray)+b*gray for a,b in zip((.031,.040,.054),(.090,.108,.139)))
    color=tuple(a*(1-redmix)+b*redmix for a,b in zip(base,(.205,.027,.024)))
    # Curved, shallow relief seams follow scapula and triceps on the same surface.
    seam1=gauss(z,2.26+.32*(x+.80),.033)*gauss(x,-.62,.30)*ss(.48,.70,ay)
    seam2=gauss(x,-.35+.11*(z-1.8),.036)*gauss(z,1.94,.35)*ss(.40,.59,ay)
    seam3=gauss(x,-.75+.15*(z-1.6),.026)*gauss(z,1.68,.24)*ss(.62,.77,ay)
    pectoral_seam=math.exp(-(path_distance(Vector((x,ay,z)),pectoral)/.044)**2)
    shade=1-.55*max(seam1,seam2,seam3,pectoral_seam)
    attr.data[loop.index].color=(*(c*shade for c in color),1)
for p in anatomy.data.polygons:p.material_index=0
anatomy['anatomy']='continuous';parts.insert(0,anatomy)

# Topology proof BEFORE glTF's material/color/normal vertex splits.
adj=[[] for _ in anatomy.data.vertices]
counts={}
for poly in anatomy.data.polygons:
    for edge_key in poly.edge_keys:counts[edge_key]=counts.get(edge_key,0)+1
for e in anatomy.data.edges:
    a,b=e.vertices;adj[a].append(b);adj[b].append(a)
unseen=set(range(len(adj)));components=[]
while unseen:
    todo=[unseen.pop()];size=0
    while todo:
        i=todo.pop();size+=1
        for j in adj[i]:
            if j in unseen:unseen.remove(j);todo.append(j)
    components.append(size)
topology={'method':'voxel union + relaxation + continuous-surface relief sculpt + decimation',
          'voxelMetres':.026,'components':components,'vertices':len(adj),
          'faces':len(anatomy.data.polygons),'boundaryEdges':sum(n==1 for n in counts.values()),
          'nonManifoldEdges':sum(n!=2 for n in counts.values()),
          'covers':['chest','left/right scapula','left/right upper arm','forearms','neck','abdomen','hind limbs'],
          'disconnectedMuscleShells':0}
assert len(components)==1,topology
assert topology['nonManifoldEdges']==0,topology

# Secondary components use the original P palette and maintain their existing form.
for obj in parts[1:]:
    if 'P_color' not in obj.data.color_attributes:
        a=obj.data.color_attributes.new(name='P_color',type='FLOAT_COLOR',domain='CORNER')
        for c in a.data:c.color=(1,1,1,1)
    if obj.name.startswith('Swept crest'):
        obj.data.materials.clear();obj.data.materials.append(paint)
        for p in obj.data.polygons:p.material_index=0
        a=obj.data.color_attributes['P_color']
        for loop in obj.data.loops:
            c=obj.matrix_world @ obj.data.vertices[loop.vertex_index].co
            t=ss(-.055,.055,min((.24-abs(c.y))*2,c.z-2.59))
            a.data[loop.index].color=(*(s*(1-t)+r*t for s,r in zip(skin.diffuse_color[:3],red.diffuse_color[:3])),1)
    if obj.name.startswith(('Directional skull','Lower jaw')):
        for p in obj.data.polygons:p.use_smooth=False

# Reuse the documented v4 rig joint coordinates and provisional run timing. The
# critical replacement is continuous, blended deformation instead of rigid pieces.
rig=seed[seed.index('# V3: correct the too-long'):]
old="""    group=obj.vertex_groups.new(name=obj['anatomy']);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')"""
new="""    if obj is anatomy:
        groups={name:obj.vertex_groups.new(name=name) for name in arm.data.bones.keys()}
        for v in obj.data.vertices:
            x,y,z=v.co; ux=x/X_COMPACT; ay=abs(y)
            weights={}
            front=1-ss(-.15,.25,ux)
            leg=ss(.22,.49,ay)*(1-ss(1.48 if front>.5 else 1.16,2.24 if front>.5 else 1.70,z))
            tag=('F' if front>.5 else 'H')+('L' if y<0 else 'R')
            kneeZ=limbs[tag][1].z
            lower=1-ss(kneeZ-.20,kneeZ+.20,z)
            weights[tag+'_upper']=leg*(1-lower)
            weights[tag+'_lower']=leg*lower
            neck=(1-ss(-1.51,-1.03,ux))*ss(1.85,2.14,z)
            weights['neck']=(1-leg)*neck
            weights['body']=(1-leg)*(1-neck)
            total=sum(weights.values())
            for name,w in weights.items():
                if w>0:groups[name].add([v.index],w/total,'REPLACE')
    else:
        group=obj.vertex_groups.new(name=obj['anatomy']);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')"""
assert old in rig
rig=rig.replace(old,new).replace('p-canonical-v4','p-canonical-v5').replace('manifest-v4','manifest-v5')
rig=rig.replace("scene.cycles.samples=48","scene.cycles.samples=24")
rig=rig.replace("'fore':.60,'hind':.36","'fore':.53,'hind':.32")
# Author from frame zero: otherwise glTF starts at 1/30 s and Three.js adds
# a one-frame hold to every nominal 0.8-second cycle.
rig=rig.replace('scene.frame_start=1;scene.frame_end=25','scene.frame_start=0;scene.frame_end=24')
rig=rig.replace('range(1,26)','range(0,25)').replace('phase=(frame-1)/24','phase=frame/24')
rig=rig.replace("'v4 forelimb rounded anatomical study; production HOLD'","'v5 joined-anatomy review candidate; production HOLD'")
rig=rig.replace("'Blender 4.3.2 / deterministic contour lofts and anatomical surface panels'","'Blender 4.3.2 / voxel-unified sculpted anatomical skin with blended weights'")
exec(compile(rig,'<v5-rig-export-review>','exec'))
topology['blendedVertices']=sum(sum(g.weight>.01 for g in v.groups)>1 for v in body.data.vertices)
(EVIDENCE/'topology-check.json').write_text(json.dumps(topology,indent=2)+'\n')
print('V5_CONNECTED_TOPOLOGY',json.dumps(topology))
