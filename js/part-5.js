(() => {
  const nf = new Intl.NumberFormat('en-US');
  const sources = ['part4_summary.json','part5_final_summary.json','part5_model_selection.json','part5_topk.json','part5_calibration.json','part5_subgroups.json','part5_uncertainty.json','project_status.json'];
  const esc = value => String(value ?? '—').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const num = value => Number.isFinite(Number(value)) ? Number(value) : null;
  const fmt = value => num(value) === null ? '—' : nf.format(num(value));
  const metric = value => num(value) === null ? '—' : Number(value).toFixed(4);
  const pct = value => num(value) === null ? '—' : `${(Number(value) * 100).toFixed(2)}%`;
  const compactPct = value => num(value) === null ? '—' : `${(Number(value) * 100).toFixed(3)}%`;
  const set = (key, value) => document.querySelectorAll(`[data-model="${key}"]`).forEach(node => { node.textContent = value; });
  const unavailable = selector => { const node = document.querySelector(selector); if (node) node.innerHTML = '<div class="load-error">Aggregate evidence unavailable.</div>'; };
  const familyName = { amount:'Amount', entity_history:'Entity History', geography:'Geography', relationship_familiarity:'Relationship Familiarity', velocity:'Velocity' };
  const familyCopy = { amount:'Positive amount baselines and deviations', entity_history:'User, card and merchant prior counts, cold start and recency', geography:'Extended-only dependency audit', relationship_familiarity:'Merchant, MCC and channel familiarity', velocity:'User, card and merchant count windows' };

  function renderFamilies(summary) {
    const target = document.querySelector('[data-feature-families]');
    const rows = summary?.feature_families;
    if (!target || !Array.isArray(rows)) { unavailable('[data-feature-families]'); return; }
    target.innerHTML = rows.map(row => `<article class="${row.feature_count ? '' : 'muted-family'}"><b>${esc(familyName[row.feature_family] || row.feature_family)}</b><strong>${fmt(row.feature_count)}</strong><span>${esc(familyName[row.feature_family] || row.feature_family)} features</span><small>${esc(familyCopy[row.feature_family] || row.scope)}</small></article>`).join('');
    const total = rows.reduce((sum, row) => sum + (num(row.feature_count) || 0), 0);
    set('feature-count', fmt(total)); set('feature-count-inline', fmt(total)); set('feature-contract', summary.feature_contract_version || 'Locked registry'); set('feature-contract-rail', summary.feature_contract_version || '—'); set('pit-contract-version', summary.pit_contract_version || '—'); set('bin-contract-version', summary.signal_bin_contract_version || '—'); set('pit-rule', summary.pit_rule || '—');
  }

  function binFor(rows, feature, bin) { return (rows || []).find(row => row.feature_name === feature && String(row.bin) === String(bin)); }
  function signalCard(title, subtitle, low, high, lowLabel, highLabel) {
    const lowRate = num(low?.fraud_rate) || 0; const highRate = num(high?.fraud_rate) || 0; const max = Math.max(lowRate, highRate, 0.0001); const ratio = lowRate ? highRate / lowRate : null;
    return `<article class="signal-card"><h3>${esc(title)}</h3><p>${esc(subtitle)}</p><div class="signal-bars"><div class="signal-bar"><label>${esc(lowLabel)}</label><i style="--w:${Math.max(4, lowRate / max * 100)}%"></i><strong>${compactPct(lowRate)}</strong></div><div class="signal-bar high"><label>${esc(highLabel)}</label><i style="--w:${Math.max(4, highRate / max * 100)}%"></i><strong>${compactPct(highRate)}</strong></div></div><div class="ratio">${ratio ? `${ratio.toFixed(2)}× higher fraud rate` : 'Insufficient comparison support'}<small>${fmt(low?.transactions)} vs ${fmt(high?.transactions)} transactions · ${fmt(low?.fraud_transactions)} vs ${fmt(high?.fraud_transactions)} fraud</small></div></article>`;
  }

  function renderSignals(summary) {
    const target = document.querySelector('[data-behavior-signals]'); const rows = [...(summary?.velocity_signal || []), ...((summary?.merchant_familiarity?.profiles) || [])];
    if (!target || !rows.length) { unavailable('[data-behavior-signals]'); return; }
    const card0 = binFor(rows, 'card_txn_count_1h', '0'); const card1 = binFor(rows, 'card_txn_count_1h', '1');
    const cold0 = binFor(rows, 'merchant_cold_start', '0'); const cold1 = binFor(rows, 'merchant_cold_start', '1');
    const pair0 = binFor(rows, 'card_merchant_is_new', '0'); const pair1 = binFor(rows, 'card_merchant_is_new', '1');
    target.innerHTML = [
      signalCard('Card velocity', 'card_txn_count_1h', card0, card1, 'count = 0', 'count = 1'),
      signalCard('Merchant cold start', 'merchant_cold_start', cold0, cold1, 'cold = 0', 'cold = 1'),
      signalCard('Card × merchant relationship', 'card_merchant_is_new', pair0, pair1, 'known', 'new')
    ].join('');
  }

  function renderCandidates(selection) {
    const target = document.querySelector('[data-candidate-models]'); const rows = selection?.rows;
    if (!target || !Array.isArray(rows)) { unavailable('[data-candidate-models]'); return; }
    target.innerHTML = rows.slice(0, 8).map(row => `<article class="${row.model === 'BlendTop3_Equal' ? 'selected' : ''}"><b>${esc(row.model)}</b><span>PR-AUC ${metric(row.pr_auc)} · ${row.model === 'BlendTop3_Equal' ? 'Validation-selected' : 'executed candidate'}</span></article>`).join('');
  }

  function renderLeaderboard(selection, champion) {
    const target = document.querySelector('[data-leaderboard]'); const rows = selection?.rows;
    if (!target || !Array.isArray(rows) || !rows.length) { unavailable('[data-leaderboard]'); return; }
    const max = Math.max(...rows.map(row => num(row.pr_auc) || 0), 0.01);
    target.innerHTML = rows.map(row => `<div class="leader-row ${row.model === champion?.name ? 'champion' : ''}"><label title="${esc(row.model)}">${esc(row.model)}</label><div><i style="--w:${Math.max(2, (num(row.pr_auc) || 0) / max * 100)}%"></i></div><strong>${metric(row.pr_auc)}</strong></div>`).join('');
    const runner = rows.find(row => row.model !== champion?.name); const margin = runner && num(rows[0]?.pr_auc) !== null && num(runner.pr_auc) !== null ? Math.abs(Number(rows[0].pr_auc) - Number(runner.pr_auc)) : null;
    set('champion-margin', margin === null ? 'Margin unavailable in retained leaderboard' : `Runner-up margin ≈ ${margin.toFixed(7)} PR-AUC · not a dominant-winner claim`);
    set('runner-up-note', margin === null ? 'Runner-up comparison unavailable.' : `Champion margin vs runner-up ≈ ${margin.toFixed(7)} PR-AUC. Treat this as a close Validation selection, not dominance.`);
  }

  function renderTopK(topk) {
    const rows = topk?.rows; const target = document.querySelector('[data-topk-bars]');
    if (!target || !Array.isArray(rows) || !rows.length) { unavailable('[data-topk-bars]'); return; }
    target.innerHTML = rows.map(row => `<div class="topk-item" style="--h:${Math.max(8, Number(row.capture || 0) * 100)}%"><i></i><b>${pct(row.capture)}</b><label>Top ${pct(row.top_k)}</label></div>`).join('');
    const top5 = rows.find(row => Number(row.top_k) === .05); const top1 = rows.find(row => Number(row.top_k) === .01); set('top5-capture', pct(top5?.capture)); set('oot-top1-capture', pct(top1?.capture));
  }

  function renderSubgroups(subgroups) {
    const target = document.querySelector('[data-subgroups]'); const rows = subgroups?.rows;
    if (!target || !Array.isArray(rows)) { unavailable('[data-subgroups]'); return; }
    target.innerHTML = rows.map(row => row.support === 'LOW_SUPPORT' ? `<div class="low"><b>${esc(row.segment)}</b><span>LOW SUPPORT · no performance claim · rows ${fmt(row.rows)}</span></div>` : `<div><b>${esc(row.segment)}</b><span>n=${fmt(row.rows)} · fraud=${fmt(row.fraud_rows)} · PR-AUC ${metric(row.pr_auc)} · Top 1% ${pct(row.top_1pct_capture)}</span></div>`).join('');
  }

  function renderAll(data) {
    const behavior = data.part4_summary; const final = data.part5_final_summary; const selection = data.part5_model_selection; const topk = data.part5_topk; const calibration = data.part5_calibration; const subgroups = data.part5_subgroups; const uncertainty = data.part5_uncertainty; const status = data.project_status;
    if (behavior) { renderFamilies(behavior); renderSignals(behavior); const execution = behavior.execution || {}; set('qa-rows', fmt(execution.rows)); set('qa-scope', execution.scope || '—'); set('history-status', execution.history_coverage_status || '—'); set('qa-slice-pass', execution.qa_execution_slice_pass ? 'PASS' : 'FAIL'); set('sql-fixture-pass', execution.sql_fixture_pass ? 'PASS' : 'FAIL'); set('semantic-pass', execution.semantic_invariants_pass ? 'PASS' : 'FAIL'); set('entity-qa-pass', execution.entity_complete_qa_pass ? 'PASS' : 'FAIL'); }
    if (final) {
      const validation = final.validation?.metrics || {}; const oot = final.oot || {}; const om = oot.metrics || {}; const champion = final.champion || {}; const degradation = final.degradation || {};
      set('champion-version', champion.version || '—'); set('champion-name', champion.name || '—'); set('champion-name-large', champion.name || '—'); set('champion-version-large', champion.version || '—'); set('champion-composition', Array.isArray(champion.components) ? champion.components.map(item => `${item.name} · ${Math.round(Number(item.weight || 0) * 100)}% · ${item.calibration}`).join(' | ') : 'Composition unavailable'); set('freeze-badge', champion.oot_used_for_retuning === false ? 'FROZEN · NO OOT RETUNING' : 'Freeze flag unavailable');
      set('validation-pr-auc', metric(validation.pr_auc)); set('validation-pr-auc-large', metric(validation.pr_auc)); set('validation-roc-auc', metric(validation.roc_auc)); set('validation-ks', metric(validation.ks)); set('oot-pr-auc', metric(om.pr_auc)); set('oot-pr-auc-large', metric(om.pr_auc)); set('oot-roc-auc', metric(om.roc_auc)); set('oot-roc-auc-large', metric(om.roc_auc)); set('oot-ks', metric(om.ks)); set('degradation-relative', pct(degradation.relative_delta)); set('degradation-absolute', metric(degradation.absolute_delta)); set('oot-population', oot.population || '—'); set('oot-rows', fmt(oot.rows)); set('oot-fraud', fmt(oot.fraud_rows)); set('oot-prevalence', pct(oot.prevalence)); set('oot-random-lift', num(om.pr_auc) !== null && num(oot.prevalence) ? `${(Number(om.pr_auc) / Number(oot.prevalence)).toFixed(0)}×` : '—');
      set('champion-version', champion.version || '—');
    }
    if (selection) { renderCandidates(selection); renderLeaderboard(selection, final?.champion); }
    if (topk) renderTopK(topk);
    if (calibration) { const m = calibration.metrics || {}; set('cal-intercept', metric(m.intercept)); set('cal-slope', metric(m.slope)); set('cal-brier', metric(m.brier)); set('cal-logloss', metric(m.log_loss)); }
    if (subgroups) renderSubgroups(subgroups);
    if (uncertainty?.retained_histogram_interval) set('uncertainty-interval', `[${Number(uncertainty.retained_histogram_interval.low).toFixed(6)}, ${Number(uncertainty.retained_histogram_interval.high).toFixed(6)}]`);
    if (status?.layers?.part5) set('blocks-status', status.layers.part5.execution_status === 'LOCKED' && final?.pipeline?.all_blocks_pass ? 'C00–C10 · 11 / 11 PASS' : 'Checkpoint status requires review');
  }

  const requests = sources.map(file => fetch(`assets/data/${file}`, {cache:'no-store'}).then(response => response.ok ? response.json() : Promise.reject(new Error(file))));
  Promise.allSettled(requests).then(results => { const data = {}; results.forEach((result, index) => { if (result.status === 'fulfilled') data[sources[index].replace('.json','')] = result.value; }); renderAll(data); if (!data.part5_final_summary) { document.querySelectorAll('.model-kpis strong').forEach(node => { if (node.textContent === '—') node.textContent = 'Unavailable'; }); } });
  document.querySelectorAll('.model-page a[href^="#"]').forEach(link => link.addEventListener('click', () => { const target = document.querySelector(link.getAttribute('href')); if (target) target.setAttribute('tabindex', '-1'); }));
})();
