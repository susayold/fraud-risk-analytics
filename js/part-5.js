(() => {
  const nf = new Intl.NumberFormat('en-US');
  const safe = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const number = v => Number.isFinite(Number(v)) ? nf.format(Number(v)) : '—';
  const metric = v => Number.isFinite(Number(v)) ? Number(v).toFixed(4) : '—';
  const pct = v => Number.isFinite(Number(v)) ? `${(Number(v) * 100).toFixed(1)}%` : '—';
  const set = (key, value) => document.querySelectorAll(`[data-summary="${key}"]`).forEach(el => el.textContent = value);
  const charts = [];
  const theme = {green:'#198754',blue:'#2671cf',amber:'#e28a00',text:'#5f6b64',grid:'#e8eee9'};
  const empty = id => { const el=document.getElementById(id); if(el) el.innerHTML='<div class="empty-chart">Aggregate evidence pending a real offline run.</div>'; };
  const init = id => { const el=document.getElementById(id); if(!el || !window.echarts) return null; el.innerHTML=''; const c=echarts.init(el); charts.push(c); return c; };
  const table = (head, rows) => `<table><thead><tr>${head.map(x=>`<th>${safe(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(x=>`<td>${safe(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  function renderTopK(rows) {
    if (!rows?.length) return empty('topk-chart');
    const c=init('topk-chart'); if(!c) return;
    c.setOption({grid:{left:45,right:15,top:18,bottom:40},tooltip:{trigger:'axis',formatter:p=>`${safe(p[0].axisValue)}<br>Fraud capture: ${pct(p[0].value)}`},xAxis:{type:'category',data:rows.map(r=>`${Number(r.top_k)*100}%`)},yAxis:{type:'value',axisLabel:{formatter:v=>`${(v*100).toFixed(0)}%`},splitLine:{lineStyle:{color:theme.grid}}},series:[{type:'line',smooth:true,symbol:'circle',data:rows.map(r=>Number(r.fraud_capture_rate)),lineStyle:{color:theme.green,width:3},itemStyle:{color:theme.green}}]});
  }
  function renderCalibration(rows) {
    if (!rows?.length) return empty('calibration-chart');
    const c=init('calibration-chart'); if(!c) return;
    c.setOption({grid:{left:48,right:18,top:18,bottom:42},tooltip:{trigger:'axis'},xAxis:{type:'value',name:'Predicted',min:0},yAxis:{type:'value',name:'Observed',min:0},series:[{type:'line',data:[[0,0],[1,1]],symbol:'none',lineStyle:{color:'#b3bbb6',type:'dashed'}},{type:'line',data:rows.map(r=>[Number(r.mean_predicted_probability),Number(r.observed_fraud_rate)]),symbol:'circle',lineStyle:{color:theme.blue,width:3},itemStyle:{color:theme.blue}}]});
  }
  function renderIncremental(data) {
    if(!data || !Number.isFinite(Number(data.delta_pr_auc))) return empty('incremental-chart');
    const c=init('incremental-chart'); if(!c) return;
    const vals=[Number(data.delta_pr_auc),Number(data.delta_roc_auc),Number(data.delta_ks)].map(v=>Number.isFinite(v)?v:0);
    c.setOption({grid:{left:45,right:16,top:18,bottom:42},tooltip:{trigger:'axis'},xAxis:{type:'category',data:['Δ PR-AUC','Δ ROC-AUC','Δ KS']},yAxis:{type:'value',splitLine:{lineStyle:{color:theme.grid}}},series:[{type:'bar',barMaxWidth:42,data:vals.map(v=>({value:v,itemStyle:{color:v>=0?theme.green:theme.amber}}))}]});
  }
  function renderImportance(rows) {
    const el=document.getElementById('importance-table'); if(!el) return;
    if(!rows?.length){el.innerHTML='<div class="empty-chart">No feature attribution published yet.</div>';return;}
    el.innerHTML=table(['Feature','Coefficient','|Coefficient|'],rows.slice(0,10).map(r=>[r.feature_name,metric(r.coefficient),metric(r.absolute_coefficient)]));
  }
  function renderFeatureSets(rows) {
    if(!rows?.length) return;
    const el=document.getElementById('feature-set-grid'); if(!el) return;
    el.innerHTML=rows.map(r=>`<article class="${r.name==='F2'?'feature-set-primary':''}"><b>${safe(r.name)}</b><h3>${safe(r.label)}</h3><strong>${number(r.feature_count)} features</strong><small>${r.name==='F0'?'amount, channel, MCC, state-missing flag':r.name==='F1'?'user, card, merchant and relationship history':'primary incremental-value comparison'}</small></article>`).join('');
  }
  fetch('assets/data/part5_summary.json').then(r=>r.ok?r.json():Promise.reject()).then(data=>{
    const exec=data.execution||{}, validation=data.validation||{}, locked=data.status==='MODEL_READY'&&data.lock_status==='LOCKED'&&validation.status==='PASS';
    const championSelected=data.status==='CHAMPION_SELECTED';
    set('historyRows',number(exec.history_population_rows)); set('behaviorFeatures',number((data.feature_sets||[]).find(x=>x.name==='F1')?.feature_count||43)); set('targetRows',number(exec.target_rows));
    set('validationPrauc',metric(data.validation_metrics?.find(x=>x.feature_set==='F2')?.pr_auc)); set('ootStatus',exec.oot_rows_manifested==null?'NOT RUN':data.splits?.oot?.accessed?'ACCESSED':'MANIFESTED'); set('ootStatusLong',data.splits?.oot?.accessed?'OOT ACCESSED':'OOT NOT ACCESSED');
    set('statusLabel',locked?'MODEL READY · LOCKED':championSelected?'CHAMPION SELECTED · OOT PENDING':'FRAMEWORK READY · METRICS SOURCE-DRIVEN');
    set('statusNote',locked?'Frozen champion and final OOT evidence are available.':championSelected?'Validation candidate selected; OOT remains frozen and unaccessed.':'The complete lifecycle is defined; executed metrics remain gated by the public evidence contract.');
    set('logisticStatus',championSelected?'CHAMPION CANDIDATE':'IN_PROGRESS'); set('championStatus',data.champion?.status||'INPUT_BLOCKED'); set('championName',data.champion?.model_name||'No champion selected'); set('footerStatus',locked?'MODEL READY · LOCKED':championSelected?'CHAMPION SELECTED · OOT PENDING':'FRAMEWORK READY · METRICS SOURCE-DRIVEN');
    (data.public_presentation?.model_inventory||[]).forEach(function(item){document.querySelectorAll(`[data-model-status="${item.name}"]`).forEach(function(el){el.textContent=item.status;});});
    (data.public_presentation?.lifecycle||[]).forEach(function(item){document.querySelectorAll(`[data-stage-status="${item.label}"]`).forEach(function(el){el.textContent=item.status;});});
    const status=document.querySelector('.p5-status'); if(status) status.dataset.status=locked?'pass':'review';
    renderFeatureSets(data.feature_sets); renderTopK(data.topk); renderCalibration(data.calibration?.bins); renderIncremental(data.incremental_value); renderImportance(data.feature_importance);
  }).catch(()=>{set('statusLabel','EVIDENCE LOAD ERROR');set('statusNote','Summary unavailable; no model claim is shown.');set('footerStatus','EVIDENCE LOAD ERROR');document.querySelector('.p5-status')?.setAttribute('data-status','review');['pr-chart','calibration-chart','topk-chart','incremental-chart'].forEach(empty);});
  window.addEventListener('resize',()=>charts.forEach(c=>c.resize()));
  if(window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches){gsap.from('.p5-hero-copy > *, .p5-hero-visual',{y:20,opacity:0,duration:.7,stagger:.08,ease:'power3.out'});gsap.utils.toArray('.metric-card,.panel,.feature-set-grid article,.model-grid article').forEach(el=>gsap.from(el,{y:12,opacity:0,duration:.45,ease:'power2.out',scrollTrigger:{trigger:el,start:'top 90%',once:true}}));}
})();
