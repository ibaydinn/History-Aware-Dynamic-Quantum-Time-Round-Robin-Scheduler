'use strict';
(() => {
 const $=id=>document.getElementById(id);
 let runs=[],loading=false;
 function sync() {
  const end=Math.max(1,...runs.map(r=>r.viewer.getExtent()));
  const taskNames=[...new Set(runs.flatMap(r=>r.data.task_definitions.map(t=>t.name)))].sort();
  const duration=Math.max(1,Math.min(end,Number($('zoom').value)));
  const start=Math.max(0,Math.min(end-duration,Number($('pan').value)));
  Object.assign($('zoom'),{max:end,value:duration,disabled:!runs.length});
  Object.assign($('pan'),{max:end-duration,value:start,disabled:!runs.length});
  $('duration').textContent=duration+' units';$('range').textContent=`${start}–${start+duration}`;
  $('empty').hidden=!!runs.length;$('clear').disabled=loading||!runs.length;
  const hashes=new Set(runs.map(r=>r.data.task_input_hash).filter(Boolean));
  $('notice').textContent=hashes.size>1?'Input hashes differ: these simulations use different task inputs.':runs.length>1&&runs.some(r=>!r.data.task_input_hash)?'Some inputs have no hash; identical task inputs cannot be verified.':'';
  for(const run of runs)run.viewer.setView({start,duration,end,taskNames,starts:$('starts').checked,deadlines:$('deadlines').checked});
 }
 $('load').addEventListener('click',()=>$('files').click());
 $('files').addEventListener('change',async()=>{
  if(loading)return;loading=true;$('load').disabled=true;sync();
  const errors=[],wasEmpty=!runs.length;
  for(const file of [...$('files').files]){
   let panel,viewer;
   try{
    const data=JSON.parse(await file.text());
    panel=document.createElement('section');
    const heading=document.createElement('div');heading.className='heading';
    const title=document.createElement('span');title.textContent=data.scheduler?.name||file.name;title.title=file.name;heading.appendChild(title);
    const menu=document.createElement('details');menu.className='run-menu';
    const summary=document.createElement('summary');summary.textContent='Options';menu.appendChild(summary);
    const actions=document.createElement('div');actions.className='run-actions';menu.appendChild(actions);
    const remove=document.createElement('button');remove.textContent='Remove';actions.appendChild(remove);
    heading.appendChild(menu);panel.appendChild(heading);
    const host=document.createElement('div');panel.appendChild(host);$('runs').appendChild(panel);
    viewer=createTimelineViewer(host,{comparison:true,onPan:start=>{$('pan').value=start;sync();}});
    viewer.load(data,file.name);
    const background=document.createElement('select');background.setAttribute('aria-label','Export background');
    for(const [value,label] of [['transparent','Transparent'],['white','White']]){const option=document.createElement('option');option.value=value;option.textContent=label;background.appendChild(option);}
    actions.appendChild(background);background.addEventListener('change',()=>viewer.setExportBackground(background.value));
    for(const [label,action] of [['Export SVG',()=>viewer.exportSVG()],['Export PNG',()=>viewer.exportPNG()]]){const button=document.createElement('button');button.textContent=label;button.addEventListener('click',action);actions.appendChild(button);}
    const run={data,viewer,panel};runs.push(run);
    remove.addEventListener('click',()=>{viewer.destroy();panel.remove();runs=runs.filter(r=>r!==run);sync();});
   }catch(error){if(viewer)viewer.destroy();if(panel)panel.remove();errors.push(`${file.name}: ${error.message}`);}
  }
  if(wasEmpty && runs.length){const end=Math.max(...runs.map(r=>r.viewer.getExtent()));$('zoom').max=end;$('zoom').value=Math.min(60,end);}
  loading=false;$('load').disabled=false;$('files').value='';$('error').textContent=errors.join('\n');sync();
 });
 $('clear').addEventListener('click',()=>{for(const r of runs){r.viewer.destroy();r.panel.remove();}runs=[];$('error').textContent='';$('zoom').value=60;$('pan').value=0;sync();});
 for(const id of ['zoom','pan','starts','deadlines'])$(id).addEventListener('input',sync);
 sync();
})();
