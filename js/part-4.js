(() => {
  const nf = new Intl.NumberFormat('en-US');
  const number = v => Number.isFinite(Number(v)) ? nf.format(Number(v)) : '—';
  const pct = v => Number.isFinite(Number(v)) ? `${(Number(v) * 100).toFixed(Number(v) < .01 ? 3 : 1)}%` : '—';
  const safe = v => String(v ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const set = (key, value) => document.querySelectorAll(`[data-summary="${key}"]`).forEach(el => el.textContent = value);
  const chartRefs = [];
  const theme = {green:'#198754',greenSoft:'#b8dfc5',blue:'#2671cf',amber:'#e28a00',text:'#5f6b64',axis:'#dfe5e0'};
  const init = id => { const node = document.getElementById(id); if (!node || !window.echarts) return null; const chart = echarts.init(node); chartRefs.push(chart); return chart; };
  const table = (headers, rows) => `<table><thead><tr>${headers.map(h => `<th>${safe(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;

  function renderFamilies(rows) {
    const holder = document.getElementById('family-grid'); if (!holder) return;
    holder.innerHTML = (rows || []).map(row => `<div class="family-card"><b>${safe(row.feature_family).replaceAll('_',' ')}</b><span>${number(row.feature_count)}</span><small>${safe(row.scope)}</small></div>`).join('');
  }
  function renderVelocity(rows) {
    const usable = (rows || []).filter(r => String(r.feature_name).includes('count')).slice(0, 12);
    const chart = init('velocity-chart');
    if (chart && usable.length) chart.setOption({grid:{left:45,right:18,top:16,bottom:55},tooltip:{trigger:'axis',backgroundColor:'#13231b',borderWidth:0,textStyle:{color:'#fff',fontSize:11}},xAxis:{type:'category',data:usable.map(r=>`${r.feature_name.replaceAll('_',' ')} · ${r.bin}`),axisLabel:{rotate:35,fontSize:9,color:theme.text}},yAxis:{type:'value',axisLabel:{formatter:v=>`${(v*100).toFixed(2)}%`,fontSize:9,color:theme.text},splitLine:{lineStyle:{color:'#edf1ed'}}},series:[{type:'bar',barMaxWidth:20,itemStyle:{color:theme.green,borderRadius:[5,5,0,0]},data:usable.map(r=>Number(r.fraud_rate||0))}]});
    const holder = document.getElementById('velocity-table'); if (holder) holder.innerHTML = usable.length ? table(['Feature','Bin','Transactions','Fraud','Rate'], usable.map(r => `<tr><td>${safe(r.feature_name)}</td><td>${safe(r.bin)}</td><td>${number(r.transactions)}</td><td>${number(r.fraud_transactions)}</td><td>${pct(r.fraud_rate)}</td></tr>`)) : '<div class="mini-note"><span class="signal-dot amber"></span><p>Full-population signal profile is not published until the offline runner completes.</p></div>';
  }
  function renderAmount(rows) {
    const usable = (rows || []).filter(r => String(r.feature_name).includes('amount')).slice(0, 12);
    const chart = init('amount-chart');
    if (chart && usable.length) chart.setOption({grid:{left:40,right:14,top:12,bottom:64},tooltip:{trigger:'axis',backgroundColor:'#13231b',borderWidth:0,textStyle:{color:'#fff',fontSize:11}},xAxis:{type:'category',data:usable.map(r=>`${r.feature_name.includes('user')?'user':'card'} · ${r.bin}`),axisLabel:{rotate:40,fontSize:9,color:theme.text}},yAxis:{type:'value',axisLabel:{formatter:v=>`${(v*100).toFixed(2)}%`,fontSize:9,color:theme.text},splitLine:{lineStyle:{color:'#edf1ed'}}},series:[{type:'bar',barMaxWidth:18,itemStyle:{color:theme.blue,borderRadius:[5,5,0,0]},data:usable.map(r=>Number(r.fraud_rate||0))}]});
  }
  function renderFamiliarity(rows) {
    const usable = (rows || []).filter(r => /merchant|mcc|channel/.test(String(r.feature_name))).slice(0, 10);
    const holder = document.getElementById('familiarity-table'); if (holder) holder.innerHTML = usable.length ? table(['Feature','Value','Transactions','Fraud','Rate'], usable.map(r => `<tr><td>${safe(r.feature_name)}</td><td>${safe(r.feature_value)}</td><td>${number(r.transactions)}</td><td>${number(r.fraud_transactions)}</td><td>${pct(r.fraud_rate)}</td></tr>`)) : '<div class="mini-note"><span class="signal-dot amber"></span><p>Relationship profiles will appear after the governed offline aggregate run.</p></div>';
  }
  function renderCold(rows) {
    const holder = document.getElementById('cold-table'); if (!holder) return;
    holder.innerHTML = rows?.length ? table(['Entity','Cold start','Transactions','Fraud rate'], rows.map(r => `<tr><td>${safe(r.entity)}</td><td>${safe(r.cold_start)}</td><td>${number(r.transactions)}</td><td>${pct(r.fraud_rate)}</td></tr>`)) : '';
  }
  function renderDependency(rows) {
    const usable = rows || []; const chart = init('dependency-chart');
    if (chart && usable.length) { const labels = usable.map(r => `${r.channel} · ${r.state_status}`); chart.setOption({grid:{left:36,right:15,top:12,bottom:55},tooltip:{trigger:'axis',backgroundColor:'#13231b',borderWidth:0,textStyle:{color:'#fff',fontSize:11},formatter:p => { const r=usable[p[0].dataIndex]; return `<b>${safe(labels[p[0].dataIndex])}</b><br>Rows: ${number(r.transactions)}<br>Share: ${pct(r.share)}`;}},xAxis:{type:'category',data:labels,axisLabel:{rotate:30,fontSize:9,color:theme.text}},yAxis:{type:'value',axisLabel:{fontSize:9,color:theme.text},splitLine:{lineStyle:{color:'#edf1ed'}}},series:[{type:'bar',barMaxWidth:24,itemStyle:{color:theme.amber,borderRadius:[5,5,0,0]},data:usable.map(r=>Number(r.transactions||0))}]}); }
  }
  function renderFindings(rows) { const holder=document.getElementById('finding-grid'); if(holder) holder.innerHTML=(rows||[]).map((r,i)=>`<article class="finding-card"><span class="finding-number">${String(i+1).padStart(2,'0')}</span><h3>${safe(r.title)}</h3><p><strong>Evidence:</strong> ${safe(r.evidence)}</p><p><strong>Meaning:</strong> ${safe(r.meaning)}</p><p class="next"><strong>Next:</strong> ${safe(r.next_action)}</p></article>`).join(''); }

  fetch('assets/data/part4_summary.json').then(r => r.ok ? r.json() : Promise.reject(new Error('summary unavailable'))).then(data => {
    const base = data.base || {}; const sample = String(data.status).includes('SAMPLE');
    set('population', number(base.source_population_rows || base.transactions));
    set('statusLabel', data.status === 'BEHAVIOR_READY' ? 'BEHAVIOR READY' : sample ? 'SAMPLE QA · CONTRACT READY' : 'CONTRACT READY · OFFLINE BUILD');
    set('statusNote', sample ? `Deterministic ${number(base.transactions)}-row QA profile · not full-population evidence` : 'PIT contract validated · full feature build runs offline');
    set('profileScope', sample ? `deterministic ${number(base.transactions)}-row sample · Development signal only` : 'full-population aggregate profile');
    set('signalStatus', sample ? 'SAMPLE QA PROFILE' : 'FULL PROFILE PENDING');
    set('signalNote', sample ? 'Real executed sample numbers; no full-population or model-performance claim.' : 'No proxy numbers are shown until execution completes.');
    set('finalStatus', sample ? 'SAMPLE QA' : data.status);
    document.querySelectorAll('[data-status]').forEach(el => el.dataset.status = data.status === 'BEHAVIOR_READY' ? 'pass' : 'review');
    renderFamilies(data.feature_families); renderVelocity(data.velocity_signal); renderAmount(data.amount_signal); renderFamiliarity(data.merchant_familiarity?.profiles?.concat(data.channel_familiarity?.profiles || [])); renderCold(data.cold_start?.profiles); renderDependency(data.dependency?.channel_state); renderFindings(data.findings);
  }).catch(() => { set('statusLabel','CONTRACT READY · OFFLINE BUILD'); set('statusNote','Summary unavailable; no fallback analytics rendered.'); });
  window.addEventListener('resize', () => chartRefs.forEach(c => c.resize()));
  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) { gsap.from('.b4-hero .hero-copy > *, .hero-visual', {y:22,opacity:0,duration:.7,stagger:.08,ease:'power3.out'}); gsap.utils.toArray('.metric-card,.panel,.family-card,.finding-card').forEach(item => gsap.from(item,{y:14,opacity:0,duration:.5,ease:'power2.out',scrollTrigger:{trigger:item,start:'top 90%',once:true}})); }
})();

