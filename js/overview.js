(() => {
  'use strict';

  const unavailable = 'EVIDENCE UNAVAILABLE';
  const qsa = selector => [...document.querySelectorAll(selector)];
  const finite = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  const number = value => finite(value) ? Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : unavailable;
  const decimal = (value, digits = 4) => finite(value) ? Number(value).toFixed(digits) : unavailable;
  const percent = (value, digits = 2) => finite(value) ? `${(Number(value) * 100).toFixed(digits)}%` : unavailable;
  const text = value => value === null || value === undefined || value === '' ? unavailable : String(value);
  const set = (key, value) => qsa(`[data-overview="${key}"]`).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = value === unavailable ? 'unavailable' : 'available';
  });
  const setSource = (selector, value, state = value === unavailable ? 'unavailable' : 'available') => qsa(selector).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = state;
  });
  const findSegment = (items, predicate) => Array.isArray(items) ? items.find(predicate) : null;
  const load = file => fetch(`assets/data/${file}`, { cache: 'no-store' }).then(response => response.ok ? response.json() : Promise.reject(new Error(`${file} unavailable`)));
  const statusLabel = value => text(value).replaceAll('_', ' ');
  const gateSummary = summary => {
    if (!summary) return unavailable;
    const v = summary.validation || {};
    const status = summary.status || v.status;
    if (!finite(v.mandatory_gates) || !finite(v.pass)) return statusLabel(status);
    if (status === 'DECISION_POLICY_LOCKED' || status === 'MONITORING_GOVERNANCE_LOCKED') return `${number(v.pass)} / ${number(v.mandatory_gates)} PASS · ${status}`;
    return `${number(v.pass)} / ${number(v.mandatory_gates)} PASS · ${number(v.blocked || 0)} BLOCKED`;
  };
  const setStatus = (part, layer) => {
    const status = layer && layer.status ? layer.status : unavailable;
    const state = status === unavailable ? 'unavailable' : String(status).toLowerCase();
    qsa(`[data-status-registry="${part}"]`).forEach(el => {
      el.textContent = status === unavailable ? unavailable : statusLabel(status);
      el.dataset.state = state;
      el.dataset.sourceState = status === unavailable ? 'unavailable' : 'available';
    });
    qsa(`[data-registry-detail="${part}"]`).forEach(el => {
      let detail = unavailable;
      if (layer) {
        detail = layer.current_blocked_gates ? `${layer.current_blocked_gates} blocked gates · ${text(layer.technical_status)}` : text(layer.technical_status || layer.execution_status || layer.label);
      }
      el.textContent = detail;
      el.dataset.sourceState = detail === unavailable ? 'unavailable' : 'available';
    });
  };

  Promise.allSettled([
    load('part2_summary.json'),
    load('part3_summary.json'),
    load('part4_summary.json'),
    load('part5_final_summary.json'),
    load('part5_topk.json'),
    load('part6_summary.json'),
    load('part7_summary.json'),
    load('part8_summary.json'),
    load('project_status.json')
  ]).then(results => {
    const [part2, part3, part4, part5, topk, part6, part7, part8, registry] = results.map(result => result.status === 'fulfilled' ? result.value : null);

    if (part2) {
      set('transactions', number(part2.transactions));
      set('fraud-transactions', number(part2.fraud_transactions));
      set('fraud-rate', percent(part2.fraud_rate, 3));
      set('users', number(part2.users));
      set('cards', number(part2.cards));
      set('merchants', number(part2.merchants));
      set('date-range', `${text(part2.date_min)} → ${text(part2.date_max)}`);
      set('active-days', number(part2.active_days));
      set('part2-recon', part2.reconciliation_status === 'PASS' ? `${number(part2.transactions)} rows reconciled` : 'RECONCILIATION ERROR');
      set('part2-source', text(part2.source));
    } else {
      ['transactions', 'fraud-transactions', 'fraud-rate', 'users', 'cards', 'merchants', 'date-range', 'active-days', 'part2-recon', 'part2-source'].forEach(setKey => set(setKey, unavailable));
    }

    if (part3) {
      const online = findSegment(part3.channel, row => row.segment_value === 'Online Transaction');
      set('online-share', percent(online?.transaction_share, 1));
      set('online-rate', percent(online?.fraud_rate, 3));
      set('online-lift', `${decimal(online?.fraud_lift, 2)}×`);
      set('online-capture', percent(online?.fraud_capture_share, 1));
    } else {
      ['online-share', 'online-rate', 'online-lift', 'online-capture'].forEach(setKey => set(setKey, unavailable));
    }

    if (part4) {
      const count = Array.isArray(part4.feature_families) ? part4.feature_families.reduce((sum, item) => sum + Number(item.feature_count || 0), 0) : null;
      set('feature-count', finite(count) ? number(count) : unavailable);
    } else set('feature-count', unavailable);

    if (part5) {
      set('champion-version', text(part5.champion?.version));
      set('champion-name', text(part5.champion?.name));
      set('validation-pr-auc', decimal(part5.validation?.metrics?.pr_auc, 4));
      set('oot-pr-auc', decimal(part5.oot?.metrics?.pr_auc, 5));
      set('oot-roc-auc', decimal(part5.oot?.metrics?.roc_auc, 4));
      set('oot-ks', decimal(part5.oot?.metrics?.ks, 4));
      set('no-oot-retuning', part5.champion?.oot_used_for_retuning === false ? 'NO OOT RETUNING' : unavailable);
    } else {
      ['champion-version', 'champion-name', 'validation-pr-auc', 'oot-pr-auc', 'oot-roc-auc', 'oot-ks', 'no-oot-retuning'].forEach(setKey => set(setKey, unavailable));
    }
    if (topk) {
      const top5 = findSegment(topk.rows, row => Number(row.top_k) === 0.05);
      set('top5-capture', percent(top5?.capture, 1));
    } else set('top5-capture', unavailable);

    if (part6) {
      const test = part6.model_comparison?.test_warm || [];
      const edge = findSegment(test, row => row.model === 'A_EDGE_ONLY');
      const combined = findSegment(test, row => row.model === 'C_EDGE_PLUS_GNN');
      const delta = part6.uncertainty?.comparison === 'C_MINUS_A' ? part6.uncertainty : findSegment(part6.pairwise_uncertainty, row => row.comparison === 'C_MINUS_A');
      set('link-pr-auc', decimal(part6.temporal_link_learning?.link_ap, 3));
      set('edge-pr-auc', decimal(edge?.pr_auc, 4));
      set('gnn-only-pr-auc', decimal(findSegment(test, row => row.model === 'B_GNN_ONLY')?.pr_auc, 4));
      set('combined-pr-auc', decimal(combined?.pr_auc, 4));
      const deltaValue = finite(delta?.delta) ? Number(delta.delta) : finite(delta?.test_warm_delta) ? Number(delta.test_warm_delta) : null;
      set('graph-delta', finite(deltaValue) ? `${deltaValue >= 0 ? '+' : ''}${deltaValue.toFixed(5)}` : unavailable);
      set('graph-ci', finite(delta?.ci95_low) && finite(delta?.ci95_high) ? `95% CI [${Number(delta.ci95_low).toFixed(5)}, +${Math.abs(Number(delta.ci95_high)).toFixed(5)}]` : unavailable);
    } else {
      ['link-pr-auc', 'edge-pr-auc', 'gnn-only-pr-auc', 'combined-pr-auc', 'graph-delta', 'graph-ci'].forEach(setKey => set(setKey, unavailable));
    }

    if (part7) {
      set('p7-summary', gateSummary(part7));
      set('p7-status', statusLabel(part7.status));
      const locked = part7.status === 'DECISION_POLICY_LOCKED' && part7.validation?.final_lock_eligible === true;
      set('p7-review-threshold', locked ? decimal(part7.policy?.review_threshold, 7) : unavailable);
      set('p7-block-threshold', locked ? decimal(part7.policy?.block_threshold, 7) : unavailable);
      set('p7-capacity', locked ? percent(part7.policy?.review_capacity, 2) : unavailable);
      set('p7-evidence-note', locked ? `ALLOW ${percent(part7.final_evidence?.allow_rate)} · REVIEW ${percent(part7.final_evidence?.review_rate)} · BLOCK ${percent(part7.final_evidence?.block_rate)} · Fraud capture ${percent(part7.final_evidence?.fraud_capture)} · Exposure capture ${percent(part7.final_evidence?.fraud_exposure_capture)} · Simulated cost ${text(part7.final_evidence?.simulated_total_cost)}` : `${statusLabel(part7.status)} · final replay evidence is not published`);
    } else ['p7-summary', 'p7-status', 'p7-review-threshold', 'p7-block-threshold', 'p7-capacity', 'p7-evidence-note'].forEach(setKey => set(setKey, unavailable));

    if (part8) {
      set('p8-summary', gateSummary(part8));
      set('p8-status', statusLabel(part8.status));
      set('p8-matured-rows', finite(part8.matured_outcome_rows) ? number(part8.matured_outcome_rows) : unavailable);
      set('p8-evidence-note', part8.lifecycle?.matured_outcomes_available ? `${number(part8.matured_outcome_rows)} matured rows · aggregate retrospective evidence` : `${statusLabel(part8.status)} · matured outcomes are not published`);
    } else ['p8-summary', 'p8-status', 'p8-matured-rows', 'p8-evidence-note'].forEach(setKey => set(setKey, unavailable));

    if (registry?.layers) Object.entries(registry.layers).forEach(([part, layer]) => setStatus(part, layer));
    else ['part1', 'part2', 'part3', 'part4', 'part5', 'part6', 'part7', 'part8', 'part9'].forEach(part => setStatus(part, null));
  });

  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    gsap.from('.overview-hero .hero-copy > *, .architecture-visual', { y: 22, opacity: 0, duration: .7, stagger: .08, ease: 'power3.out' });
    gsap.utils.toArray('.scale-kpi, .tension-card, .layer-card, .finding-card, .scoreboard>div, .evidence-class, .explore-grid>a').forEach(group => gsap.from(group, { y: 16, opacity: 0, duration: .5, ease: 'power2.out', scrollTrigger: { trigger: group, start: 'top 90%', once: true } }));
  }
})();
