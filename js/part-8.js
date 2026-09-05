(() => {
  'use strict';
  const nodes = key => [...document.querySelectorAll(`[data-monitor="${key}"]`)]
  const set = (key, value) => nodes(key).forEach(node => { node.textContent = value })
  const raw = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value)) ? Number(value) : null
  const fmt = value => raw(value) === null ? '—' : Number(value).toLocaleString('en-US', {maximumFractionDigits: 2})
  const pct = value => raw(value) === null ? '—' : `${(Number(value) * 100).toFixed(2)}%`
  const first = (...values) => values.find(value => value !== undefined && value !== null)
  const sourceStatus = status => String(status || 'GATED').toUpperCase()
  const finalLocked = (summary, status) => { const v = summary.validation || {}; return status === 'MONITORING_GOVERNANCE_LOCKED' && v.pass === v.mandatory_gates && v.blocked === 0 && v.fail === 0 && v.final_lock_eligible === true }

  const setMetric = (metric, object, fallbackStatus = 'GATED') => {
    const value = first(object?.value, object?.current_value, object?.metric_value)
    const threshold = first(object?.threshold, object?.frozen_threshold)
    const support = first(object?.support, object?.rows, object?.fraud_support)
    const missing = raw(value) === null
    const noSupport = raw(support) === 0
    let status = sourceStatus(object?.status || fallbackStatus)
    if (noSupport) status = 'INSUFFICIENT_SUPPORT'
    else if (missing) status = status === 'AVAILABLE' || status === 'GREEN' ? 'NOT_EVALUABLE' : status
    else if (threshold === null && (metric.includes('psi') || metric.includes('js') || metric.includes('wasserstein'))) status = 'NOT_EVALUABLE'
    set(metric, raw(value) === null ? '—' : fmt(value)); set(`${metric}-threshold`, raw(threshold) === null ? '—' : fmt(threshold)); document.querySelectorAll(`[data-metric-status="${metric}"]`).forEach(node => { node.textContent = status })
  }

  const viewStatus = (source, key, locked) => {
    const views = source?.evidence_views || source?.views || source?.monitoring_views || {}
    const view = Array.isArray(views) ? views.find(item => item.id === key || item.view === key || item.name === key) : views[key]
    if (view?.status) return sourceStatus(view.status)
    if (!locked) return 'GATED'
    return view ? 'NOT_EVALUABLE' : 'GATED'
  }
  const renderViews = (summary, locked) => {
    const mapping = {'data-quality':'P8C2', drift:'P8C1', policy:'P8C3', graph:'P8C5'}
    Object.entries(mapping).forEach(([key, id]) => { document.querySelectorAll(`[data-view="${key}"]`).forEach(node => { node.textContent = viewStatus(summary, id, locked) }) })
    document.querySelectorAll('[data-view-status]').forEach(node => { node.textContent = viewStatus(summary, node.dataset.viewStatus, locked) })
  }
  const renderOptionalMetrics = summary => {
    const metrics = first(summary.metrics, summary.drift_metrics, summary.matured_metrics, {}) || {}
    const find = (...keys) => keys.reduce((value, key) => value ?? metrics[key] ?? summary[key], null)
    setMetric('score-psi', find('score_psi', 'risk_score_psi'), 'NOT_EVALUABLE'); setMetric('score-js', find('score_js', 'risk_score_js'), 'NOT_EVALUABLE'); setMetric('score-wasserstein', find('score_wasserstein', 'risk_score_wasserstein'), 'NOT_EVALUABLE'); setMetric('prauc', find('pr_auc', 'prauc', 'matured_prauc'), 'GATED')
    const performance = first(summary.performance, summary.matured_metrics, {}) || {}
    [['prauc-value',['pr_auc','prauc']],['rocauc-value',['roc_auc','rocauc']],['ks-value',['ks']],['brier-value',['brier']],['logloss-value',['log_loss','logloss']],['ece-value',['ece']]].forEach(([key, names]) => set(key, fmt(names.map(name => performance[name]).find(value => value !== undefined))))
  }
  const renderTimeline = (timeline, locked) => {
    const events = timeline?.events || []
    set('policy-timeline', events.length ? `${events.length} source-driven monitoring windows available.` : locked ? 'No timeline points retained in the public aggregate.' : 'Evidence unavailable until a genuine monitoring timeline is published.')
    set('monthly-performance', events.length ? 'Timeline available; unsupported windows remain explicitly labeled.' : 'Matured PR-AUC timeline unavailable.')
  }
  const renderState = (summary, alerts, timeline, alertError, timelineError) => {
    const status = summary.status || 'EVIDENCE_REVIEW'; const locked = finalLocked(summary, status); const validation = summary.validation || {}; const boundary = summary.claim_boundary || {}; const replay = summary.replay || {}; const reference = summary.reference || {}
    document.body.dataset.evidenceState = locked ? 'locked' : status === 'INPUT_BLOCKED' ? 'blocked' : 'review'
    set('status', status); set('mandatory-gates', validation.mandatory_gates ?? '—'); set('pass-gates', validation.pass ?? '—'); set('blocked-gates', validation.blocked ?? '—'); set('fail-gates', validation.fail ?? '—'); set('gate-summary', `${validation.pass ?? '—'} / ${validation.mandatory_gates ?? '—'}`); set('source-commit', summary.source_commit || 'public aggregate summary'); set('validator-version', summary.validator_version || 'source validator'); set('status-note', locked ? 'Monitoring governance is locked; each metric still reports its own evaluability.' : status === 'INPUT_BLOCKED' ? 'Monitoring framework is ready, but public replay evidence is still blocked.' : 'Monitoring evidence is under validator review.')
    set('matured-rows', fmt(first(replay.matured_outcome_rows, summary.matured_outcome_rows))); set('observation-rows', fmt(first(replay.observation_rows, summary.observation_rows))); set('matured-state', locked && boundary.matured_outcomes_available !== false ? 'AVAILABLE' : 'GATED'); set('matured-note', locked ? 'Matured evidence is evaluated only with retained support counts.' : 'Final monitoring replay has not been published in the current public source.')
    set('graph-reference', first(reference.graph_version, summary.graph_version) ? `GOVERNED VERSION · ${first(reference.graph_version, summary.graph_version)}` : 'NOT_EVALUABLE · governed version required'); set('reference-lineage', reference.baseline_id ? `${reference.baseline_id} · score / policy / graph lineage` : 'baseline · threshold · score · policy · graph · code hashes'); set('baseline-summary', reference.date_start ? `${reference.date_start} → ${reference.date_end || '—'} · ${fmt(reference.rows)} reference rows` : 'Baseline period and row count are unavailable in the current public source.')
    if (alertError) { set('alert-state', 'UNAVAILABLE'); set('alert-register-status', 'ALERT REGISTER UNAVAILABLE'); set('alert-register-note', 'The alert source could not be loaded; this is not the same as zero alerts.') } else if (!locked) { set('alert-state', 'GATED'); set('alert-register-status', 'ALERT REGISTER GATED'); set('alert-register-note', alerts?.note || 'No alert rows are published. This is not the same as zero alerts.') } else { const rows = alerts?.alerts || []; set('alert-state', rows.length ? fmt(rows.length) : 'NO ROWS'); set('alert-register-status', rows.length ? 'AVAILABLE' : 'NO ALERT ROWS'); set('alert-register-note', rows.length ? 'Source-driven alert rows are available for owner review.' : 'No alert rows were published in the locked source.') }
    set('review-utilization', '—'); set('overflow', '—'); set('reason-mix', '—'); set('policy-timeline', timelineError ? 'MONITORING TIMELINE UNAVAILABLE' : 'Evidence unavailable until a genuine monitoring timeline is published.')
    renderViews(summary, locked); renderOptionalMetrics(summary); renderTimeline(timeline, locked)
    if (!locked) document.querySelectorAll('[data-metric-status]').forEach(node => { if (!['score-psi','score-js','score-wasserstein'].includes(node.dataset.metricStatus)) node.textContent = 'GATED' })
  }
  Promise.allSettled(['part8_summary.json','part8_alert_summary.json','part8_monitoring_timeline.json'].map(file => fetch(`assets/data/${file}`, {cache:'no-store'}).then(response => response.ok ? response.json() : Promise.reject(file)))).then(results => {
    const summaryResult = results[0]; const alertsResult = results[1]; const timelineResult = results[2]
    if (summaryResult.status !== 'fulfilled') { document.body.dataset.evidenceState = 'error'; set('status', 'MONITORING EVIDENCE UNAVAILABLE'); set('status-note', 'The canonical monitoring summary could not be loaded; no monitoring claim is shown.'); set('alert-register-status', 'ALERT REGISTER UNAVAILABLE'); set('alert-register-note', 'Independent alert source cannot be interpreted without the canonical summary.'); return }
    renderState(summaryResult.value, alertsResult.status === 'fulfilled' ? alertsResult.value : null, timelineResult.status === 'fulfilled' ? timelineResult.value : null, alertsResult.status !== 'fulfilled', timelineResult.status !== 'fulfilled'); set('validator-version', summaryResult.value.validator_version || 'source validator')
  }).catch(() => { document.body.dataset.evidenceState = 'error'; set('status', 'MONITORING EVIDENCE UNAVAILABLE'); set('status-note', 'Source unavailable; no monitoring claim is shown.'); set('alert-register-status', 'ALERT REGISTER UNAVAILABLE'); set('alert-register-note', 'Source failure is not treated as zero alerts.') })
})()
