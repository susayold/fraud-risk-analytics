(() => {
  'use strict';
  const qsa = (s) => [...document.querySelectorAll(s)];
  const set = (key, value) => qsa(`[data-p7="${key}"]`).forEach(el => { el.textContent = value; });
  const finite = v => v !== null && v !== undefined && Number.isFinite(Number(v));
  const pct = v => finite(v) ? `${(Number(v) * 100).toFixed(2)}%` : '—';
  const num = v => finite(v) ? Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 }) : '—';
  const threshold = v => finite(v) ? Number(v).toFixed(4) : '—';
  const money = v => finite(v) ? Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 }) : '—';
  const statusText = s => String(s || 'EVIDENCE REVIEW').replaceAll('_', ' ');
  const isLocked = s => s === 'DECISION_POLICY_LOCKED';

  const setEvidenceAvailability = locked => {
    qsa('[data-p7-evidence-list] em').forEach(el => {
      el.textContent = locked ? 'AVAILABLE' : 'GATED';
      el.classList.toggle('available', locked);
      el.classList.toggle('blocked', !locked);
    });
    qsa('.result-grid article').forEach(el => el.dataset.available = locked ? 'true' : 'false');
    qsa('.evidence-slot').forEach(el => el.classList.toggle('is-available', locked));
  };

  fetch('assets/data/part7_summary.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
    .then(data => {
      const status = data.status || 'EVIDENCE_REVIEW';
      const locked = isLocked(status);
      const blocked = status === 'INPUT_BLOCKED';
      const v = data.validation || {};
      const p = data.policy || {};
      const e = data.final_evidence || {};
      document.body.dataset.evidenceState = locked ? 'locked' : blocked ? 'blocked' : 'review';

      set('status', statusText(status));
      set('statusNote', locked ? 'Policy freeze and final replay evidence are published.' : blocked ? 'Public evidence is still gated; private execution does not change the public claim boundary.' : 'Policy evidence is under validator review.');
      set('publicBoundary', locked ? 'validator-backed replay published' : 'source-driven evidence only');
      set('mandatoryGates', v.mandatory_gates ?? 64);
      set('passGates', v.pass ?? '—');
      set('blockedGates', v.blocked ?? '—');
      set('failGates', v.fail ?? '—');
      set('lockSummary', locked ? `${v.pass ?? '—'} / ${v.mandatory_gates ?? '—'} PASS` : `${v.pass ?? '—'} / ${v.mandatory_gates ?? '—'} PASS · ${v.blocked ?? '—'} BLOCKED`);
      set('scoreVersion', data.score_version || 'Not resolved');
      set('policyVersion', data.policy_version || 'Not frozen');
      set('reviewThreshold', threshold(p.review_threshold));
      set('blockThreshold', threshold(p.block_threshold));
      set('capacity', pct(p.review_capacity));
      set('allowRate', pct(e.allow_rate));
      set('reviewRate', pct(e.review_rate));
      set('blockRate', pct(e.block_rate));
      set('fraudCapture', pct(e.fraud_capture));
      set('exposureCapture', pct(e.fraud_exposure_capture));
      set('legitBlockRate', pct(e.legitimate_block_rate));
      set('totalCost', money(e.simulated_total_cost));
      set('capacityEvidence', locked ? `Review rate ${pct(e.review_rate)} · capacity ${pct(p.review_capacity)}` : 'Evidence unlocks after genuine replay.');
      set('costEvidence', locked ? `Simulated total cost ${money(e.simulated_total_cost)}` : 'Evidence unlocks after genuine replay.');
      set('finalHeading', locked ? 'Decision policy locked — handoff ready for monitoring.' : 'Decision evidence remains source-driven.');
      set('finalCopy', locked ? 'Part 8 can consume the frozen decision mart and policy lineage. Public decision claims remain aggregate-only and simulated where economics are involved.' : 'Part 8 consumes a frozen policy and decision mart. The public website changes to locked only when the genuine Part 7 validator and final replay evidence say so.');
      setEvidenceAvailability(locked);

      const box = document.querySelector('[data-p7-state-box]');
      if (box) box.classList.toggle('blocked', !locked);
    })
    .catch(() => {
      document.body.dataset.evidenceState = 'error';
      set('status', 'EVIDENCE LOAD ERROR');
      set('statusNote', 'Summary unavailable; no decision claim is shown.');
      set('publicBoundary', 'summary unavailable');
      set('lockSummary', 'EVIDENCE UNAVAILABLE');
      setEvidenceAvailability(false);
    });

  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    gsap.from('.p7x-hero>*,.gate-strip article,.p7x-kpis article,.p7x-panel,.p7x-final', { y: 14, opacity: 0, duration: .48, stagger: .025, ease: 'power2.out' });
  }
})();
