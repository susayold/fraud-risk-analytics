(() => {
  const nf = new Intl.NumberFormat('en-US');
  const esc = value => String(value ?? '—').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const num = value => Number.isFinite(Number(value)) ? Number(value) : null;
  const fmt = value => num(value) === null ? '—' : nf.format(num(value));
  const metric = value => num(value) === null ? '—' : Number(value).toFixed(4);
  const pct = value => num(value) === null ? '—' : `${(Number(value) * 100).toFixed(2)}%`;
  const set = (key, value) => document.querySelectorAll(`[data-network="${key}"]`).forEach(node => { node.textContent = value; });
  const fail = () => { document.querySelectorAll('[data-network]').forEach(node => { node.textContent = 'NETWORK EVIDENCE UNAVAILABLE'; }); document.querySelectorAll('[data-classification-chart],[data-novelty-cards],[data-community-chart],[data-monthly-chart],[data-ablations],[data-shap-list]').forEach(node => { node.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; }); };
  const label = { A_EDGE_ONLY:'A — Edge Only', B_GNN_ONLY:'B — GNN Only', C_EDGE_PLUS_GNN:'C — Edge + GNN' };
  const chartMetric = value => num(value) === null ? 0 : Math.max(3, Number(value) * 100);

  function renderClassification(data) {
    const target = document.querySelector('[data-classification-chart]'); const validation = data.model_comparison?.validation_warm || []; const test = data.model_comparison?.test_warm || [];
    if (!target || !validation.length || !test.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; }
    const groups = [{name:'Validation', rows:validation}, {name:'Test', rows:test}];
    target.innerHTML = groups.map(group => `<div class="bar-group"><div class="bar-group-label">${group.name}</div>${group.rows.map(row => `<div class="bar-item" style="--h:${chartMetric(row.pr_auc)}%;--bar:${row.model === 'A_EDGE_ONLY' ? '#67a7df' : row.model === 'B_GNN_ONLY' ? '#e3a141' : '#20a27d'}"><i></i><b>${metric(row.pr_auc)}</b><span>${esc(row.model.replaceAll('_',' '))}</span></div>`).join('')}</div>`).join('');
    const val = Object.fromEntries(validation.map(row => [row.model, row.pr_auc])); const tst = Object.fromEntries(test.map(row => [row.model, row.pr_auc]));
    set('val-a', metric(val.A_EDGE_ONLY)); set('val-b', metric(val.B_GNN_ONLY)); set('val-c', metric(val.C_EDGE_PLUS_GNN)); set('test-a', metric(tst.A_EDGE_ONLY)); set('test-b', metric(tst.B_GNN_ONLY)); set('test-c', metric(tst.C_EDGE_PLUS_GNN));
    set('validation-delta', `C − A = ${metric((num(val.C_EDGE_PLUS_GNN) || 0) - (num(val.A_EDGE_ONLY) || 0))}`); set('test-delta', `C − A = ${metric((num(tst.C_EDGE_PLUS_GNN) || 0) - (num(tst.A_EDGE_ONLY) || 0))}`);
  }

  function renderNovelty(data) {
    const target = document.querySelector('[data-novelty-cards]'); const rows = data.novelty_segments || [];
    if (!target || !rows.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; }
    target.innerHTML = rows.map(row => { const delta = Number(row.c_pr_auc) - Number(row.a_pr_auc); const positive = delta >= 0; return `<article class="novelty-card ${positive ? 'positive' : 'negative'}"><h3>${esc(row.segment.replaceAll('_',' '))}</h3><p>Relationship novelty diagnostic · retained support</p><div class="novelty-metrics"><span>Rows<b>${fmt(row.rows)}</b></span><span>Fraud<b>${fmt(row.fraud)}</b></span><span>A — Edge Only<b>${metric(row.a_pr_auc)}</b></span><span>C — Edge + GNN<b>${metric(row.c_pr_auc)}</b></span></div><div class="novelty-delta"><span>C − A</span><strong>${delta >= 0 ? '+' : ''}${metric(delta)}</strong></div><small>${row.segment === 'WARM_PAIR_SEEN' ? 'Combined graph context is weaker for already-seen pairs.' : row.segment === 'WARM_PAIR_NEW' ? 'Graph context adds useful information when both nodes are known but their pair is new.' : 'Largest observed uplift, with support limited to the retained fraud rows.'}</small></article>`; }).join('');
    const setNovelty = (segment, prefix) => { const row = rows.find(item => item.segment === segment); if (!row) return; set(`${prefix}-a`, metric(row.a_pr_auc)); set(`${prefix}-c`, metric(row.c_pr_auc)); set(`${prefix}-delta`, metric(Number(row.c_pr_auc) - Number(row.a_pr_auc))); };
    setNovelty('WARM_PAIR_SEEN','seen'); setNovelty('WARM_PAIR_NEW','new-pair'); setNovelty('NEW_CARD_ONLY','new-card');
  }

  function renderCommunity(data) {
    const target = document.querySelector('[data-community-chart]'); const rows = data.community_enrichment || [];
    if (!target || !rows.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; }
    const order = [['VALIDATION','SAME_COMMUNITY'],['VALIDATION','DIFFERENT_COMMUNITY'],['TEST','SAME_COMMUNITY'],['TEST','DIFFERENT_COMMUNITY']]; const selected = order.map(([split,segment]) => rows.find(row => row.split === split && row.segment === segment)).filter(Boolean); const max = Math.max(...selected.map(row => row.fraud_rate), 0.0001);
    target.innerHTML = selected.map(row => `<div class="community-bar ${row.segment === 'DIFFERENT_COMMUNITY' ? 'different' : ''}" style="--h:${Math.max(7, row.fraud_rate / max * 100)}%"><i></i><b>${pct(row.fraud_rate)}</b><span>${row.split.slice(0,3)} · ${row.segment === 'SAME_COMMUNITY' ? 'same' : 'different'}</span></div>`).join('');
  }

  function renderMonthly(data) {
    const target = document.querySelector('[data-monthly-chart]'); const rows = data.monthly_stability?.rows || [];
    if (!target || !rows.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; }
    const max = 1; target.innerHTML = rows.map(row => `<div class="month-column"><i style="--h:${Number(row.A) / max * 100}%"></i><i class="c" style="--h:${Number(row.C) / max * 100}%"></i><label>${esc(row.month)}</label></div>`).join(''); set('monthly-status', `${data.monthly_stability.status} · ${data.monthly_stability.months_available}`);
  }

  function renderAblations(data) { const target = document.querySelector('[data-ablations]'); const rows = data.ablations || []; if (!target || !rows.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; } target.innerHTML = `<div class="ablation-row ablation-header"><b>Control</b><b>Validation</b><b>Test</b></div>${rows.map(row => `<div class="ablation-row"><b>${esc(row.id.replaceAll('_',' '))}</b><strong>${metric(row.validation_pr_auc)}</strong><strong>${metric(row.test_pr_auc)}</strong></div>`).join('')}`; }
  function renderShap(data) { const target = document.querySelector('[data-shap-list]'); const rows = (data.shap || []).slice(0,8); if (!target || !rows.length) { if (target) target.innerHTML = '<div class="network-load-error">NETWORK EVIDENCE UNAVAILABLE</div>'; return; } const max = Math.max(...rows.map(row => row.mean_abs_shap), .01); target.innerHTML = rows.map(row => `<div class="shap-item"><label>${esc(row.feature)}</label><i style="--w:${Number(row.mean_abs_shap) / max * 100}%"></i><strong>${metric(row.mean_abs_shap)}</strong></div>`).join(''); }

  function render(data) {
    const d = data.part6_summary; if (!d) { fail(); return; }
    const graph = d.graph || {}; const foundation = d.foundation_graph || {}; const train = d.train_network || {}; const temporal = d.temporal_link_learning || {}; const uncertainty = d.uncertainty || {}; const publicBoundary = d.public_boundary || {};
    set('status', data.project_status?.layers?.part6?.technical_status || d.technical_status || 'STATUS UNAVAILABLE'); set('lifetime-pairs', fmt(foundation.lifetime_unique_pairs)); set('train-edges', fmt(train.train_unique_edges || graph.train_unique_edges)); set('total-nodes', fmt(train.total_nodes || graph.total_nodes)); set('communities', fmt(train.leiden_communities || graph.leiden_communities)); set('link-pr-auc', metric(temporal.link_ap)); set('card-nodes', fmt(foundation.card_nodes)); set('merchant-nodes', fmt(foundation.merchant_nodes)); set('monthly-rows', fmt(foundation.monthly_graph_rows)); set('train-rows', fmt(train.train_rows)); set('largest-community', fmt(train.largest_community_nodes || graph.largest_community_nodes)); set('link-positive', fmt(temporal.positive_links)); set('link-roc-auc', metric(temporal.link_roc_auc)); set('sync-diff', metric(temporal.max_parameter_sync_diff)); set('card-embedding-dim', fmt(train.card_embedding_dim)); set('merchant-embedding-dim', fmt(train.merchant_embedding_dim));
    const dims = train.feature_dimensions || {}; set('dim-a', `${fmt(dims.A_EDGE_ONLY)} features`); set('dim-b', `${fmt(dims.B_GNN_ONLY)} dimensions`); set('dim-c', `${fmt(dims.C_EDGE_PLUS_GNN)} dimensions`); set('global-delta', metric(uncertainty.test_warm_delta)); set('global-ci', `[${metric(uncertainty.ci95_low)}, ${metric(uncertainty.ci95_high)}]`); set('global-classification', uncertainty.classification || '—'); set('uncertainty-method', `${uncertainty.method || '—'} · ${fmt(uncertainty.replicates)} replicates`); set('graph-auto-block', publicBoundary.graph_auto_block_allowed === false ? 'NOT ALLOWED' : 'STATUS UNAVAILABLE'); set('raw-ids', publicBoundary.raw_ids_published === false ? 'NOT PUBLISHED' : 'STATUS UNAVAILABLE'); set('raw-edges', publicBoundary.raw_edges_published === false ? 'NOT PUBLISHED' : 'STATUS UNAVAILABLE'); set('aggregate-only', publicBoundary.aggregate_only === true ? 'ALLOWED' : 'STATUS UNAVAILABLE'); set('closure-artifact', d.source?.closure_artifact || '—');
    renderClassification(d); renderNovelty(d); renderCommunity(d); renderMonthly(d); renderAblations(d); renderShap(d);
  }

  Promise.allSettled(['part6_summary.json','project_status.json'].map(file => fetch(`assets/data/${file}`, {cache:'no-store'}).then(response => response.ok ? response.json() : Promise.reject(file)))).then(results => { const data = {}; results.forEach((result, index) => { if (result.status === 'fulfilled') data[index === 0 ? 'part6_summary' : 'project_status'] = result.value; }); render(data); });
})();
