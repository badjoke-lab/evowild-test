"""Replace the inherited noisy color edge with an anatomical surface chart.

The chart is vertex data on the edited existing mesh, interpolated by Blender's
shader and deformed with it. It is not a texture image or separate plate mesh.
"""
import bpy, json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
m=bpy.data.objects['S_ZERO_BODY_CONTINUOUS'].data
assert 'R8 plane coordinates' not in m.color_attributes
attr=m.color_attributes.new(name='R8 plane coordinates',type='FLOAT_COLOR',domain='CORNER')
arr=np.load(ROOT/'evidence/R8_TRIAL_A_ARRAYS.npz')['original']
for p in m.polygons:
    if p.material_index!=6:continue
    for li in p.loop_indices:
        x,y,z=arr[m.loops[li].vertex_index]
        if y<0:
            zz=[1.20,1.30,1.45,1.65,1.85,2.03]
            left=np.interp(z,zz,[1.245,1.14,.99,.82,.62,.51])
            right=np.interp(z,zz,[1.245,1.245,1.235,1.16,1.035,.70])
            cx=np.interp(z,zz,[1.245,1.195,1.11,.99,.82,.61])
        else:
            zz=[1.12,1.30,1.50,1.70,1.88,2.03]
            left=np.interp(z,zz,[.80,.695,.57,.52,.48,.50])
            right=np.interp(z,zz,[.80,.86,.915,.915,.835,.65])
            cx=np.interp(z,zz,[.80,.78,.74,.72,.65,.58])
        side_edge=np.interp(z,[1.1,1.4,1.75,1.95,2.1],[.28,.275,.235,.12,.08])
        distance=min(x-left,right-x,abs(y)-side_edge,z-zz[0],2.035-z)
        attr.data[li].color=(.5+distance, .5+(x-cx)*2.7, z/2.1, 1)
mat=m.materials[6]; nt=mat.node_tree
node=next(n for n in nt.nodes if n.type=='VERTEX_COLOR'); node.layer_name=attr.name
bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(node.outputs['Color'],sep.inputs[0])
mask=nt.nodes.new('ShaderNodeMapRange');mask.clamp=True
mask.inputs['From Min'].default_value=.4975;mask.inputs['From Max'].default_value=.5025
mask.inputs['To Min'].default_value=0;mask.inputs['To Max'].default_value=1
nt.links.new(sep.outputs['X'],mask.inputs['Value'])
ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for index,(position,col) in enumerate([(.0,(.86,.88,.90,1)),(.36,(.86,.88,.90,1)),(.375,(.69,.76,.84,1)),(.73,(.69,.76,.84,1)),(.745,(.44,.53,.65,1)),(1.,(.44,.53,.65,1))]):
    el=ramp.color_ramp.elements[0] if index==0 else ramp.color_ramp.elements.new(position)
    el.position=position;el.color=col
nt.links.new(sep.outputs['Y'],ramp.inputs['Fac'])
mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.035,.046,.067,1)
nt.links.new(mask.outputs['Result'],mix.inputs[0]);nt.links.new(ramp.outputs['Color'],mix.inputs[2])
nt.links.new(mix.outputs[0],bs.inputs['Base Color'])
m.update()
out=ROOT/'evidence/R8_BOUNDARY_REFINEMENT.json';assert not out.exists()
out.write_text(json.dumps({'reason':'First sharpened inherited vertex mask retained a sawtooth edge; revise before candidate save.',
 'method':'Continuous scalar surface chart from neutral vertex coordinates. Tapered near/far thigh masks and longitudinal ivory/pearl/slate planes. 0.005-unit transition width.',
 'mesh_coordinates_unchanged_from_guarded_trial':True,'shader_attached_to_existing_deforming_surface':True,'status':'Pending rendered visual check'},indent=2)+'\n')
sc=bpy.context.scene;sc.frame_set(1);sc.camera=bpy.data.objects['TEST_SIDE_HIP']
sc.render.filepath=str(ROOT/'renders/R8_UNSAVED_BOUNDARY_B.png')
assert not Path(sc.render.filepath).exists()
print('R8_BOUNDARY_B_READY',sc.render.filepath)
