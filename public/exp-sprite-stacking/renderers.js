export class StackAssets{
 constructor(manifest){this.manifest=manifest;this.images=new Map();this.bytes=0;this.decodedBytes=0;this.draws=0;this.key='';}
 async load(layers,frames){const key=`${layers}/${frames}`;if(this.key===key)return;this.dispose();this.key=key;const step=48/frames;
  const list=this.manifest.atlases.filter(a=>a.layers===layers&&a.frame%step===0);await Promise.all(list.map(async a=>{const response=await fetch(`assets/${a.file}`);if(!response.ok)throw Error('Atlas missing '+a.file);const blob=await response.blob(),image=await createImageBitmap(blob);if(this.key!==key){image.close();return;}this.images.set(a.frame,{...a,image});this.bytes+=blob.size;this.decodedBytes+=a.width*a.height*4;}));
 }
 dispose(){this.key='';for(const a of this.images.values())a.image.close();this.images.clear();this.bytes=0;this.decodedBytes=0;}
}
export function projected(v,camera){const dx=v.x-camera.x,dz=v.z-camera.z;return {x:camera.w/2+(camera.cos*dx-camera.sin*dz)*camera.scale,y:camera.h*.65+((camera.sin*dx+camera.cos*dz)*camera.se-(v.y||0)*camera.ce)*camera.scale};}
export function sliceTransform(entity,camera,height,ppu){const a=entity.heading-camera.az,co=Math.cos(a),si=Math.sin(a),k=camera.scale/ppu,base=projected(entity,camera);return [k*co,-k*camera.se*si,k*si,k*camera.se*co,base.x,base.y-height*camera.ce*camera.scale];}
export function drawStack(ctx,assets,entity,camera,frame){const atlas=assets.images.get(frame);if(!atlas)return 0;const m=assets.manifest;let count=0;
 for(let i=0;i<atlas.layers;i++){const r=atlas.rects[i];if(r[2]<=1&&r[3]<=1)continue;const [a,b,c,d,e,f]=sliceTransform(entity,camera,(i+.5)*m.height/atlas.layers,m.pixelsPerUnit),x=r[4]-m.tileSize/2,y=r[5]-m.tileSize/2;
  ctx.setTransform(a,b,c,d,e+a*x+c*y,f+b*x+d*y);ctx.drawImage(atlas.image,r[0],r[1],r[2],r[3],0,0,r[2],r[3]);count++;
 }ctx.resetTransform();return count;
}
export class SpriteAssets{
 constructor(){this.images=new Map();this.decodedBytes=0;this.bytes=0;}
 async load(frames){if(this.frames===frames)return;this.dispose();this.frames=frames;const key=frames;const response=await fetch('assets/sprite-manifest.json');if(!response.ok)throw Error('2D comparison assets are not baked');this.manifest=await response.json();await Promise.all(Array.from({length:frames},async(_,i)=>{const frame=i*48/frames;const r=await fetch(`assets/sprite/${String(frame).padStart(2,'0')}.png`),b=await r.blob(),image=await createImageBitmap(b);if(this.frames!==key){image.close();return;}this.images.set(frame,image);this.bytes+=b.size;this.decodedBytes+=image.width*image.height*4;}));}
 dispose(){for(const i of this.images.values())i.close();this.images.clear();this.bytes=0;this.decodedBytes=0;this.frames=0;}
 draw(ctx,entity,camera,frame){const image=this.images.get(frame);if(!image)return 0;const m=this.manifest,heading=((entity.heading-camera.az)%(Math.PI*2)+Math.PI*2)%(Math.PI*2),index=Math.round(heading/(Math.PI*2)*m.directions)%m.directions;
 const p=projected(entity,camera),k=camera.scale/m.pixelsPerUnit;ctx.drawImage(image,index%4*m.size,Math.floor(index/4)*m.size,m.size,m.size,p.x-m.size*.5*k,p.y-m.size*.65*k,m.size*k,m.size*k);return 1;}
}
export class WebGLSlices{
 constructor(){this.canvas=document.createElement('canvas');const gl=this.gl=this.canvas.getContext('webgl',{alpha:true,premultipliedAlpha:true,antialias:false});if(!gl)throw Error('WebGL unavailable');
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.program=gl.createProgram();gl.attachShader(this.program,shader(gl.VERTEX_SHADER,'attribute vec2 p;attribute vec2 uv;varying vec2 v;void main(){v=uv;gl_Position=vec4(p,0.,1.);}'));gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,'precision mediump float;varying vec2 v;uniform sampler2D tex;void main(){gl_FragColor=texture2D(tex,v);}'));gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error('Slice shader link failed');this.buffer=gl.createBuffer();this.textures=new Map();
  this.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.lost=true;});this.canvas.addEventListener('webglcontextrestored',()=>{this.lost=true;});
 }
 resetTextures(){for(const t of this.textures.values())this.gl.deleteTexture(t);this.textures.clear();}
 render(assets,entities,camera,frameFor){if(this.lost)throw Error('WebGL context lost; select Canvas to recover');const gl=this.gl;if(this.key!==assets.key){this.resetTextures();this.key=assets.key;}
  if(this.canvas.width!==camera.w||this.canvas.height!==camera.h){this.canvas.width=camera.w;this.canvas.height=camera.h;}gl.viewport(0,0,camera.w,camera.h);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);gl.useProgram(this.program);gl.enable(gl.BLEND);gl.blendFuncSeparate(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA,gl.ONE,gl.ONE_MINUS_SRC_ALPHA);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
  const pl=gl.getAttribLocation(this.program,'p'),ul=gl.getAttribLocation(this.program,'uv');gl.enableVertexAttribArray(pl);gl.enableVertexAttribArray(ul);gl.vertexAttribPointer(pl,2,gl.FLOAT,false,16,0);gl.vertexAttribPointer(ul,2,gl.FLOAT,false,16,8);let calls=0;
  for(const entity of entities){const atlas=assets.images.get(frameFor(entity));if(!atlas)continue;let texture=this.textures.get(atlas.frame);if(!texture){texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,atlas.image);this.textures.set(atlas.frame,texture);}gl.bindTexture(gl.TEXTURE_2D,texture);
   const vertices=[],m=assets.manifest;for(let i=0;i<atlas.layers;i++){const r=atlas.rects[i];if(r[2]<=1&&r[3]<=1)continue;const [a,b,c,d,e,f]=sliceTransform(entity,camera,(i+.5)*m.height/atlas.layers,m.pixelsPerUnit);
    for(const [u,v]of [[0,0],[1,0],[0,1],[0,1],[1,0],[1,1]]){const x=r[4]-m.tileSize/2+u*r[2],y=r[5]-m.tileSize/2+v*r[3];vertices.push((e+a*x+c*y)/camera.w*2-1,1-(f+b*x+d*y)/camera.h*2,(r[0]+u*r[2])/atlas.width,(r[1]+v*r[3])/atlas.height);}}
   gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STREAM_DRAW);gl.drawArrays(gl.TRIANGLES,0,vertices.length/4);calls++;
  }return {canvas:this.canvas,calls};
 }
}
