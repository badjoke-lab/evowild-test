function fail(message) { throw Error(message); }
function checkSize(size) {
  if (!Array.isArray(size) || size.length!==2 || !size.every(n=>Number.isInteger(n)&&n>0)) fail('描画寸法が不正です');
  return size.join('×');
}
function frameRates(samples, expected) {
  if (!Array.isArray(samples)||samples.length!==expected) fail(expected+'フレーム必要です');
  const ms=samples.map(s=>s?.interval_ms);
  if (ms.some(n=>!Number.isFinite(n)||n<=0)) fail('フレーム時間が不正です');
  const sorted=[...ms].sort((a,b)=>a-b);
  return {fps:1000*ms.length/ms.reduce((sum,n)=>sum+n,0),p95:sorted[Math.ceil(.95*ms.length)-1]};
}
function rows(data) {
  const labels={device:data.device_label||'端末名なし',gpu:data.renderer||'GPU名なし',version:data.version};
  if(data.schema==='evowild-ridge-race/1'&&data.protocol==='ridge-oval-30hz-24warm-96raf-v1'){
    if(!['classic','v4.1'].includes(data.version)||!['mixed','s'].includes(data.field)||
       !['race','follow'].includes(data.camera)||![1,10,18,50,100].includes(data.count)||
       data.warmup!==24||Math.abs(data.step_ms-1000/30)>.00001||!Number.isFinite(data.step_ms))fail('レース条件が不正です');
    const rate=frameRates(data.samples,96);
    const streamed=data.samples.filter(s=>s.streaming||s.atlas_errors?.length).length;
    const key=['Ridge Oval',data.field==='s'?'Sのみ':'混走',data.count+'体',data.camera,
      checkSize(data.raster),data.mobile?'モバイル画角':'PC画角',data.antialias?'AA有':'AA無'].join(' ／ ');
    return [{...labels,version:labels.version+' ／ '+(data.integrated_build||'初回統合'),...rate,key,comparable:!streamed,note:streamed?'方位素材の読込・エラー '+streamed+'フレーム':''}];
  }
  if(data.schema_version===1&&['v4','v4.1'].includes(data.version)&&['desktop','mobile'].includes(data.profile)&&Array.isArray(data.rows)){
    if(data.rows.length!==2||new Set(data.rows.map(r=>r.scenario)).size!==2)fail('単体試験の2条件が必要です');
    return data.rows.map(r=>{
      if(!['mixed50','mixed100'].includes(r.scenario)||r.frames!==48||r.width!==data.raster?.width||r.height!==data.raster?.height)fail('単体試験の条件が不正です');
      const key=['v4.1単体デモ',r.scenario,checkSize([r.width,r.height]),data.profile,'1画素同期'].join(' ／ ');
      return {...labels,...frameRates(r.samples,48),key,comparable:true,note:''};
    });
  }
  fail('対応する実機計測JSONではありません');
}
const all=new Map(),errors=document.getElementById('errors'),groups=document.getElementById('groups');
const text=(tag,content)=>{const e=document.createElement(tag);e.textContent=content;return e;};
function render(){
  groups.replaceChildren();const grouped=new Map();
  for(const records of all.values())for(const r of records){
    if(!grouped.has(r.key))grouped.set(r.key,[]);grouped.get(r.key).push(r);
  }
  for(const [key,records] of grouped){
    groups.append(text('h2',key));
    const scroller=text('div','');scroller.className='scroll';
    const table=document.createElement('table'),head=table.createTHead().insertRow(),body=table.createTBody();
    for(const label of ['端末／ファイル','表示','平均FPS','p95 ms','Δ FPS','Δ p95 ms'])head.append(text('th',label));
    const base=records.find(r=>r.comparable);
    for(const r of records){
      const tr=body.insertRow(),device=tr.insertCell();device.textContent=r.device;
      device.append(text('small',r.file),text('small',r.gpu));
      if(r.note)device.append(text('small',r.note));
      for(const v of [r.version,r.fps.toFixed(2),r.p95.toFixed(2),
        r.comparable?(r.fps-base.fps).toFixed(2):'—',r.comparable?(r.p95-base.p95).toFixed(2):'—'])tr.insertCell().textContent=v;
    }
    scroller.append(table);groups.append(scroller);
  }
}
let generation=0;
document.getElementById('files').onchange=async e=>{
  const token=generation,files=Array.from(e.target.files);
  e.target.value='';
  for(const f of files){
    try{
      if(f.size>12*1024*1024)fail('12 MiB以下のJSONを選択してください');
      const content=await f.text();if(token!==generation)return;
      const records=rows(JSON.parse(content));
      all.set(content,records.map(r=>({...r,file:f.name})));
    }catch(err){if(token===generation)errors.append(text('p',f.name+' ｜ '+err.message));}
  }
  render();
};
document.getElementById('clear').onclick=()=>{generation++;all.clear();errors.replaceChildren();render();};
