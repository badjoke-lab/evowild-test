"""Refinement after recorded BLOCKOUT SIDE/FRONT/FRONT34 inspection.
Fix buried shell anatomy, parallel front crest, small toes. Preserve body source.
"""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/lyla/evowild-s-zero-20261017/art/s-creature/zero-rebuild-20261017')
scene=bpy.context.scene
assert scene['stage']=='BLOCKOUT'
model=bpy.data.collections['S_ZERO_CREATURE'];root=bpy.data.objects['S_ZERO_ROOT']
DARK=bpy.data.materials['S | graphite dermis'];RIDGE=bpy.data.materials['S | slate tendons']
WHITE=bpy.data.materials['S | pearl shell'];LIGHT=bpy.data.materials['S | ivory facet'];SHADE=bpy.data.materials['S | blue grey facet']
BLUE=bpy.data.materials['S | cobalt recess'];CYAN=bpy.data.materials['S | cue cyan'];BLACK=bpy.data.materials['S | socket'];GOLD=bpy.data.materials['S | cue warm alloy']
MATS=[WHITE,LIGHT,SHADE,BLUE]
src=(ROOT/'scripts/01_build_blockout.py').read_text()
exec(src[src.index('def mesh_obj'):src.index('# Continuous flesh:')])
random.seed(23)
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
changes=[]
def remove(name):
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
def rounded(poly):
    # Preserve shape; 75/25 corner cuts, not a subdivision that buries the shell.
    out=[]
    for i,p in enumerate(poly):
        a=poly[i-1];b=poly[(i+1)%len(poly)]
        out += [(p[0]*.83+a[0]*.17,p[1]*.83+a[1]*.17),(p[0]*.83+b[0]*.17,p[1]*.83+b[1]*.17)]
    return out

def surface_shell(name,poly,s,bulge=.04,material=WHITE,facet=True):
    remove(name);poly=rounded(poly);n=len(poly)
    cx=sum(p[0] for p in poly)/n;cz=sum(p[1] for p in poly)/n
    vs=[];fs=[]
    for r in [1,.73,.34,0]:
        pp=poly if r else [(cx,cz)]
        for x,z in pp:
            x=cx+(x-cx)*r;z=cz+(z-cz)*r
            loc,norm,index,dist=bvh.ray_cast(Vector((x,s*3,z)),Vector((0,-s,0)),6)
            yy=abs(loc.y) if loc else .12
            vs.append((x,s*(yy+.008+bulge*(1-r*r)),z))
    for q in range(2):
        for j in range(n):
            k=(j+1)%n;fs.append((q*n+j,q*n+k,(q+1)*n+k,(q+1)*n+j))
    for j in range(n):fs.append((2*n+j,2*n+(j+1)%n,3*n))
    nf=len(vs);vs+= [(x,y-s*.032,z) for x,y,z in vs]
    fs += [tuple(nf+j for j in reversed(f)) for f in list(fs)]
    for j in range(n):k=(j+1)%n;fs.append((j,k,nf+k,nf+j))
    ob=mesh_obj(name,vs,fs,material)
    if facet and material==WHITE:
        ob.data.materials.append(LIGHT);ob.data.materials.append(SHADE)
        for p in ob.data.polygons[:3*n]:
            p.material_index=1 if p.index%11 in [2,3] else (2 if p.index%17==5 else 0)
    smooth(ob)
    ob['construction']='Closed domed shell projected onto newly built continuous anatomy'
    changes.append(name);return ob

for s,lab in [(-1,'N'),(1,'F')]:
    surface_shell('DELTOID_'+lab,[(-1.08,1.77),(-.94,1.98),(-.73,1.94),(-.60,1.78),(-.61,1.53),(-.72,1.40),(-.96,1.50),(-1.10,1.64)],s,.045)
    surface_shell('SCAPULA_'+lab,[(-.94,1.94),(-.69,2.04),(-.38,2.03),(-.20,1.96),(-.35,1.80),(-.62,1.74),(-.79,1.80)],s,.035)
    surface_shell('RIB_SHELL_'+lab,[(-.45,1.88),(-.17,1.94),(.10,1.89),(.22,1.73),(.04,1.60),(-.18,1.59),(-.38,1.70)],s,.025)
    surface_shell('LOWER_RIB_'+lab,[(-.70,1.44),(-.43,1.45),(-.10,1.56),(.19,1.72),(.04,1.48),(-.36,1.33),(-.61,1.35)],s,.015)
    if s<0:
        hip=[(.47,1.87),(.65,1.99),(.94,1.94),(1.08,1.75),(1.22,1.31),(1.05,1.23),(.85,1.47),(.67,1.78)]
        thigh=[(.84,1.88),(1.02,1.79),(1.19,1.53),(1.25,1.20),(1.06,1.30),(.92,1.55)]
    else:
        hip=[(.44,1.86),(.62,1.98),(.84,1.91),(.91,1.72),(.85,1.38),(.70,1.32),(.57,1.56)]
        thigh=[(.61,1.73),(.82,1.61),(.86,1.35),(.78,1.13),(.65,1.27),(.57,1.51)]
    surface_shell('PELVIS_'+lab,hip,s,.035)
    surface_shell('THIGH_SHELL_'+lab,thigh,s,.022)
    surface_shell('CHEEK_'+lab,[(-2.30,1.98),(-2.14,2.12),(-1.96,2.16),(-1.99,2.04),(-2.17,1.97)],s,.012)
    surface_shell('BROW_'+lab,[(-2.32,2.07),(-2.16,2.24),(-1.99,2.28),(-2.02,2.19),(-2.17,2.12)],s,.012)
    surface_shell('NECK_TENDON_'+lab,[(-1.90,2.14),(-1.64,2.00),(-1.33,1.76),(-1.08,1.51),(-1.17,1.72),(-1.61,2.11)],s,.012,RIDGE,False)
    surface_shell('NAPE_IVORY_'+lab,[(-1.77,2.23),(-1.48,2.12),(-1.17,2.04),(-.96,2.00),(-1.14,1.94),(-1.43,2.02)],s,.01)

# Broad forehead and narrow nose ridge unify the two side cheeks.
patch('FOREHEAD_MEDIAN',[(-2.34,-.035,2.055),(-2.19,-.08,2.21),(-2.02,-.065,2.32),(-1.92,0,2.31),(-2.02,.065,2.32),(-2.19,.08,2.21),(-2.34,.035,2.055)],(0,0,.025),WHITE,True,0)
ell('NOSE_CAP',(-2.35,0,1.982),(.045,.044,.025),DARK)
# Small jaw seam gives a tapered muzzle, not a featureless taper.
for s in [-1,1]:
    tube('MOUTH_SEAM_'+str(s),[(-2.35,s*.034,1.964,.005,.005),(-2.25,s*.066,1.99,.006,.005),(-2.12,s*.082,2.023,.004,.004)],BLACK,8,3)

# Front-view crest opens at the mid-height, tapers back at its tips.
for ob in list(model.objects):
    if ob.name.startswith('CROWN_'):
        s=-1 if ob.name.endswith('_N') else 1
        for v in ob.data.vertices:
            t=max(0,min(1,(v.co.z-2.19)/.92))
            v.co.y += s*(.12*math.sin(math.pi*t)+.025*t)
        ob.data.update();changes.append(ob.name)
# Extend the characteristic large dorsal swept point, preserving its rooted base.
for ob in model.objects:
    if ob.name.startswith(('DORSAL_CREST_2_','DORSAL_BLUE_2_')):
        for v in ob.data.vertices:
            t=max(0,min(1,(v.co.x+.70)/.38));v.co.x+=.20*t
        ob.data.update()

legs={
'FORE_NEAR':(-.74,-.31,1.42,-.52,1.13,-.39,.20),
'FORE_FAR':(-.95,.29,1.37,-1.03,1.08,-1.37,.37),
'HIND_NEAR':(1.17,-.28,1.12,1.58,.91,1.98,.23),
'HIND_FAR':(.71,.28,1.11,1.08,.87,.73,.22)}
for name,(a,y,az,x,z,ax,az2) in legs.items():
    s=-1 if y<0 else 1
    if name.startswith('FORE'):
        surface_shell('BRACHIAL_'+name,[(a-.11,az+.13),(a+.10,az+.07),(x+.08,z+.01),(x+.05,z-.16),(x-.07,z-.03)],s,.018)
    surface_shell('CANNON_RIDGE_'+name,[(x-.055,z+.065),(x+.075,z+.14),(x+.065,z-.10),(ax+.025,az2),(ax-.035,az2+.02)],s,.022,RIDGE,False)
    side_patch('ELBOW_SPUR_'+name,[(x+.02,z-.10),(x+.12,z+.18),(x+.15,z+.21),(x+.13,z+.015)],y+s*.03,.023,DARK,False,0)
# Toe shells should read as a split load-bearing foot in both front and side views.
for name,fx,fy in [('FORE_NEAR',-.45,-.29),('FORE_FAR',-1.46,.28),('HIND_NEAR',1.97,-.28),('HIND_FAR',.64,.28)]:
    for ob in model.objects:
        if ob.type=='MESH' and any(ob.name.startswith(p+name) for p in ['TOE_','TOE_IVORY_','TOE_CYAN_']):
            for v in ob.data.vertices:
                v.co.x=fx+(v.co.x-fx)*1.25;v.co.y=fy+(v.co.y-fy)*1.30;v.co.z*=1.12
            ob.data.update()
# Add broader white upper facets and tapered cobalt centers to tail blades.
for i in range(6):
    t=i/6;x=1.02+1.12*t;z=1.91-.62*t*t
    for s in [-1,1]:
        yy=s*(.09+.025*math.sin(t*math.pi))
        patch('TAIL_IVORY_%d_%d'%(i,s),[(x-.06,yy,z+.025),(x+.08,yy+s*.04,z+.038),(x+.33,yy+s*.04,z-.08-.15*t),(x+.10,yy+s*.07,z-.035)],(0,s*.009,.025),WHITE,False,0)

# Improve review lighting without concealing geometry.
for ar in bpy.context.screen.areas:
    if ar.type=='VIEW_3D':
        ar.spaces.active.shading.type='SOLID';ar.spaces.active.shading.color_type='MATERIAL'
        ar.spaces.active.region_3d.view_perspective='CAMERA';ar.spaces.active.overlay.show_overlays=False
scene.camera=bpy.data.objects['CAM_FRONT34'];scene['stage']='REFINED'
scene['refinement']='Surface-conforming shells; crown transverse sweep; widened toes; anatomical limb ridges'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'S_ZERO_REFINED.blend'),compress=True)
(ROOT/'evidence/REFINEMENT_CHANGES.json').write_text(json.dumps({'stage':'REFINED','inspected_views':['SIDE','FRONT','FRONT34'],'findings':['Buried ivory anatomy','Parallel frontal crown','Undersized split toes'],'modified_objects':changes,'body_reused':'Only newly built S_ZERO_BLOCKOUT geometry'},indent=2)+'\n')
print('REFINED saved;',len(changes),'targeted surface/crest changes')
