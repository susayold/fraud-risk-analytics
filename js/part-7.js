(() => {
  'use strict';
  const nodes = key => [...document.querySelectorAll(`[data-decision="${key}"]`)]
  const set = (key, value) => nodes(key).forEach(node => { node.textContent = value })
  const finite = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
  const raw = value => finite(value) ? Number(value) : null
  const pct = value => finite(value) ? `${(Number(value) * 100).toFixed(2)}%` : '—'
  const pct4 = value => finite(value) ? `${(Number(value) * 100).toFixed(4)}%` : '—'
  const money = value => finite(value) ? Number(value).toLocaleString('en-US', {maximumFractionDigits: 2}) : '—'
  const threshold = value => finite(value) ? Number(value).toFixed(6) : '—'
  const first = (...values) => values.find(value => value !== undefined && value !== null)
  const clean = value => String(value || '—').replaceAll('_', ' ')
  const lockedStatus = 'DECISION_POLICY_LOCKED'

  const hideLockedEvidence = () => {
    set('action-state', '—'); set('economics-state', '—'); set('capacity-reconciliation', 'EVIDENCE UNAVAILABLE')
    set('capacity-note', 'No final queue evidence is published while Part 7 is INPUT_BLOCKED.')
    document.querySelectorAll('[data-action-chart],[data-cost-chart]').forEach(node => { node.innerHTML = '<div class="evidence-placeholder">FINAL REPLAY EVIDENCE UNAVAILABLE</div>' })
  }
  const getFinal = data => first(data.final_evidence, data.final_replay, data.final_oot, data.final_oot_evidence, data.action_mix)
  const getConfirmation = data => first(data.confirmation, data.confirmation_evidence, data.pre_oot_confirmation, data.generalization?.confirmation)
  const getEconomics = data => first(data.economics, data.final_evidence?.economics, data.final_replay?.economics)

  const renderActionChart = evidence => {
    const target = document.querySelector('[data-action-chart]'); if (!target) return
    const rates = [raw(evidence?.allow_rate), raw(evidence?.review_rate), raw(evidence?.block_rate)]
    if (rates.some(value => value === null)) { target.innerHTML = '<div class="evidence-placeholder">FINAL REPLAY EVIDENCE UNAVAILABLE</div>'; return }
    target.innerHTML = `<span class="bar allow" style="width:${rates[0] * 100}%"></span><span class="bar review" style="width:${rates[1] * 100}%"></span><span class="bar block" style="width:${Math.max(rates[2] * 100, .18)}%"></span>`
  }
  const renderCostChart = (evidence, economics) => {
    const target = document.querySelector('[data-cost-chart]'); if (!target) return
    const selected = raw(first(evidence?.simulated_total_cost, economics?.selected_cost, economics?.selected_policy_cost))
    const baseline = raw(first(evidence?.allow_all_simulated_total_cost, economics?.allow_all_cost, economics?.allow_all_simulated_total_cost))
    if (selected === null || baseline === null) { target.innerHTML = '<div class="evidence-placeholder">COST DECOMPOSITION NOT AVAILABLE IN PUBLIC AGGREGATE</div>'; return }
    const max = Math.max(selected, baseline)
    target.innerHTML = `<div class="cost-bar-row"><span>Allow All</span><i style="--bar-width:${baseline / max * 100}%"></i><strong>${money(baseline)}</strong></div><div class="cost-bar-row"><span>Selected</span><i style="--bar-width:${selected / max * 100}%"></i><strong>${money(selected)}</strong></div>`
  }
  const renderGeneralization = (data, finalEvidence) => {
    const confirmation = getConfirmation(data) || {}; const final = finalEvidence || {}
    const pairs = [['confirmation-fraud-capture', first(confirmation.fraud_capture, confirmation.fraud_transaction_capture)], ['confirmation-exposure-capture', first(confirmation.fraud_exposure_capture, confirmation.exposure_capture)], ['confirmation-cost', first(confirmation.simulated_total_cost, confirmation.total_cost)], ['oot-fraud-capture', first(final.fraud_capture, final.fraud_transaction_capture)], ['oot-exposure-capture', first(final.fraud_exposure_capture, final.exposure_capture)], ['oot-cost', first(final.simulated_total_cost, final.total_cost)]]
    pairs.forEach(([key, value]) => set(key, key.includes('cost') ? money(value) : pct(value)))
    set('confirmation-state', confirmation.fraud_capture === undefined ? 'Evidence unavailable' : 'Pre-OOT confirmation')
    set('oot-state', final.fraud_capture === undefined ? 'Evidence unavailable' : 'Retrospective replay')
  }
  const renderLocked = data => {
    const v = data.validation || {}; const policy = data.policy || {}; const evidence = getFinal(data) || {}; const economics = getEconomics(data) || {}
    set('policy-note', 'Validator-backed policy identity and thresholds are published from the locked source object.')
    set('score-version', first(data.score_version, data.score?.version, '—')); set('policy-version', first(data.policy_version, policy.version, '—')); set('policy-profile', first(data.policy_profile, policy.profile, '—'))
    set('review-threshold', threshold(policy.review_threshold)); set('block-threshold', threshold(policy.block_threshold)); set('review-capacity', pct(policy.review_capacity)); set('review-marker', threshold(policy.review_threshold)); set('block-marker', threshold(policy.block_threshold))
    set('allow-rate', pct(evidence.allow_rate)); set('review-rate', pct(evidence.review_rate)); set('block-rate', pct4(evidence.block_rate)); set('fraud-capture', pct(evidence.fraud_capture)); set('exposure-capture', pct(evidence.fraud_exposure_capture)); set('legit-block-rate', pct4(evidence.legitimate_block_rate))
    set('final-rows-label', finite(evidence.rows) ? `${Number(evidence.rows).toLocaleString('en-US')} replayed rows` : 'Final replay'); set('action-note', 'The frozen policy changes only a small share of transactions in the retrospective final replay.'); set('action-state', 'LOCKED'); set('economics-state', 'SIMULATED')
    const selectedCost = first(evidence.simulated_total_cost, economics.selected_cost); const baseline = first(evidence.allow_all_simulated_total_cost, economics.allow_all_cost); const delta = raw(selectedCost) !== null && raw(baseline) !== null ? raw(selectedCost) - raw(baseline) : null; const deltaPct = delta !== null && raw(baseline) ? delta / raw(baseline) : null
    set('selected-cost', money(selectedCost)); set('allow-all-cost', money(baseline)); set('cost-delta-pct', deltaPct === null ? '—' : `${(deltaPct * 100).toFixed(1)}% lower simulated cost`)
    set('capacity-reconciliation', finite(evidence.review_rate) && finite(policy.review_capacity) ? (raw(evidence.review_rate) <= raw(policy.review_capacity) ? 'RECONCILED' : 'CAPACITY CHECK FAILED') : 'EVIDENCE UNAVAILABLE'); set('capacity-note', finite(evidence.review_rate) ? 'Final replay review rate is compared with the frozen capacity constraint.' : 'Final queue evidence is not retained in the public aggregate.')
    set('lock-summary', `${v.pass ?? '—'} / ${v.mandatory_gates ?? '—'} PASS · ${v.blocked ?? '—'} BLOCKED`); renderActionChart(evidence); renderCostChart(evidence, economics); renderGeneralization(data, evidence)
  }
  const renderState = (data, status) => {
    const validation = data.validation || {}; const eligible = status === lockedStatus && validation.pass === validation.mandatory_gates && validation.blocked === 0 && validation.fail === 0 && validation.final_lock_eligible === true
    document.body.dataset.evidenceState = eligible ? 'locked' : status === 'INPUT_BLOCKED' ? 'blocked' : 'review'
    set('status', eligible ? lockedStatus : status); set('mandatory-gates', validation.mandatory_gates ?? '—'); set('pass-gates', validation.pass ?? '—'); set('blocked-gates', validation.blocked ?? '—'); set('fail-gates', validation.fail ?? '—'); set('source-commit', first(data.source_commit, 'public aggregate summary')); set('status-note', eligible ? 'Policy freeze and final replay evidence are published.' : status === 'INPUT_BLOCKED' ? 'Decision policy and final outcomes are withheld until genuine replay evidence is imported.' : 'Policy evidence is under validator review.')
    set('lock-summary', eligible ? `${validation.pass} / ${validation.mandatory_gates} PASS` : `${validation.pass ?? '—'} / ${validation.mandatory_gates ?? '—'} PASS · ${validation.blocked ?? '—'} BLOCKED`)
    if (!eligible) { hideLockedEvidence(); set('policy-note', 'Current public evidence has not unlocked a final policy. Thresholds remain withheld rather than guessed.'); renderGeneralization(data, null) } else renderLocked(data)
  }
  Promise.allSettled(['part7_summary.json', 'project_status.json'].map(file => fetch(`assets/data/${file}`, {cache: 'no-store'}).then(response => response.ok ? response.json() : Promise.reject(file)))).then(results => {
    const data = {}; results.forEach((result, index) => { if (result.status === 'fulfilled') data[index === 0 ? 'summary' : 'project'] = result.value })
    if (!data.summary) { document.body.dataset.evidenceState = 'error'; set('status', 'DECISION EVIDENCE UNAVAILABLE'); set('status-note', 'Source unavailable; no decision claim is shown.'); hideLockedEvidence(); return }
    renderState(data.summary, data.summary.status || data.project?.layers?.part7?.status || 'EVIDENCE_REVIEW'); set('validator-version', data.summary.validator_version || 'source validator')
  }).catch(() => { document.body.dataset.evidenceState = 'error'; set('status', 'DECISION EVIDENCE UNAVAILABLE'); set('status-note', 'Source unavailable; no decision claim is shown.'); hideLockedEvidence() })
})()
