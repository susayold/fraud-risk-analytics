(() => {
  const safe = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const pct = value => Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(2)}%` : '—';
  const money = value => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : '—';
  const set = (key, value) => document.querySelectorAll(`[data-p7="${key}"]`).forEach(el => el.textContent = value);
  const empty = (id, message) => { const el = document.getElementById(id); if (el) el.innerHTML = `<div class="p7-empty">${safe(message)}</div>`; };
  fetch('assets/data/part7_summary.json').then(r => r.ok ? r.json() : Promise.reject()).then(data => {
    const blocked = data.status === 'INPUT_BLOCKED';
    const locked = data.status === 'DECISION_POLICY_LOCKED';
    set('status', data.status || 'REVIEW'); set('statusNote', blocked ? 'Frozen Part 5 row-level score artifact is required before policy search.' : locked ? 'Policy freeze and final replay evidence are available.' : 'Policy evidence is in review.');
    document.querySelector('.p7-status-card')?.setAttribute('data-status', blocked ? 'blocked' : locked ? 'locked' : 'review');
    const p = data.policy || {}, e = data.final_evidence || {};
    set('reviewThreshold', p.review_threshold == null ? '—' : Number(p.review_threshold).toFixed(4)); set('blockThreshold', p.block_threshold == null ? '—' : Number(p.block_threshold).toFixed(4)); set('capacity', p.review_capacity == null ? '—' : pct(p.review_capacity));
    set('allowRate', pct(e.allow_rate)); set('reviewRate', pct(e.review_rate)); set('blockRate', pct(e.block_rate)); set('totalCost', money(e.simulated_total_cost));
    set('profile', data.policy_profile || 'Not selected'); set('scoreVersion', data.score_version || 'Not resolved'); set('policyVersion', data.policy_version || 'Not frozen');
    if (blocked) { ['frontier-chart','capacity-chart','cost-chart'].forEach(id => empty(id, 'Aggregate evidence is withheld until the approved Part 5 score artifact is supplied.')); }
    else if (e.fraud_capture == null) { ['frontier-chart','capacity-chart','cost-chart'].forEach(id => empty(id, 'No final aggregate has been published for this policy stage.')); }
  }).catch(() => { set('status','EVIDENCE REVIEW'); set('statusNote','Summary unavailable; no policy claim is shown.'); ['frontier-chart','capacity-chart','cost-chart'].forEach(id => empty(id, 'Part 7 summary unavailable.')); });
})();
