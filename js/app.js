(() => {
  'use strict';
  const text = (selector, value, when = null) => {
    document.querySelectorAll(selector).forEach(node => {
      if (!when || when(node.textContent || '', node)) node.textContent = value;
    });
  };
  const replaceExact = (selector, from, to) => text(selector, to, value => value.trim() === from);
  const contains = needle => value => value.includes(needle);

  const reconcileContent = () => {
    const part = document.body?.dataset?.currentPart;
    if (!part) return;

    if (part === '1') {
      document.querySelectorAll('.hero-badge strong').forEach(node => {
        if ((node.textContent || '').trim() === 'IBM TabFormer Dataset') node.textContent = 'IBM Synthetic Credit Card Transactions (TabFormer)';
      });
      document.querySelectorAll('.tension-card').forEach(card => {
        if (card.querySelector('h3')?.textContent?.trim() === 'Govern Change Over Time') {
          const p = card.querySelector('p');
          if (p) p.textContent = 'Retrospectively monitor changes in data, scores, policy outcomes, customer behavior and graph structure under the offline governance contract.';
        }
      });
    }

    if (part === '2') {
      const section = document.querySelector('#temporal-split');
      if (section && !section.querySelector('.model-oot-scope-note')) {
        const note = document.createElement('div');
        note.className = 'governance-note model-oot-scope-note';
        note.innerHTML = '<img src="assets/icons/governance-claim-boundary.svg" alt=""><div><b>Split-scope clarification</b><span>Part 2 defines the broad data-governance OOT holdout. Part 5 uses a narrower governed final model-replay window inside the later-period evidence; the two row counts are therefore not expected to match.</span></div>';
        section.appendChild(note);
      }
    }

    if (part === '3') {
      replaceExact('[data-summary="statusLabel"]', 'PORTFOLIO PENDING', 'LOADING PORTFOLIO EVIDENCE');
    }

    if (part === '4') {
      text('[data-summary="statusNote"]', 'PIT contract validated · public evidence is a deterministic QA execution slice · no full-population behavioral claim', contains('full feature build runs offline'));
    }

    if (part === '6') {
      const why = document.querySelector('#network-intelligence .section-heading p');
      if (why && /Page 3 asks|Page 4 asks/.test(why.textContent || '')) {
        why.textContent = 'Transaction and behavioral layers describe what was unusual about the event. This graph layer asks whether relationship structure adds incremental context beyond those signals.';
      }
      const boundary = document.querySelector('#fraud-classification .split-boundary b');
      if (boundary && /PAGE 3 MODEL OOT SPLIT/.test(boundary.textContent || '')) boundary.textContent = 'GRAPH EXPERIMENT SPLIT ≠ PART 5 FROZEN-MODEL OOT EVALUATION SCOPE';
      document.querySelectorAll('.network-hero .hero-badges span').forEach(node => {
        if ((node.textContent || '').includes('GLOBAL FRAUD-CLASSIFICATION UPLIFT')) node.textContent = '⚠ GLOBAL GNN UPLIFT: NON-ROBUST / INCONCLUSIVE · SEGMENT-SPECIFIC SIGNALS RETAINED';
      });
    }

    if (part === '7') {
      text('[data-decision="policy-note"]', 'Loading validator-backed locked policy evidence…', contains('has not unlocked a final policy'));
      text('[data-decision="action-note"]', 'Loading final OOT replay evidence…', contains('FINAL REPLAY EVIDENCE UNAVAILABLE'));
      text('[data-decision="capacity-note"]', 'Loading public queue reconciliation…', value => /INPUT_BLOCKED|No final queue evidence/.test(value));
      const frozen = document.querySelector('#frozen-policy');
      if (frozen && !frozen.querySelector('.selected-policy-clarification')) {
        const note = document.createElement('div');
        note.className = 'interpretation selected-policy-clarification';
        note.innerHTML = '<b>Final selection</b><span><strong>P4 — Exposure-Weighted Probability</strong> is the frozen final policy. Graph-assisted P5 remained a candidate and was not selected as the final policy.</span>';
        frozen.appendChild(note);
      }
      const generalization = document.querySelector('#policy-generalization');
      if (generalization && !generalization.querySelector('.oot-scope-clarification')) {
        const note = document.createElement('div');
        note.className = 'interpretation oot-scope-clarification';
        note.innerHTML = '<b>OOT scope boundary</b><span>Final OOT did not tune the Part 5 model or Part 7 policy. It is not claimed as globally untouched across every later project layer, so the page treats it as a governed final replay rather than a universal pristine holdout.</span>';
        generalization.appendChild(note);
      }
    }

    if (part === '8') {
      text('[data-monitor="baseline-summary"]', 'Loading frozen pre-OOT reference evidence…', contains('unavailable in the current public source'));
      text('[data-monitor="policy-timeline"]', 'Loading source-driven monitoring timeline…', contains('Evidence unavailable until a genuine monitoring timeline'));
      text('[data-monitor="matured-note"]', 'Loading matured outcome evidence with retained support counts…', contains('Final monitoring replay has not been published'));
      text('[data-monitor="monthly-performance"]', 'Loading supported monthly retrospective performance…', contains('Matured PR-AUC timeline unavailable'));
      const section = document.querySelector('#drift-evaluability');
      if (section && !section.querySelector('.evaluability-source-note')) {
        const note = document.createElement('div');
        note.className = 'semantic-ribbon evaluability-source-note';
        note.innerHTML = '<b>PUBLIC EVALUABILITY NORMALIZATION</b><span>Retained upstream alert labels are not promoted blindly: a missing observed JS/PSI value or a missing family-matched Wasserstein threshold is displayed as NOT_EVALUABLE.</span>';
        section.appendChild(note);
      }
    }

    if (part === '9') {
      document.querySelectorAll('#claim-taxonomy .definition').forEach(card => {
        const h3 = card.querySelector('h3');
        const p = card.querySelector('p');
        const small = card.querySelector('small');
        if (h3) h3.textContent = 'KPI meaning when no retained result exists';
        if (p) p.textContent = 'Locked Part 7 populates capture, exposure capture, review rate, utilization and simulated cost. Metrics without retained execution evidence stay definition-only.';
        if (small) small.textContent = 'precision remains definition-only · executed policy KPIs are source-driven';
      });
      const health = document.querySelector('[data-audit="source-health-note"]');
      if (health && /gated|blocked/i.test(health.textContent || '')) health.textContent = 'Release audit is reconciled with locked Part 7 and Part 8 summaries; unavailable individual metrics remain explicitly NOT_EVALUABLE or NOT_AVAILABLE.';
    }
  };

  const run = () => {
    reconcileContent();
    window.setTimeout(reconcileContent, 350);
    window.setTimeout(reconcileContent, 1200);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
  window.addEventListener('load', run);
})();

(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!window.gsap) return;
  gsap.registerPlugin(ScrollTrigger);
  const progress = document.querySelector('.scroll-progress');
  if (progress) gsap.to(progress, { width: '100%', ease: 'none', scrollTrigger: { start: 0, end: 'max', scrub: .3 } });
  if (!reduce && window.Lenis) {
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(time => lenis.raf(time * 1000));
    gsap.ticker.lagSmoothing(0);
  }
})();
