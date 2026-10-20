/* Product workflows around the Python simulation. No analytical duplicate engine. */
'use strict';
window.PulsePlus={
  activeChallenge:null,cases:[],editing:null,undo:[],
  storageKey:'mq.pipeline-pulse.experiments.v1',
  mount(){
    const bar=document.createElement('div');bar.className='mode-launcher';
    bar.innerHTML='<div><span class="eyebrow">GO BEYOND THE DEMO</span><strong>Build. Investigate. Keep your discoveries.</strong></div><div><button data-open-mode="4">＋ Visual builder</button><button data-open-mode="5">◎ Incident arena</button><button data-open-mode="6">▣ My experiments</button></div>';
    $('.commandbar').after(bar);
    $$('[data-open-mode]').forEach(b=>b.onclick=()=>switchView(Number(b.dataset.openMode)));
    fetch('challenges.json?v=20261020.4').then(r=>{if(!r.ok)throw new Error('Incident scenarios could not load.');return r.json();}).then(cases=>{this.cases=cases;if(S.view===5)this.renderArena();}).catch(e=>showError(e.message));
    if(location.hash==='#arena')switchView(5);
    if(location.hash==='#builder')switchView(4);
    if(location.hash==='#vault')switchView(6);
  },
  render(view){
    if(view===4)this.renderBuilder();
    if(view===5)this.renderArena();
    if(view===6)this.renderVault();
  },
  nodes(){
    const nodes=JSON.parse($('#f-pipeline').value);
    if(!Array.isArray(nodes)||nodes.length>40)throw new Error('Use a JSON array of up to 40 nodes.');
    return nodes;
  },
  change(nodes){
    this.undo.push($('#f-pipeline').value);if(this.undo.length>20)this.undo.shift();
    $('#f-pipeline').value=JSON.stringify(nodes,null,2);this.activeChallenge=null;S.positions={};
  },
  renderBuilder(){
    let nodes;try{nodes=this.nodes();}catch(e){$('#view').innerHTML=heading('Visual pipeline builder','Fix the JSON in the input editor to continue.')+'<p class="small">'+esc(e.message)+'</p>';return;}
    const n=nodes.find(x=>x.id===this.editing),deps=n?.depends||[];
    $('#view').innerHTML=heading('Build the pipeline you want to test','Add activities and wire their dependencies without writing JSON. Python validates the DAG when you run.',`${nodes.length} / 40 ACTIVITIES`)+
    `<div class="builder-layout"><form id="node-form" class="builder-form"><div class="eyebrow">${n?'EDIT ACTIVITY':'NEW ACTIVITY'}</div><label>Activity ID<input id="builder-id" value="${esc(n?.id||'')}" ${n?'readonly':''} required placeholder="e.g. validate_orders" maxlength="40"></label><label>Display name<input id="builder-label" value="${esc(n?.label||'')}" maxlength="80" placeholder="Validate orders"></label><div class="builder-numbers"><label>Duration · seconds<input id="builder-duration" type="number" min="1" max="3600" value="${n?.duration||30}" required></label><label>Intrinsic failures<input id="builder-failures" type="number" min="0" max="10" value="${n?.failures||0}" required></label></div><label>Activity type<select id="builder-kind">${['source','ingest','quality','transform','mart','serve','activity'].map(k=>`<option ${k===(n?.kind||'transform')?'selected':''}>${k}</option>`).join('')}</select></label><fieldset><legend>Upstream dependencies</legend><div class="dependency-picker">${nodes.filter(x=>x.id!==n?.id).map(x=>`<label><input type="checkbox" name="depends" value="${esc(x.id)}" ${deps.includes(x.id)?'checked':''}>${esc(x.label||x.id)} <small>${esc(x.id)}</small></label>`).join('')||'<p class="small">The first activity has no upstream dependencies.</p>'}</div></fieldset><div class="inline-fields"><button class="primary" type="submit">${n?'Save changes':'Add activity'}</button><button type="button" id="builder-new">Clear form</button></div><p class="micro">IDs use letters, numbers, underscores, and hyphens. Self-dependencies are excluded; Python rejects cycles and missing references.</p></form><div><div class="builder-list">${nodes.map(x=>`<article class="builder-node"><div><span class="eyebrow">${esc(x.kind||'activity')}</span><h3>${esc(x.label||x.id)}</h3><p>${esc(x.id)} · ${esc(x.duration)}s · ${(x.depends||[]).length} upstream</p></div><div><button data-edit-node="${esc(x.id)}" aria-label="Edit ${esc(x.id)}">Edit</button><button data-delete-node="${esc(x.id)}" aria-label="Remove ${esc(x.id)}">×</button></div></article>`).join('')}</div><div class="inline-fields"><button id="builder-run" class="primary">Simulate this pipeline</button><button id="builder-undo" ${this.undo.length?'':'disabled'}>Undo graph edit</button></div><p class="small" id="builder-note">Edits update the input model. Simulation results change after you run. Removing an activity is blocked while downstream activities still depend on it.</p></div></div>`;
    $('#builder-new').onclick=()=>{this.editing=null;this.renderBuilder();};
    $('#builder-undo').onclick=()=>{if(this.undo.length){$('#f-pipeline').value=this.undo.pop();this.activeChallenge=null;this.editing=null;this.renderBuilder();}};
    $('#node-form').onsubmit=e=>{e.preventDefault();try{
      const id=$('#builder-id').value.trim();if(!n&&!/^[a-zA-Z][a-zA-Z0-9_-]{0,39}$/.test(id))throw new Error('Start the ID with a letter; use up to 40 letters, digits, underscores, or hyphens.');
      if(!n&&nodes.some(x=>x.id===id))throw new Error('That activity ID already exists.');
      if(!n&&nodes.length>=40)throw new Error('The simulator supports at most 40 activities.');
      const next={id,label:$('#builder-label').value.trim()||id,duration:Number($('#builder-duration').value),failures:Number($('#builder-failures').value),kind:$('#builder-kind').value,depends:$$('#node-form input[name=depends]:checked').map(x=>x.value)};
      this.change(n?nodes.map(x=>x.id===id?next:x):[...nodes,next]);this.editing=null;this.renderBuilder();toast('Pipeline model updated. Run to validate and simulate.');
    }catch(e){showError(e.message);}};
    $$('[data-edit-node]').forEach(b=>b.onclick=()=>{this.editing=b.dataset.editNode;this.renderBuilder();$('#builder-label').focus();});
    $$('[data-delete-node]').forEach(b=>b.onclick=()=>{const id=b.dataset.deleteNode,dependents=nodes.filter(x=>(x.depends||[]).includes(id));if(dependents.length){showError('Disconnect downstream dependencies before removing '+id+': '+dependents.map(x=>x.id).join(', '));return;}if(nodes.length===1){showError('Keep at least one pipeline activity.');return;}this.change(nodes.filter(x=>x.id!==id));if($('#f-inject').value===id)$('#f-inject').value='';if($('#f-repair').value===id)$('#f-repair').value='';this.editing=null;this.renderBuilder();});
    $('#builder-run').onclick=()=>{switchView(0);analyze();};
  },
  renderArena(){
    const active=this.cases.find(c=>c.id===this.activeChallenge);
    const grade=!S.preview&&S.result?.lab?.challenge?.id===this.activeChallenge?S.result.lab.challenge:null;
    $('#view').innerHTML=heading('Incident arena','Three reproducible engineering challenges, evaluated by Python. Synthetic exercises; no external resources are changed.','LEARN BY REPAIRING')+
    `<div class="arena-cases">${this.cases.map(c=>`<button class="arena-card ${c.id===this.activeChallenge?'active':''}" data-challenge="${c.id}"><span class="eyebrow">${esc(c.level)}</span><strong>${esc(c.title)}</strong><span>${c.deadline}s completion target · ≤${c.max_workers} workers</span></button>`).join('')||'<p class="small">Loading incident scenarios…</p>'}</div>`+
    (active?`<article class="challenge-brief"><div class="panel-heading"><div><h2>${esc(active.title)}</h2><p>${esc(active.brief)}</p></div>${tag(grade?.passed?'SOLVED':grade?'TRY AGAIN':'ACTIVE',grade?.passed?'ok':'warn')}</div><div class="challenge-limits">${tag('≤ '+active.max_workers+' workers')}${tag('≤ '+active.max_retries+' retries')}${tag(active.repair_node?'One repair selection':'No repair')}${tag('Keep the graph intact')}</div><p class="small">Change the experiment controls on the right. For the repair challenge, type the causal activity ID in “Repair node in comparison.” Use Topology or Execution timeline to investigate, then return here.</p><div class="inline-fields"><button id="grade-run" class="primary">Run & grade solution</button><button id="investigate-challenge">Inspect topology</button><button id="leave-challenge">Leave challenge</button></div><details class="challenge-hint"><summary>Show a diagnostic hint</summary><p>${esc(active.hint)}</p></details></article>${grade?`<div class="challenge-score ${grade.passed?'solved':''}"><div><span class="eyebrow">${grade.passed?'CHALLENGE COMPLETE':'EVIDENCE FROM YOUR ATTEMPT'}</span><strong>${grade.completed}/${grade.total} activities · ${grade.wall_time}s</strong><p class="small">Evaluated ${esc(grade.evaluated_run)} run against the fixed ${grade.deadline}s target.</p></div><ul>${grade.checks.map(c=>`<li class="${c.passed?'passed':'failed'}"><span>${c.passed?'✓':'○'}</span>${esc(c.label)}</li>`).join('')}</ul></div>`:'<p class="small">Run the experiment to receive a grade for this challenge.</p>'}`:'<div class="challenge-welcome"><span class="eyebrow">CHOOSE YOUR INVESTIGATION</span><h3>Prove the reasoning, not just the result.</h3><p class="small">Keep the source activities intact. Each challenge grades completion, timing, and policy constraints. A fast failed run does not count as a solution.</p></div>');
    $$('[data-challenge]').forEach(b=>b.onclick=()=>this.loadChallenge(b.dataset.challenge));
    if(active){$('#grade-run').onclick=analyze;$('#investigate-challenge').onclick=()=>switchView(0);$('#leave-challenge').onclick=()=>{this.activeChallenge=null;this.renderArena();toast('Challenge mode ended. Your current pipeline remains in the editor.');};}
  },
  loadChallenge(id){
    const c=this.cases.find(c=>c.id===id);if(!c)return;
    loadSample();$('#f-pipeline').value=JSON.stringify(c.pipeline,null,2);$('#f-inject').value='';
    for(const [key,value]of Object.entries({...c.initial,deadline:c.deadline})){
      $('#f-'+key).value=value;if($('#o-'+key))$('#o-'+key).textContent=value;
    }
    this.activeChallenge=id;S.positions={};S.node=null;this.renderArena();analyze();
  },
  readVault(){
    try{const raw=localStorage.getItem(this.storageKey);if(!raw)return [];const v=JSON.parse(raw);if(!Array.isArray(v))throw new Error();return v.slice(0,12).filter(x=>x&&typeof x.id==='string'&&typeof x.name==='string'&&x.input);}
    catch{showError('Saved experiments could not be read. Your current input is still available; browser storage may be unavailable or contain an old format.');return [];}
  },
  writeVault(items){
    try{localStorage.setItem(this.storageKey,JSON.stringify(items));return true;}
    catch{showError('The browser could not save this experiment. Storage may be blocked or full. Export the experiment instead.');return false;}
  },
  restore(value){
    const p=PulseVault.normalize(value);
    for(const [key,,type]of C.fields){const e=$('#f-'+key);e.value=p[key]??C.sample[key]??'';if(type==='range')$('#o-'+key).textContent=e.value;}
    this.activeChallenge=p.challenge&&this.cases.some(c=>c.id===p.challenge)?p.challenge:null;S.positions={};this.editing=null;
    toast('Experiment restored locally. Run to recompute its results.');switchView(0);
  },
  renderVault(){
    const items=this.readVault();
    $('#view').innerHTML=heading('Your experiment vault','Save named pipeline inputs on this device, then reopen or export them. Nothing is uploaded.','OPT-IN / LOCAL STORAGE')+
    `<div class="vault-save"><label>Experiment name<input id="vault-name" maxlength="80" placeholder="e.g. Sales pipeline / two workers"></label><button id="vault-save" class="primary">Save current inputs</button><label class="vault-import">Import JSON<input id="vault-import" type="file" accept=".json" aria-label="Import experiment JSON"></label></div><p class="small">Saving stores the complete pipeline inputs in this browser until you delete them. Maximum 12 experiments. Inputs may contain sensitive names or labels; choose what to keep. Imported files are validated locally and are not saved automatically.</p><div class="vault-list">${items.map(x=>`<article class="vault-card"><div><span class="eyebrow">${esc(new Date(x.saved).toLocaleString())}</span><h3>${esc(x.name)}</h3><p>${esc(x.summary||'Inputs saved; run to compute results.')}</p></div><div class="inline-fields"><button data-load-experiment="${esc(x.id)}">Open</button><button data-export-experiment="${esc(x.id)}">Export JSON</button><button data-delete-experiment="${esc(x.id)}" aria-label="Delete ${esc(x.name)}">Delete</button></div></article>`).join('')||'<div class="challenge-welcome"><h3>Keep the experiments worth comparing.</h3><p class="small">Save the current setup, change the graph or worker budget, and reopen your baseline later.</p></div>'}</div>`;
    $('#vault-save').onclick=()=>{try{
      const name=$('#vault-name').value.trim();if(!name)throw new Error('Give this experiment a name.');
      const input=PulseVault.normalize(payload());const data=this.readVault();if(data.length>=12)throw new Error('Delete an old experiment before saving another.');
      const matches=S.input&&JSON.stringify(input)===JSON.stringify(PulseVault.normalize(S.input));
      data.unshift({id:crypto.randomUUID(),name,saved:new Date().toISOString(),input,summary:matches&&!S.preview?S.result.metrics.map(m=>m.label+': '+m.value).join(' · '):''});
      if(this.writeVault(data)){this.renderVault();toast('Saved on this device.');}
    }catch(e){showError(e.message);}};
    $$('[data-load-experiment]').forEach(b=>b.onclick=()=>{try{this.restore(items.find(x=>x.id===b.dataset.loadExperiment));}catch(e){showError(e.message);}});
    $$('[data-export-experiment]').forEach(b=>b.onclick=()=>{const x=items.find(x=>x.id===b.dataset.exportExperiment);download('pipeline-experiment.json',JSON.stringify({version:1,project:'pipeline-pulse',...x},null,2));});
    $$('[data-delete-experiment]').forEach(b=>b.onclick=()=>{if(this.writeVault(items.filter(x=>x.id!==b.dataset.deleteExperiment))){this.renderVault();toast('Saved experiment removed from this device.');}});
    $('#vault-import').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>2000000)throw new Error('Use an experiment file under 2 MB.');this.restore(JSON.parse(await file.text()));}catch(e){showError(e.message);}};
  },
  renderPlanner(){
    const planner=S.result?.lab?.planner;if(!planner)return;
    const part=document.createElement('section');part.className='capacity-planner';
    part.innerHTML=heading('Capacity planning frontier','Python reruns this recovery model with each worker budget. Choose a completion target in the controls.',planner.deadline+'s TARGET')+
    `<div class="capacity-summary"><strong>${planner.recommendation?planner.recommendation.workers+' workers':'No feasible budget'}</strong><p class="small">${planner.recommendation?'Smallest tested worker budget that completes every activity within the target.':'None of the 1–8 worker budgets complete every activity within this target. Address failures or revise the timing model.'} ${planner.repair?'Assumes the selected repair: '+esc(planner.repair)+'.':'No repair is assumed.'}</p></div>`+
    `<div class="capacity-bars">${planner.policies.map(p=>`<button data-workers="${p.workers}" class="${p.meets_target?'feasible':''}" aria-label="Use ${p.workers} workers"><span>${p.workers}</span><i style="height:${Math.max(5,100*p.wall_time/Math.max(...planner.policies.map(x=>x.wall_time)))}%"></i><b>${p.wall_time}s</b></button>`).join('')}</div>`+
    table(['Workers','Wall time','Completed','Compute utilization','Within target'],planner.policies.map(p=>[p.workers,p.wall_time+'s',p.completed+'/'+S.result.lab.nodes.length,p.compute_utilization+'%',p.meets_target?'yes':'no']))+
    '<p class="small">Click a bar to apply that worker budget. Compute utilization excludes backoff and is not a billing estimate. This deterministic comparison assumes the same graph, retry budget, and selected repair.</p>';
    $('#view').append(part);$$('[data-workers]').forEach(b=>b.onclick=()=>{$('#f-concurrency').value=b.dataset.workers;$('#o-concurrency').textContent=b.dataset.workers;analyze();});
  }
};
