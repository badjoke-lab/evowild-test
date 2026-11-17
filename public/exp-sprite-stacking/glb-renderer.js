import * as THREE from 'three';
import {GLTFLoader} from './vendor/GLTFLoader.js';
import {clone} from './vendor/SkeletonUtils.js';
import {preparePose} from './runtime/pose.js';
export class GLBRenderer{
 async init(){const [gltf,tracks]=await Promise.all([new GLTFLoader().loadAsync('assets/source.glb'),fetch('assets/pose-tracks.json').then(r=>r.json())]);this.tracks=tracks;this.template=preparePose(gltf);this.template.localize();this.scene=new THREE.Scene();this.instances=[];
  this.material=new THREE.ShaderMaterial({vertexShader:`#include <common>
#include <skinning_pars_vertex>
varying float vLight;
void main(){
#include <beginnormal_vertex>
#include <skinbase_vertex>
#include <skinnormal_vertex>
vLight=.28+.72*max(0.,dot(normalize(objectNormal),normalize(vec3(.4,.85,.35))));
#include <begin_vertex>
#include <skinning_vertex>
gl_Position=projectionMatrix*modelViewMatrix*vec4(transformed,1.);
}`,fragmentShader:`varying float vLight;void main(){gl_FragColor=vec4(vec3(vLight),1.);
#include <colorspace_fragment>
}`});
  this.renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,preserveDrawingBuffer:true});this.renderer.setPixelRatio(1);this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.setClearColor(0,0);this.camera=new THREE.OrthographicCamera();return this;
 }
 ensure(count){while(this.instances.length<count){const object=clone(this.template.root);const nodes=new Map();object.traverse(n=>{nodes.set(n.name,n);if(n.isMesh){n.material=this.material;n.frustumCulled=false;}});this.scene.add(object);this.instances.push({object,nodes});}}
 render(entities,c,frameFor){this.ensure(entities.length);this.instances.forEach((ins,i)=>{ins.object.visible=i<entities.length;if(i>=entities.length)return;const e=entities[i];for(const [name,t]of Object.entries(this.tracks[frameFor(e)])){const node=ins.nodes.get(name);node.position.fromArray(t.p);node.quaternion.fromArray(t.q);node.scale.fromArray(t.s);}ins.object.position.set(e.x,0,e.z);ins.object.rotation.y=e.heading;});
  this.camera.left=-c.w/2/c.scale;this.camera.right=c.w/2/c.scale;this.camera.top=c.h*.65/c.scale;this.camera.bottom=-c.h*.35/c.scale;this.camera.near=.1;this.camera.far=500;
  this.camera.position.set(c.x+c.sin*c.ce*100,c.se*100,c.z+c.cos*c.ce*100);this.camera.up.set(0,1,0);this.camera.lookAt(c.x,0,c.z);this.camera.updateProjectionMatrix();
  if(this.renderer.domElement.width!==c.w||this.renderer.domElement.height!==c.h)this.renderer.setSize(c.w,c.h,false);this.renderer.render(this.scene,this.camera);return {canvas:this.renderer.domElement,calls:this.renderer.info.render.calls,triangles:this.renderer.info.render.triangles};
 }
}
