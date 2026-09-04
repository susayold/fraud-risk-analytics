(() => {
  'use strict';

  const unavailable = 'EVIDENCE UNAVAILABLE';
  const qsa = selector => [...document.querySelectorAll(selector)];
  const finite = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  const number = value => finite(value) ? Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 }) : unavailable;
  const percent = value => finite(value) ? `${(Number(value) * 100).toFixed(3)}%` : unavailable;
  const set = (key, value) => qsa(`[data-p2="${key}"]`).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = value === unavailable ? 'unavailable' : 'available';
  });
  const setRecon = (key, value, state = 'available') => qsa(`[data-p2-recon="${key}"]`).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = state;
  });
  const setInvariant = (key, value, state = 'available') => qsa(`[data-p2-invariant="${key}"]`).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = state;
  });
  const setSplit = (name, field, value) => qsa(`[data-p2-split="${name}"][data-split-field="${field}"]`).forEach(el => {
    el.textContent = value;
    el.dataset.sourceState = value === unavailable ? 'unavailable' : 'available';
  });
  const setUnavailable = () => {
    ['transactions', 'fields', 'fraud-transactions', 'fraud-rate', 'date-range', 'users', 'cards', 'merchants', 'active-days', 'source-file'].forEach(key => set(key, unavailable));
    ['SOURCE_CSV', 'PARQUET', 'DUCKDB_RAW', 'STANDARDIZED', 'TRANSACTION_BASE', 'MODEL_SPLITS'].forEach(key => setRecon(key, unavailable, 'unavailable'));
    ['population-loss', 'row-multiplication', 'fraud-drift'].forEach(key => setInvariant(key, unavailable, 'unavailable'));
    ['DEVELOPMENT', 'VALIDATION', 'OUT_OF_TIME_OOT'].forEach(name => ['date', 'rows', 'fraud'].forEach(field => setSplit(name, field, unavailable)));
  };

  fetch('assets/data/part2_summary.json', { cache: 'no-store' })
    .then(response => response.ok ? response.json() : Promise.reject(new Error(`summary ${response.status}`)))
    .then(data => {
      const valid = data && finite(data.transactions) && finite(data.fraud_transactions) && Array.isArray(data.reconciliation) && Array.isArray(data.split_summary);
      if (!valid) throw new Error('invalid part2 summary');
      set('transactions', number(data.transactions));
      set('fields', number(15));
      set('fraud-transactions', number(data.fraud_transactions));
      set('fraud-rate', percent(data.fraud_rate));
      set('date-range', `${data.date_min} → ${data.date_max}`);
      set('users', number(data.users));
      set('cards', number(data.cards));
      set('merchants', number(data.merchants));
      set('active-days', number(data.active_days));
      set('source-file', data.source_file || unavailable);

      const rows = data.reconciliation;
      const expectedRows = Number(data.transactions);
      const rowCounts = rows.map(row => Number(row.row_count));
      const allRowsReconcile = rows.length === 6 && rowCounts.every(value => value === expectedRows);
      const fraudCounts = rows.filter(row => finite(row.fraud_rows)).map(row => Number(row.fraud_rows));
      const allFraudReconcile = fraudCounts.length === 5 && fraudCounts.every(value => value === Number(data.fraud_transactions));
      rows.forEach(row => setRecon(row.layer, allRowsReconcile ? number(row.row_count) : 'RECONCILIATION ERROR', allRowsReconcile ? 'available' : 'error'));
      const invariant = allRowsReconcile && allFraudReconcile;
      setInvariant('population-loss', invariant ? '0' : 'RECONCILIATION ERROR', invariant ? 'available' : 'error');
      setInvariant('row-multiplication', invariant ? '0' : 'RECONCILIATION ERROR', invariant ? 'available' : 'error');
      setInvariant('fraud-drift', invariant ? '0' : 'RECONCILIATION ERROR', invariant ? 'available' : 'error');

      data.split_summary.forEach(split => {
        const name = split.split_name;
        setSplit(name, 'date', `${split.date_start} → ${split.date_end}`);
        setSplit(name, 'rows', `${number(split.row_count)} transactions`);
        setSplit(name, 'fraud', `${number(split.fraud_count)} fraud · ${percent(Number(split.fraud_count) / Number(split.row_count))}`);
      });
      document.body.dataset.evidenceState = invariant ? 'ready' : 'error';
    })
    .catch(() => {
      document.body.dataset.evidenceState = 'error';
      setUnavailable();
    });

  if (!window.gsap || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  gsap.from('.data-hero .hero-copy > *, .data-pipeline-visual', { y: 22, opacity: 0, duration: .7, stagger: .08, ease: 'power3.out' });
  gsap.utils.toArray('.hero-metrics article, .contract-facts>div, .schema-grid>span, .preservation-ladder>div, .missing-chart>div, .duplicate-grid>div, .split-chart article, .baseline-grid article, .handoff-grid article, .summary-cards article').forEach(group => gsap.from(group, { y: 18, opacity: 0, duration: .5, ease: 'power2.out', scrollTrigger: { trigger: group, start: 'top 90%', once: true } }));
})();
