import math
import os
import sys
import numpy as np
import trimesh


def args():
    xs=sys.argv
    if "--" not in xs:
        raise SystemExit("Expected input.glb output.glb metadata.json")
    user=xs[xs.index("--")+1:]
    if len(user)!=3:
        raise SystemExit("Expected 3 args")
    return [os.path.abspath(x) for x in user]


def tube_mesh(points,radii_x,radii_y=None,sections=10):
    pts=np.asarray(points,dtype=float)
    rx=np.asarray(radii_x,dtype=float)
    ry=rx if radii_y is None else np.asarray(radii_y,dtype=float)
    n=len(pts)
    verts=[]
    for i,p in enumerate(pts):
        if i==0:
            tangent=pts[1]-pts[0]
        elif i==n-1:
            tangent=pts[-1]-pts[-2]
        else:
            tangent=pts[i+1]-pts[i-1]
        tangent=tangent/np.linalg.norm(tangent)
        e1=np.array([1.0,0.0,0.0])
        e1=e1-tangent*np.dot(e1,tangent)
        if np.linalg.norm(e1)<1e-8:
            e1=np.array([0.0,1.0,0.0])
            e1=e1-tangent*np.dot(e1,tangent)
        e1=e1/np.linalg.norm(e1)
        e2=np.cross(tangent,e1)
        e2=e2/np.linalg.norm(e2)
        for j in range(sections):
            a=2.0*math.pi*j/sections
            verts.append(p+e1*rx[i]*math.cos(a)+e2*ry[i]*math.sin(a))

    faces=[]
    for i in range(n-1):
        for j in range(sections):
            a=i*sections+j
            b=i*sections+(j+1)%sections
            c=(i+1)*sections+(j+1)%sections
            d=(i+1)*sections+j
            faces.append([a,b,c])
            faces.append([a,c,d])

    verts.append(pts[0]); c0=len(verts)-1
    verts.append(pts[-1]); c1=len(verts)-1
    for j in range(sections):
        faces.append([c0,(j+1)%sections,j])
        a=(n-1)*sections+j
        b=(n-1)*sections+(j+1)%sections
        faces.append([c1,a,b])

    return trimesh.Trimesh(
        vertices=np.asarray(verts),
        faces=np.asarray(faces),
        process=False
    )


def main():
    input_path,output_path,meta_path=args()
    os.makedirs(os.path.dirname(output_path),exist_ok=True)
    os.makedirs(os.path.dirname(meta_path),exist_ok=True)

    scene=trimesh.load(input_path,force="scene")
    if len(scene.geometry)!=1:
        raise RuntimeError(f"Expected one source geometry, got {len(scene.geometry)}")
    source=next(iter(scene.geometry.values())).copy()

    v=np.asarray(source.vertices).copy()
    f=np.asarray(source.faces).copy()
    original=v.copy()

    x_min,y_min,z_min=v.min(axis=0)
    x_max,y_max,z_max=v.max(axis=0)
    cx=(x_min+x_max)*0.5

    # The raw GLB coordinate system is verified directly:
    # X lateral, +Y head / -Y tail, Z vertical.
    body=(
        (v[:,1]>-0.27)&(v[:,1]<0.34)&
        (v[:,2]>-0.15)&(v[:,2]<0.48)
    )
    v[body,1]=0.03+(v[body,1]-0.03)*1.10
    v[body,0]=cx+(v[body,0]-cx)*0.92
    v[body,2]=0.18+(v[body,2]-0.18)*0.90

    belly=(
        (v[:,1]>-0.23)&(v[:,1]<0.29)&
        (v[:,2]>-0.18)&(v[:,2]<0.10)
    )
    factor=np.clip((0.10-v[belly,2])/0.28,0.0,1.0)
    v[belly,2]+=0.035*factor

    head=(
        (v[:,1]>0.25)&(v[:,1]<0.58)&
        (v[:,2]>0.43)&(v[:,2]<0.82)
    )
    hx=float(np.median(v[head,0]))
    hz=0.62
    v[head,0]=hx+(v[head,0]-hx)*0.86
    v[head,2]=hz+(v[head,2]-hz)*0.92

    # Remove legacy multi-prong crest and feather-fan tail by FACE,
    # not by squeezing their vertices into spikes.
    face_original=original[f]
    horn_a=(face_original[:,:,1]>0.49)&(face_original[:,:,2]>0.14)
    horn_b=(face_original[:,:,1]>0.12)&(face_original[:,:,2]>0.70)
    remove_horn=(horn_a.sum(axis=1)>=2)|(horn_b.sum(axis=1)>=2)

    tail_a=(face_original[:,:,1]<-0.30)&(face_original[:,:,2]>0.10)
    remove_tail=(tail_a.sum(axis=1)>=2)

    keep=~(remove_horn|remove_tail)
    body_mesh=trimesh.Trimesh(
        vertices=v,
        faces=f[keep],
        process=False,
        visual=source.visual
    )
    body_mesh.remove_unreferenced_vertices()

    crest=[]
    for side in (-1.0,1.0):
        x0=cx+side*0.052
        points=np.array([
            [x0,             0.41, 0.68],
            [x0+side*0.004, 0.32, 0.76],
            [x0+side*0.007, 0.21, 0.84],
            [x0+side*0.006, 0.09, 0.90],
            [x0+side*0.003,-0.04, 0.94],
        ])
        crest.append(tube_mesh(
            points,
            [0.032,0.026,0.019,0.012,0.0035],
            [0.046,0.038,0.028,0.017,0.0035],
            sections=10
        ))

    tail=tube_mesh(
        np.array([
            [cx,-0.28,0.28],
            [cx,-0.42,0.28],
            [cx,-0.58,0.26],
            [cx,-0.74,0.23],
            [cx,-0.90,0.19],
        ]),
        [0.034,0.027,0.020,0.012,0.003],
        [0.042,0.034,0.025,0.015,0.003],
        sections=10
    )

    out=trimesh.Scene()
    out.add_geometry(body_mesh,geom_name="S_body",node_name="S_body")
    out.add_geometry(crest[0],geom_name="S_crest_L",node_name="S_crest_L")
    out.add_geometry(crest[1],geom_name="S_crest_R",node_name="S_crest_R")
    out.add_geometry(tail,geom_name="S_tail",node_name="S_tail")
    out.export(output_path)

    meta={
        "status":"shape_refine_v12_direct_geometry_surgery_candidate_not_canonical",
        "source_vertices":int(len(original)),
        "source_faces":int(len(f)),
        "body_vertices_after_surgery":int(len(body_mesh.vertices)),
        "body_faces_after_surgery":int(len(body_mesh.faces)),
        "removed_horn_faces":int(remove_horn.sum()),
        "removed_tail_faces":int(remove_tail.sum()),
        "new_crest_count":2,
        "new_tail_count":1,
        "coordinate_basis":"raw_glb_x_lateral_y_head_tail_z_vertical",
        "source":os.path.basename(input_path),
        "output":os.path.basename(output_path)
    }
    with open(meta_path,"w",encoding="utf-8") as fh:
        import json
        json.dump(meta,fh,indent=2)

    if not os.path.exists(output_path) or os.path.getsize(output_path)<1024:
        raise RuntimeError("v12 GLB missing or too small")
    print("SHAPE_V12",meta)


if __name__=="__main__":
    main()
