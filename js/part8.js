(() => {
  'use strict';
  const qsa = s => [...document.querySelectorAll(s)];
  const setAll = (s, value) => qsa(s).forEach(el => { el.textContent = value; });
  const statusText = s => String(s || 'EVIDENCE_REVIEW').replaceAll('_', ' ');
  const lockedState = s => s === 'MONITORING_GOVERNANCE_LOCKED';

  const setEvidence = locked => {
    qsa('[data-p8-evidence-list] em').forEach(el => {
      el.textContent = locked ? 'AVAILABLE' : 'GATED';
      el.classList.toggle('available', locked);
      el.classList.toggle('blocked', !locked);
    });
  };

  Promise.all([
    fetch('assets/data/part8_summary.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : Promise.reject(new Error(`summary ${r.status}`))),
    fetch('assets/data/part8_alert_summary.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : ({ alerts: [] })),
    fetch('assets/data/part8_monitoring_timeline.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : ({ events: [] }))
  ]).then(([s, alerts, timeline]) => {
    const v = s.validation || {};
    const status = s.status || 'EVIDENCE_REVIEW';
    const locked = lockedState(status);
    const blocked = status === 'INPUT_BLOCKED';
    document.body.dataset.evidenceState = locked ? 'locked' : blocked ? 'blocked' : 'review';
    setAll('[data-p8-status]', statusText(status));
    setAll('[data-p8-technical]', statusText(s.technical_status || 'MONITORING_FRAMEWORK_READY'));
    setAll('[data-p8-total]', v.mandatory_gates ?? 72);
    setAll('[data-p8-pass]', v.pass ?? '—');
    setAll('[data-p8-blocked]', v.blocked ?? '—');
    setAll('[data-p8-fail]', v.fail ?? '—');
    setAll('[data-p8-operational]', s.two_clock?.operational || 'OPERATIONS_NOW');
    setAll('[data-p8-matured]', s.two_clock?.matured || 'OUTCOMES_MATURED');
    setAll('[data-p8-alert-count]', Array.isArray(alerts.alerts) ? alerts.alerts.length : '—');
    setAll('[data-p8-boundary]', locked ? 'validator-backed monitoring replay published' : 'source-driven evidence only');
    setAll('[data-p8-matured-state]', s.lifecycle?.matured_outcomes_available ? 'Retrospective matured outcomes available.' : 'Matured outcome evidence is not yet published.');
    setAll('[data-p8-final-heading]', locked ? 'Monitoring governance locked.' : 'Monitoring evidence remains source-driven.');
    setAll('[data-p8-final-copy]', locked ? 'The frozen baseline, replay evidence and governance checks are available as aggregate public artifacts. Row-level operational data remain private.' : 'Public outputs contain aggregate metrics, hashes, versions and claim boundaries only. Row-level scores, decisions, labels and private marts stay outside GitHub.');
    setEvidence(locked);
    const stateBox = document.querySelector('[data-p8-state-box]');
    if (stateBox) stateBox.classList.toggle('blocked', !locked);
    if (Array.isArray(timeline.events) && timeline.events.length) setAll('[data-p8-alert-count]', timeline.events.length);
  }).catch(() => {
    document.body.dataset.evidenceState = 'error';
    setAll('[data-p8-status]', 'EVIDENCE LOAD ERROR');
    setAll('[data-p8-technical]', 'STATUS UNAVAILABLE');
    setAll('[data-p8-pass],[data-p8-blocked],[data-p8-fail],[data-p8-alert-count]', '—');
    setEvidence(false);
  });

  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    gsap.from('.p8x-hero>*,.gate-strip article,.p8x-kpis article,.p8x-panel,.p8x-final', { y: 14, opacity: 0, duration: .48, stagger: .025, ease: 'power2.out' });
  }
})();
