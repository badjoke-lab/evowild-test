// Only the flat, constant-material Ridge Oval ground uses this lookup. Its
// normal and lights are fixed, so the original BRDF varies with eye direction
// alone. Bake it with Three's own shaders, preserving near/far fog per pixel.
import * as THREE from 'three';

export function prepareRidgeGround(renderer,ground,lights){
  const size=128;
  const target=new THREE.WebGLRenderTarget(size,size,{depthBuffer:false,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter});
  const original=ground.material;
  function bake(){
    const scene=new THREE.Scene();
    for(const light of lights)scene.add(light.clone());
    const geometry=new THREE.PlaneGeometry(2,2);
    for(let i=0;i<4;i++)geometry.attributes.normal.setXYZ(i,0,1,0);
    const material=original.clone();
    material.fog=false;
    material.onBeforeCompile=shader=>{
      const direction=`
        vec2 uv=(gl_FragCoord.xy/float(${size})*2.-1.);
        vec3 geometryViewDir=normalize(vec3((uv.x+uv.y)*.5,1.-max(abs(uv.x),abs(uv.y)),(uv.x-uv.y)*.5));`;
      const lightChunk=THREE.ShaderChunk.lights_fragment_begin.replace(/vec3 geometryViewDir = [^;]+;/,direction);
      shader.fragmentShader=THREE.ShaderChunk.tonemapping_pars_fragment+'\n'+shader.fragmentShader
        .replace('#include <lights_fragment_begin>',lightChunk)
        .replace('#include <tonemapping_fragment>','gl_FragColor.rgb=ACESFilmicToneMapping(gl_FragColor.rgb);')
        .replace('#include <colorspace_fragment>','gl_FragColor=sRGBTransferOETF(gl_FragColor);');
    };
    scene.add(new THREE.Mesh(geometry,material));
    const camera=new THREE.OrthographicCamera(-1,1,1,-1,.1,2);
    camera.position.z=1;
    const previous=renderer.getRenderTarget();
    try{renderer.setRenderTarget(target);renderer.render(scene,camera);}
    finally{renderer.setRenderTarget(previous);geometry.dispose();material.dispose();}
  }
  bake();
  const uniforms=THREE.UniformsUtils.clone(THREE.UniformsLib.fog);
  uniforms.groundLight={value:target.texture};
  ground.material=new THREE.ShaderMaterial({uniforms,fog:true,toneMapped:false,
    vertexShader:`
      varying highp vec3 toEye;
      #include <fog_pars_vertex>
      void main(){
        #include <begin_vertex>
        #include <project_vertex>
        toEye=cameraPosition-(modelMatrix*vec4(position,1.)).xyz;
        #include <fog_vertex>
      }`,
    fragmentShader:`
      uniform sampler2D groundLight;
      varying highp vec3 toEye;
      #include <fog_pars_fragment>
      void main(){
        highp vec2 p=toEye.xz/dot(abs(toEye),vec3(1.));
        gl_FragColor=texture2D(groundLight,vec2(p.x+p.y,p.x-p.y)*.5+.5);
        #include <fog_fragment>
      }`
  });
  renderer.domElement.addEventListener('webglcontextrestored',bake);
}
