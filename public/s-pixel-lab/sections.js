// A worker builds the visible faces of each contiguous horizontal band directly
// from the indexed PNG. Every face belongs to a texel in the selected stack.
let meta;
const data = new Map();
self.onmessage = async ({data: job}) => {
  try {
    if (job.meta) meta = job.meta;
    const {count, pose} = job;
    const p = meta.poses[pose];
    const url = './assets/stack-' + count + '/' + p.name + '.png';
    const req = await fetch(url);
    if (!req.ok) throw Error(url + ' ' + req.status);
    const bitmap = await createImageBitmap(await req.blob(), {colorSpaceConversion:'none'});
    const canvas = new OffscreenCanvas(bitmap.width, bitmap.height);
    const ctx = canvas.getContext('2d', {willReadFrequently:true});
    ctx.drawImage(bitmap,0,0);
    const rgba = ctx.getImageData(0,0,canvas.width,canvas.height).data;
    bitmap.close();
    if (!data.size) meta.palette.forEach((c,i)=>data.set(parseInt(c.slice(1),16),i));
    const {nx,nz} = meta;
    const dims = [nx,count,nz];
    const steps = [1,nx,nx*count];
    const cells = new Uint8Array(nx*nz*count);
    p.stacks[count].forEach(([x,z,w,h,u,v],y)=>{
      for(let j=0;j<h;j++) for(let i=0;i<w;i++) {
        const pix = 4*((v+j)*canvas.width+u+i);
        if(rgba[pix+3]) cells[x+i+y*nx+(z+j)*steps[2]]=data.get((rgba[pix]<<16)|(rgba[pix+1]<<8)|rgba[pix+2]);
      }
    });
    const vertices=[], indices=[];
    // Greedy rectangles merge adjacent coplanar faces only when their paint matches.
    for(let axis=0;axis<3;axis++){
      const u=(axis+1)%3,v=(axis+2)%3, w=dims[u], h=dims[v];
      const mask=new Int16Array(w*h);
      for(let k=0;k<=dims[axis];k++){
        let j=0;
        for(let y=0;y<h;y++){
          let pos=k*steps[axis]+y*steps[v];
          for(let x=0;x<w;x++,j++,pos+=steps[u]){
            const a=k?cells[pos-steps[axis]]:0, b=k<dims[axis]?cells[pos]:0;
            mask[j]=a&&!b?a:b&&!a?-b:0;
          }
        }
        for(let y=0;y<h;y++) for(let x=0;x<w;){
          const ix=x+w*y, c=mask[ix];
          if(!c){x++;continue;}
          let dw=1,dh=1;
          while(x+dw<w && mask[ix+dw]===c) dw++;
          height: while(y+dh<h) {
            for(let n=0;n<dw;n++) if(mask[ix+dh*w+n]!==c) break height;
            dh++;
          }
          const start=vertices.length/4, tag=Math.abs(c)*8+axis*2+(c>0?1:0);
          for(const [i,j] of [[0,0],[dw,0],[dw,dh],[0,dh]]){
            const pt=[0,0,0];pt[axis]=k;pt[u]=x+i;pt[v]=y+j;
            vertices.push(...pt,tag);
          }
          if(c>0)indices.push(start,start+1,start+2,start,start+2,start+3);
          else indices.push(start,start+2,start+1,start,start+3,start+2);
          for(let n=0;n<dh;n++) mask.fill(0,ix+w*n,ix+w*n+dw);
          x+=dw;
        }
      }
    }
    const verts=Uint16Array.from(vertices), elements=Uint32Array.from(indices);
    self.postMessage({count,pose,verts,elements},[verts.buffer,elements.buffer]);
  } catch(e){self.postMessage({error:String(e)});}
};
