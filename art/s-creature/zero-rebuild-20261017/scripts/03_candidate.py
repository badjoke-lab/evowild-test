"""Candidate after visual inspection of REFINED real renders and viewport.
Replace ray-projected regions that folded across limbs with explicit closed volumes.
This changes only this lane's anatomy; the saved BLOCKOUT and REFINED remain intact.
"""
import bpy,bmesh,math,random,json
from mathutils import Vector
from pathlib import Path
ROOT=Path('/Users/lyla/evowild-s-zero-20261017/art/s-creature/zero-rebuild-20261017')
scene=bpy.context.scene
assert scene['stage']=='REFINED'
model=bpy.data.collections['S_ZERO_CREATURE'];root=bpy.data.objects['S_ZERO_ROOT']
DARK=bpy.data.materials['S | graphite dermis'];RIDGE=bpy.data.materials['S | slate tendons']
WHITE=bpy.data.materials['S | pearl shell'];LIGHT=bpy.data.materials['S | ivory facet'];SHADE=bpy.data.materials['S | blue grey facet']
BLUE=bpy.data.materials['S | cobalt recess'];CYAN=bpy.data.materials['S | cue cyan'];BLACK=bpy.data.materials['S | socket'];GOLD=bpy.data.materials['S | cue warm alloy']
MATS=[WHITE,LIGHT,SHADE,BLUE]
src=(ROOT/'scripts/01_build_blockout.py').read_text();exec(src[src.index('def mesh_obj'):src.index('# Continuous flesh:')])
random.seed(29)
def drop(name):
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)
def volume(name,rows,mat=WHITE,sides=16,steps=4):
    drop(name);ob=tube(name,rows,mat,sides,steps)
    if mat==WHITE:
        ob.data.materials.append(LIGHT);ob.data.materials.append(SHADE)
        for p in ob.data.polygons:
            # restrained longitudinal facet grouping
            col=p.index%sides;row=p.index//sides
            if col in [2,3] and row%8<5:p.material_index=1
            elif col==9 and row%9<3:p.material_index=2
    return ob
# Smooth frontal shoulder width taper; avoids a large broad shoulder board.
body=bpy.data.objects['S_ZERO_BODY_CONTINUOUS']
for v in body.data.vertices:
    x,y,z=v.co
    if -1.25<x<-.40 and 1.30<z<2.10:
        wx=max(0,1-abs((x+.825)/.425));wz=max(0,1-abs((z-1.70)/.40))
        v.co.y*=1-.13*wx*wz
body.data.update()
for s,lab in [(-1,'N'),(1,'F')]:
    volume('DELTOID_'+lab,[(-.87,s*.24,1.99,.025,.035),(-.89,s*.30,1.90,.115,.15),(-.86,s*.32,1.75,.155,.235),(-.80,s*.31,1.58,.14,.20),(-.71,s*.30,1.44,.065,.10),(-.68,s*.29,1.39,.014,.025)])
    volume('SCAPULA_'+lab,[(-.98,s*.20,1.92,.035,.04),(-.75,s*.24,1.96,.13,.10),(-.48,s*.25,1.95,.145,.095),(-.27,s*.23,1.96,.09,.045),(-.18,s*.20,2.00,.005,.008)])
    volume('RIB_SHELL_'+lab,[(-.49,s*.25,1.82,.025,.05),(-.34,s*.265,1.79,.095,.145),(-.10,s*.245,1.81,.11,.15),(.09,s*.20,1.82,.065,.09),(.22,s*.15,1.87,.008,.015)])
    volume('LOWER_RIB_'+lab,[(-.73,s*.22,1.43,.015,.02),(-.48,s*.27,1.40,.045,.055),(-.23,s*.23,1.48,.04,.05),(.07,s*.18,1.63,.035,.045),(.28,s*.12,1.74,.006,.009)])
    if s<0:
        hip=[(.47,s*.18,1.94,.025,.025),(.67,s*.25,1.91,.105,.115),(.84,s*.33,1.78,.15,.20),(1.00,s*.355,1.56,.135,.19),(1.13,s*.33,1.37,.075,.115),(1.23,s*.29,1.25,.006,.014)]
    else:
        hip=[(.46,s*.18,1.94,.025,.03),(.63,s*.27,1.86,.11,.13),(.72,s*.33,1.66,.15,.19),(.72,s*.34,1.43,.12,.15),(.80,s*.31,1.17,.005,.018)]
    volume('PELVIS_'+lab,hip)
    drop('THIGH_SHELL_'+lab)
    drop('NECK_TENDON_'+lab);drop('NAPE_IVORY_'+lab)
    volume('NECK_TENDON_'+lab,[(-1.91,s*.075,2.15,.012,.015),(-1.65,s*.115,1.99,.025,.025),(-1.35,s*.165,1.77,.032,.03),(-1.10,s*.18,1.56,.006,.008)],RIDGE,12)
    volume('NAPE_IVORY_'+lab,[(-1.79,s*.055,2.24,.012,.012),(-1.56,s*.075,2.16,.04,.02),(-1.30,s*.09,2.05,.04,.027),(-1.05,s*.14,1.97,.04,.035),(-.95,s*.16,1.94,.005,.01)])
    drop('CHEEK_'+lab);drop('BROW_'+lab)
    volume('CHEEK_'+lab,[(-2.30,s*.05,2.00,.009,.012),(-2.17,s*.10,2.05,.022,.042),(-2.04,s*.116,2.13,.022,.055),(-1.99,s*.10,2.15,.007,.01)])
    # Reduce excess side-to-side bow of the crest; preserve sagittal profile.
    for name in ['CROWN_MAIN_'+lab,'CROWN_BLUE_'+lab]:
        ob=bpy.data.objects[name]
        for v in ob.data.vertices:
            t=max(0,min(1,(v.co.z-2.19)/.92))
            v.co.y+=s*(-.095*math.sin(math.pi*t)+.020*t)
        ob.data.update()
    drop('CROWN_IVORY_RIDGE_'+lab)
    crest=[]
    for x,z,r in [(-2.19,2.19,.008),(-1.98,2.435,.016),(-1.65,2.643,.014),(-1.18,2.837,.010),(-.62,2.999,.006),(-.08,3.11,.001)]:
        t=max(0,min(1,(z-2.19)/.92));y=s*(.145+.025*math.sin(math.pi*t)+.045*t)
        crest.append((x,y,z,r,r))
    volume('CROWN_IVORY_RIDGE_'+lab,crest,WHITE,10,3)
# A single tapered cranial shield, continuous across the forehead.
drop('FOREHEAD_MEDIAN')
volume('FOREHEAD_MEDIAN',[(-2.365,0,1.992,.026,.016),(-2.28,0,2.09,.053,.025),(-2.15,0,2.221,.083,.032),(-2.04,0,2.292,.074,.038),(-1.96,0,2.29,.029,.018)],WHITE,16,4)
# Explicit upper arms following their own limb paths.
for name,rows in [
 ('FORE_NEAR',[(-.78,-.33,1.57,.06,.07),(-.70,-.36,1.41,.08,.11),(-.56,-.345,1.21,.055,.09),(-.47,-.31,1.05,.005,.015)]),
 ('FORE_FAR',[(-.98,.31,1.56,.04,.04),(-.98,.34,1.37,.055,.07),(-1.04,.32,1.16,.03,.05),(-1.07,.30,1.03,.005,.008)])]:
    volume('BRACHIAL_'+name,rows)
# Remove projected lower-limb membranes and trace each anatomical ridge independently.
for name,y,rows in [
 ('FORE_NEAR',-.355,[(-.52,1.16,.045,.055),(-.46,.91,.035,.043),(-.34,.44,.014,.018),(-.39,.23,.006,.009)]),
 ('FORE_FAR',.335,[(-1.03,1.12,.043,.055),(-1.17,.81,.03,.039),(-1.36,.40,.014,.02),(-1.45,.17,.006,.01)]),
 ('HIND_NEAR',-.345,[(1.58,.96,.035,.055),(1.74,.62,.028,.035),(1.96,.26,.013,.018),(1.97,.14,.006,.009)]),
 ('HIND_FAR',.345,[(1.08,.91,.033,.05),(.91,.57,.027,.035),(.75,.27,.014,.02),(.65,.12,.006,.009)])]:
    volume('CANNON_RIDGE_'+name,[(x,y,z,ry,rz) for x,z,ry,rz in rows],RIDGE,10,4)
# Keep only a small forearm spur, with plausible root thickness.
for ob in list(model.objects):
    if ob.name.startswith('ELBOW_SPUR_') and 'HIND' in ob.name:drop(ob.name)
# Tail fronds: a deeper, overlapping swept silhouette, matching the sheet's lower tips.
for ob in list(model.objects):
    if ob.name.startswith(('TAIL_BLADE_','TAIL_BLUE_','TAIL_IVORY_')):drop(ob.name)
for i in range(7):
    t=i/6;x=1.00+1.10*t;z=1.925-.64*t*t
    for s in [-1,1]:
        y=s*(.075+.04*math.sin(t*math.pi));length=.30+.075*t
        p=[(x-.08,y,z+.01),(x+.085,y+s*.045,z+.025),(x+length,y+s*.055,z-.30-.12*t),(x+.12,y+s*.10,z-.16),(x-.01,y+s*.055,z-.055)]
        patch('TAIL_BLADE_%d_%d'%(i,s),p,(0,s*.023,.025),DARK,False,0)
        patch('TAIL_BLUE_%d_%d'%(i,s),[p[0],p[1],(x+length*.92,y+s*.06,z-.25-.11*t),(x+.08,y+s*.065,z-.07)],(0,s*.025,.015),BLUE,False,0)
        if i<5:
            patch('TAIL_IVORY_%d_%d'%(i,s),[(x-.06,y,z+.03),(x+.05,y+s*.025,z+.04),(x+length*.65,y+s*.06,z-.15-.08*t),(x+.05,y+s*.05,z-.04)],(0,s*.027,.018),WHITE,False,0)
# Better foot definition: add small ivory front caps that are visible across all views.
for name,fx,fy in [('FORE_NEAR',-.45,-.29),('FORE_FAR',-1.46,.28),('HIND_NEAR',1.97,-.28),('HIND_FAR',.64,.28)]:
    for k in [-1,1]:
        yy=fy+k*.06
        volume('HOOF_FACE_'+name+'_'+str(k),[(fx-.18,yy,.036,.018,.014),(fx-.135,yy,.085,.027,.020),(fx-.065,yy,.142,.020,.014)],WHITE,10,3)
        volume('HOOF_SIGNAL_'+name+'_'+str(k),[(fx-.19,yy-.008,.044,.006,.006),(fx-.15,yy-.008,.09,.008,.007),(fx-.087,yy-.008,.14,.004,.004)],BLUE,8,3)
# Make a readable dorsal sacrum rather than an exposed dark rod.
volume('SACRAL_MANTLE',[(.22,0,1.965,.04,.016),(.48,0,1.98,.13,.03),(.76,0,1.985,.15,.04),(.99,0,1.94,.05,.018)],WHITE,16,4)
scene['stage']='CANDIDATE'
scene['candidate_status']='Unreviewed until five real renders and technical audit'
scene.camera=bpy.data.objects['CAM_FRONT34']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'S_ZERO_CANDIDATE.blend'),compress=True)
(ROOT/'evidence/CANDIDATE_CHANGES.json').write_text(json.dumps({'stage':'CANDIDATE','trigger':'REFINED showed ray projection folds and excessive frontal crown bow','changes':['Closed loft volumes for shoulder, scapula, ribs, pelvis, upper arms','Separate limb-following cannon ridges; removed cross-limb membranes','Narrow frontal crown; narrow white crown ridge','Continuous forehead shield','Deeper swept tail fronds','Split toe front caps'],'no_old_geometry':True},indent=2)+'\n')
print('CANDIDATE saved',len(model.objects),'objects')
