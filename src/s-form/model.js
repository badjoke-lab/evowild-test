import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const assetRoot = new URL('s-form/', new URL(import.meta.env.BASE_URL, location.origin));
export async function loadForm() {
  const [gltf, meta] = await Promise.all([
    new GLTFLoader().loadAsync(new URL('s-form.glb', assetRoot).href),
    fetch(new URL('anatomy.json', assetRoot)).then(r=>r.json())
  ]);
  const geometries=[];
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(object=>{
    if(!object.isMesh)return;
    const g=object.geometry.clone();
    // Exported primitive transforms are identical. Preserve morph coordinates.
    g.applyMatrix4(object.matrixWorld);
    for(const attr of [...(g.morphAttributes.position||[]),...(g.morphAttributes.normal||[])]) {
      for(let i=0;i<attr.count;i++) {
        const v=new THREE.Vector3().fromBufferAttribute(attr,i);
        if(g.morphTargetsRelative)v.applyMatrix3(new THREE.Matrix3().setFromMatrix4(object.matrixWorld));
        else v.applyMatrix4(object.matrixWorld);
        attr.setXYZ(i,v.x,v.y,v.z);
      }
    }
    const color=object.material.color;
    const colors=new Float32Array(g.attributes.position.count*3);
    for(let i=0;i<colors.length;i+=3)colors.set([color.r,color.g,color.b],i);
    g.setAttribute('color',new THREE.BufferAttribute(colors,3));
    geometries.push(g);
  });
  const geometry=mergeGeometries(geometries);
  geometry.morphTargetsRelative=geometries[0].morphTargetsRelative;
  const material=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.85,metalness:0});
  const create=()=>{
    const mesh=new THREE.Mesh(geometry,material);
    mesh.frustumCulled=false;mesh.name='S anatomical study';
    return mesh;
  };
  return {create,meta,geometry,material};
}

export function setPose(mesh, tick) {
  mesh.morphTargetInfluences.fill(0);
  if(tick<0)return;
  const a=((Math.floor(tick)%24)+24)%24, f=tick-Math.floor(tick);
  mesh.morphTargetInfluences[a]=1-f;
  mesh.morphTargetInfluences[(a+1)%24]=f;
}

export function addLight(scene) {
  scene.add(new THREE.HemisphereLight(0xe9f3ff,0x738298,2.0));
  const key=new THREE.DirectionalLight(0xfff4e3,2.5);key.position.set(-3,6,4);scene.add(key);
  const fill=new THREE.DirectionalLight(0x9cb9e5,.7);fill.position.set(2,3,-4);scene.add(fill);
}
