"""Single deliberate anatomical sculpt pass below the newly connected sheet."""
import bpy,bmesh,json
from mathutils import Vector
pilot=bpy.app.driver_namespace['shoulder_pilot'];body=pilot['body'];OUT=pilot['OUT']
SIDE=globals().get('SIDE',1)
STAGE=globals().get('STAGE','10_ANATOMY')
pilot['before_chest_arm']=body.data.copy()
bm=bmesh.new();bm.from_mesh(body.data)
def ramp(a,b,t):
    q=max(0,min(1,(t-a)/(b-a)));return q*q*(3-2*q)
def brush(y,z,cy,cz,ry,rz):
    d=((y-cy)/ry)**2+((z-cz)/rz)**2
    return (1-min(1,d))**2
changed=0
for v in bm.verts:
    x,y,z=v.co
    xlocal=-.03588832542300224+SIDE*(x+.03588832542300224)
    lateral=ramp(.035,.09,xlocal)
    # Recess the tissue immediately below the pointed shoulder plate. This
    # short valley separates pectoral volume from the proximal upper-arm belly.
    hollow=brush(y,z,-.332,-.172,.060,.037)
    arm=brush(y,z,-.263,-.221,.053,.077)
    if lateral*(hollow+arm)>0:
        v.co.x+=SIDE*lateral*(-.019*hollow+.011*arm)
        v.co.y-=lateral*.005*arm
        changed+=1
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free();body.data.update()
(OUT/(STAGE+'_OPERATION.json')).write_text(json.dumps({'operation':'one compact anatomical sculpt pass: pectoral/arm valley .019, distinct proximal arm belly .011','side':SIDE,'vertices_shaped':changed,'disconnected_parts_added':0},indent=2))
pilot['view']('SIDE' if SIDE==1 else 'LEFT_SIDE',STAGE)
