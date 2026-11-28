import {loadForm,setPose,addLight} from './model.js';

// View-only adapter. The simulation's racers, camera, course and collision data
// are read here and are never modified. Original S renderers remain separate.
export async function loadActors(THREE,renderer,racers) {
  const asset=await loadForm(), scene=new THREE.Scene();addLight(scene);
  const runners=racers.filter(r=>r.morph==='S').map(r=>{
    const mesh=asset.create();scene.add(mesh);return {r,mesh};
  });
  const frustum=new THREE.Frustum(),vp=new THREE.Matrix4(),sphere=new THREE.Sphere();
  return function draw(camera,travel,inspect=false){
    vp.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);frustum.setFromProjectionMatrix(vp);
    const mix={fine:0,race:0,mid:0,transition:0,sprite:0,outside:0},details=[];
    for(const {r,mesh} of runners){
      const scale=r.obj.scale.x*4.65/700*200;
      mesh.scale.setScalar(scale);mesh.position.set(r.obj.position.x,.034,r.obj.position.z);
      mesh.rotation.y=r.obj.rotation.y+Math.PI;
      const tick=travel.get(r.id)/(scale*asset.meta.stride)*24+(r.id-1)*7;
      setPose(mesh,r.speed>0?tick:-1);
      sphere.center.copy(mesh.position);sphere.center.y+=1.1*scale;sphere.radius=2.5*scale;
      mesh.visible=frustum.intersectsSphere(sphere);mix[mesh.visible?'fine':'outside']++;
      if(inspect&&mesh.visible){
        const phase=Math.floor(tick)%24;
        const feet=r.speed>0?asset.meta.poses[phase].feet:null;
        details.push({id:r.id,pose:r.speed>0?phase+1:0,fraction:tick-Math.floor(tick),lod:'form',
          direction:[Math.cos(r.obj.rotation.y),-Math.sin(r.obj.rotation.y)],
          base:mesh.position.toArray(),feet:feet?Object.values(feet).reduce((n,f,i)=>n|(Number(f.contact)<<i),0):0});
      }
    }
    const clear=renderer.autoClear;
    try{renderer.autoClear=false;renderer.render(scene,camera);}finally{renderer.autoClear=clear;}
    return {mix,details,atlasPending:false,atlasErrors:[],form:'anatomical-study-20261128',
      note:'New mesh at every distance for visual review; no new LOD or performance claim'};
  };
}
