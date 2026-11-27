// Regression for shared WebGL state when the existing race advances during I/O.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {launch,fixedClock,ready} from '../race-integration/browser.mjs';
const [origin,file]=process.argv.slice(2),browser=await launch(),results=[];
try{
 for(const mode of ['base','group','color','both']){
  const page=await browser.newPage({viewport:{width:1100,height:745}});
  await page.addInitScript(fixedClock);
  await page.addInitScript(()=>{
    const prototype=WebGL2RenderingContext.prototype,create=prototype.createVertexArray,arrays=[];
    prototype.createVertexArray=function(){const vao=create.call(this);arrays.push(vao);return vao;};
    window.inspectRaceArrays=()=>{
      const gl=document.querySelector('#game').getContext('webgl2'),previous=gl.getParameter(gl.VERTEX_ARRAY_BINDING);
      const states=arrays.map(vao=>{
        if(!gl.isVertexArray(vao))return null;
        gl.bindVertexArray(vao);
        const attrs=Array.from({length:gl.getParameter(gl.MAX_VERTEX_ATTRIBS)},(_,i)=>
          [gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_BUFFER_BINDING),
           gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_ENABLED),gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_SIZE),
           gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_TYPE),gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_STRIDE),
           gl.getVertexAttrib(i,gl.VERTEX_ATTRIB_ARRAY_DIVISOR),gl.getVertexAttribOffset(i,gl.VERTEX_ATTRIB_ARRAY_POINTER)]);
        return {ibo:gl.getParameter(gl.ELEMENT_ARRAY_BUFFER_BINDING),attrs};
      });
      gl.bindVertexArray(previous);return states;
    };
  });
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/paint.gz',async route=>{
    const response=await route.fetch();await new Promise(r=>setTimeout(r,500));await route.fulfill({response});
  });
  await page.goto(origin+'/'+mode+'/evowild-test/?raceTrial=1&verify=1&field=s&count=10&look=classic');
  await ready(page);
  await page.evaluate(()=>{tickRace(3);window.initialArrays=inspectRaceArrays();window.raceLoadInterval=setInterval(()=>tickRace(),30);});
  await page.selectOption('#trial-mode','pixel');await ready(page,true);
  const result=await page.evaluate(()=>{
    clearInterval(raceLoadInterval);tickRace();
    const later=inspectRaceArrays();
    const same=initialArrays.every((a,i)=>a===null||a.ibo===later[i].ibo&&
      a.attrs.every((attr,k)=>attr.every((value,j)=>value===later[i].attrs[k][j])));
    const differences=initialArrays.flatMap((a,i)=>{
      if(!a)return [];
      const b=later[i],list=[];
      if(a.ibo!==b.ibo)list.push({vao:i,field:'indices'});
      a.attrs.forEach((v,k)=>v.forEach((x,j)=>{if(x!==b.attrs[k][j])list.push({vao:i,attribute:k,field:j,before:String(x),after:String(b.attrs[k][j])});}));
      return list;
    });
    return {differences,existing_arrays:initialArrays.filter(Boolean).length,unchanged:same,elapsed_ms:raceSnapshot().elapsed_ms,
      gl:document.querySelector('#game').getContext('webgl2').getError()};
  });
  console.log(mode,JSON.stringify(result));
  assert.equal(result.unchanged,true,mode+' modified an existing geometry VAO');
  assert.equal(result.gl,0);assert.deepEqual(errors,[]);results.push({mode,...result});
  await page.close();
 }
 await fs.writeFile(file,JSON.stringify(results,null,2)+'\n');console.log('All four modes preserve existing geometry while loading during race updates.');
}finally{await browser.close();}
