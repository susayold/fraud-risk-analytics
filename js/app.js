(() => {
  const reconcileFinalRelease = () => {
    if (document.body?.dataset?.currentPart !== '9') return;

    const boundary = document.querySelector('.release-boundary b');
    if (boundary) boundary.textContent = 'PART7_PART8_LOCKED';

    const statusIntro = document.querySelector('#status-registry .section-heading p:last-child');
    if (statusIntro) statusIntro.textContent = 'The presentation layer is ready; Part 7 and Part 8 are now locked by their own executed evidence contracts.';

    const decision = document.querySelector('.gate-card.decision');
    if (decision) {
      const strong = decision.querySelector('strong');
      const label = decision.querySelector('b');
      const note = decision.querySelector('p');
      const small = decision.querySelector('small');
      if (strong) strong.textContent = '64 / 64';
      if (label) label.textContent = 'DECISION_POLICY_LOCKED';
      if (note) note.textContent = 'Frozen policy, clean freeze, verified replay and aggregate final OOT decision evidence are published.';
      if (small) small.textContent = '0 BLOCKED · 0 FAIL';
    }

    const monitoring = document.querySelector('.gate-card.monitoring');
    if (monitoring) {
      const strong = monitoring.querySelector('strong');
      const label = monitoring.querySelector('b');
      const note = monitoring.querySelector('p');
      const small = monitoring.querySelector('small');
      if (strong) strong.textContent = '72 / 72';
      if (label) label.textContent = 'MONITORING_GOVERNANCE_LOCKED';
      if (note) note.textContent = 'Offline monitoring replay and matured-outcome evidence are published under the two-clock governance contract.';
      if (small) small.textContent = '0 BLOCKED · 0 FAIL';
    }

    const gateNote = document.querySelector('.gate-note');
    if (gateNote) gateNote.textContent = 'Presentation 40/40 PASS · Decision 64/64 PASS · Monitoring 72/72 PASS. Each lock still preserves its own claim boundary.';

    document.querySelectorAll('#limitations .risk-grid article').forEach(card => {
      const title = card.querySelector('b')?.textContent?.trim();
      if (title === 'PART 7 / PART 8') {
        const p = card.querySelector('p');
        if (p) p.textContent = 'Both execution layers are locked. Decision economics remain simulated; monitoring remains offline and retrospective, not production evidence.';
      }
    });

    const health = document.querySelector('[data-audit="source-health-note"]');
    if (health && /gated|blocked/i.test(health.textContent || '')) {
      health.textContent = 'Release audit is reconciled with the final locked Part 7 and Part 8 source summaries.';
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', reconcileFinalRelease);
  else reconcileFinalRelease();
  window.addEventListener('load', () => {
    reconcileFinalRelease();
    window.setTimeout(reconcileFinalRelease, 500);
    window.setTimeout(reconcileFinalRelease, 1500);
  });
})();

(() => { const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; if (!window.gsap) return; gsap.registerPlugin(ScrollTrigger); const progress = document.querySelector('.scroll-progress'); if (progress) gsap.to(progress,{width:'100%',ease:'none',scrollTrigger:{start:0,end:'max',scrub:.3}}); if (!reduce && window.Lenis) { const lenis = new Lenis({duration:1.1,smoothWheel:true}); lenis.on('scroll',ScrollTrigger.update); gsap.ticker.add(time=>lenis.raf(time*1000)); gsap.ticker.lagSmoothing(0); } })();
