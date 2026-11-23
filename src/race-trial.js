// Opt-in adapter for the Ridge Oval game. No references are written back to a racer.
const query = new URLSearchParams(location.search);
export const trialEnabled = query.get('raceTrial') === '1';
const counts = [1, 10, 18, 50, 100];
export const fieldSize = trialEnabled && counts.includes(Number(query.get('count'))) ? Number(query.get('count')) : 18;
export const sprintField = trialEnabled && query.get('field') === 's';
const byId = id => document.getElementById(id);
const root = new URL(import.meta.env.BASE_URL, document.baseURI);
const verify = query.get('verify') === '1';
const warmup = 24, samples = 96;

export function createTrial({THREE, renderer, racers, mobile, restart, status}) {
  const panel = byId('race-trial');
  panel.hidden = false;
  const count = byId('trial-count'), field = byId('trial-field'), mode = byId('trial-mode');
  count.value = String(fieldSize); field.value = sprintField ? 's' : 'mixed';
  mode.value = query.get('look') === 'classic' ? 'classic' : 'pixel';
  byId('trial-apply').onclick = () => {
    const next = new URL(location.href);
    for (const [k,v] of [['count',count.value],['field',field.value],['look',mode.value]]) next.searchParams.set(k,v);
    location.assign(next);
  };

  let actors, loading, loadError, generation = 0, lastDraw = null;
  let run = null, saved = null, lastRAF = null, recent = [];
  const travel = new Map(), previous = new Map();
  const sCount = racers.filter(r=>r.morph==='S').length;
  const gpu = () => {
    const gl=renderer.getContext(), ext=gl.getExtension('WEBGL_debug_renderer_info');
    return gl.getParameter(ext?ext.UNMASKED_RENDERER_WEBGL:gl.RENDERER);
  };
  function controls() {
    byId('trial-measure').disabled = !!run || (mode.value==='pixel' && !actors);
    byId('trial-save').disabled = !saved;
    byId('trial-cancel').hidden = !run;
    for (const element of [mode, count, field, byId('trial-apply'), byId('trial-device')]) element.disabled=!!run;
  }
  function cancel(reason) {
    if (!run) return;
    run=null;
    controls();
    byId('trial-note').textContent=reason;
  }
  async function load() {
    if (actors || loading || mode.value!=='pixel') return;
    const token = generation;
    loading = true; loadError=null; controls();
    byId('trial-note').textContent='v4.1 を読込中。従来表示で走行しています。';
    try {
      const {loadActors} = await import(/* @vite-ignore */ new URL('race-integration/actors.js',root).href);
      const draw = await loadActors(THREE,renderer,racers);
      if(token===generation) {
        actors=draw;
        byId('trial-note').textContent='走行中も表示を切り替えられます。';
      }
    } catch(error) {
      if(token===generation) {
        loadError=String(error.message); mode.value='classic';
        byId('trial-note').textContent='従来表示で継続。v4.1 読込エラー '+loadError;
      }
    } finally {
      if(token===generation){loading=false;controls();}
    }
  }
  mode.onchange=()=>{ recent=[];lastRAF=null;lastDraw=null;load();controls(); };
  renderer.domElement.addEventListener('webglcontextlost',()=>{
    generation++; actors=null; loading=false; cancel('コンテキスト消失のため中断しました。');controls();
  });
  renderer.domElement.addEventListener('webglcontextrestored',load);
  document.addEventListener('visibilitychange',()=>{
    recent=[];lastRAF=null;
    if(document.hidden) cancel('タブが非表示になったため中断しました。');
  });
  byId('trial-cancel').onclick=()=>cancel('測定を中断しました。');
  byId('trial-measure').onclick=()=>{
    const {view}=status();
    if(view!=='race' && view!=='follow'){
      byId('trial-note').textContent='Race または Follow カメラを選択してください。';return;
    }
    restart();
    const c=renderer.domElement;
    saved=null;
    run={schema:'evowild-ridge-race/1',protocol:'ridge-oval-30hz-24warm-96raf-v1',
      started_at:new Date().toISOString(),device_label:byId('trial-device').value,renderer:gpu(),
      user_agent:navigator.userAgent,dpr:devicePixelRatio,raster:[c.width,c.height],mobile,
      version:mode.value==='classic'?'classic':'v4.1',camera:view,count:racers.length,s_count:sCount,
      field:sprintField?'s':'mixed',antialias:renderer.getContext().getContextAttributes().antialias,
      warmup,step_ms:1000/30,samples:[],frame:0,previous:null};
    controls();byId('trial-note').textContent='予熱中…';
  };
  byId('trial-save').onclick=()=>{
    if(!saved)return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(saved)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='ridge-'+saved.version+'-'+saved.count+'-'+saved.started_at.replace(/[:.]/g,'-')+'.json';
    a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
  };
  function resetTravel(){
    previous.clear();travel.clear();
    for (const r of racers) if(r.morph==='S'){
      previous.set(r.id,[r.obj.position.x,r.obj.position.z]);travel.set(r.id,0);
    }
  }
  resetTravel(); controls(); load();
  function rates(intervals){
    const sorted=[...intervals].sort((a,b)=>a-b);
    return {fps:intervals.length*1000/intervals.reduce((a,b)=>a+b,0),p95_ms:sorted[Math.ceil(.95*sorted.length)-1]};
  }
  return {
    get active(){return !!actors && mode.value==='pixel';},
    get step(){return run?.step_ms;},
    resetTravel, cancel,
    sync(){
      for(const r of racers) {
        if(r.morph!=='S')continue;
        const old=previous.get(r.id),p=r.obj.position, y=r.obj.rotation.y;
        const forward=(p.x-old[0])*Math.cos(y)-(p.z-old[1])*Math.sin(y);
        travel.set(r.id,travel.get(r.id)+Math.max(0,forward)); old[0]=p.x;old[1]=p.z;
      }
    },
    draw(camera,view){
      lastDraw=null;
      if(this.active && (view==='race'||view==='follow')){
        try{ lastDraw=actors(camera,travel,verify); }
        catch(error){
          mode.value='classic'; loadError=String(error.message);
          cancel('描画エラーのため中断しました。');
          byId('trial-note').textContent='従来表示に復帰しました。 '+loadError;
          controls();
        }
      }
    },
    frame(now,view){
      const dt=lastRAF===null?null:now-lastRAF;
      lastRAF=now;
      if(dt>0){recent.push(dt);if(recent.length>48)recent.shift();}
      if(run){
        const c=renderer.domElement;
        if(run.raster[0]!==c.width||run.raster[1]!==c.height||document.hidden||view!==run.camera){
          cancel('画面条件が変化したため中断しました。');return;
        }
        if(run.frame>=warmup && now>run.previous)run.samples.push({interval_ms:now-run.previous,
          ...status(),lod:lastDraw?.mix??null,streaming:lastDraw?.atlasPending??false,atlas_errors:lastDraw?.atlasErrors??[]});
        run.frame++;run.previous=now;
        if(run.samples.length===samples){
          const intervals=run.samples.map(s=>s.interval_ms);
          const {frame,previous,...exported}=run;
          saved={...exported,...rates(intervals)};run=null;controls();
          byId('trial-note').textContent='測定完了　'+saved.fps.toFixed(1)+' fps ／ p95 '+saved.p95_ms.toFixed(1)+' ms。JSONを保存できます。';
        }else if(run.frame%6===0)byId('trial-note').textContent='測定中　'+run.samples.length+' / '+samples;
      }
      if(recent.length && !(Math.floor(now/240)===Math.floor((now-(dt||0))/240))){
        const t=rates(recent),m=lastDraw?.mix;
        const summary=m?'近 '+(m.fine+m.race)+' ／ 中 '+m.mid+' ／ 移行 '+m.transition+' ／ 遠 '+m.sprite+' ／ 画角外 '+m.outside:'';
        byId('trial-hud').textContent=t.fps.toFixed(1)+' fps ・ p95 '+t.p95_ms.toFixed(1)+' ms ・ 出走 '+racers.length+'（S '+sCount+'） '+summary+(lastDraw?.atlasErrors.length?' 方位素材読込エラー':'');
      }
      panel.dataset.renderer=this.active?'pixel':'classic';
    },
    inspect(){return {ready:!!actors,mode:mode.value,error:loadError,draw:lastDraw,travel:[...travel.values()]};}
  };
}
