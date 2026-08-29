(() => {
  const summaryText = (value, fallback = '—') => value === null || value === undefined || value === '' ? fallback : String(value);
  const formatNumber = value => typeof value === 'number' ? new Intl.NumberFormat('en-US').format(value) : summaryText(value);
  const formatRate = value => typeof value === 'number' ? `${(value * 100).toFixed(2)}%` : summaryText(value);
  const setText = (key, value) => document.querySelectorAll(`[data-summary="${key}"]`).forEach(el => { el.textContent = value; });
  fetch('assets/data/part2_summary.json').then(response => response.ok ? response.json() : Promise.reject(new Error('summary unavailable'))).then(data => {
    setText('transactions', formatNumber(data.transactions));
    setText('fraudRate', formatRate(data.fraud_rate));
    setText('entityCoverage', data.users !== null || data.cards !== null ? `${formatNumber(data.users)} users · ${formatNumber(data.cards)} cards` : 'Pending');
    setText('dateCoverage', data.date_min && data.date_max ? `${data.date_min} → ${data.date_max}` : 'Pending');
    setText('statusLabel', data.status === 'READY' ? 'AUDIT READY' : 'AUDIT PENDING');
  }).catch(() => setText('statusLabel', 'AUDIT PENDING'));
  if (!window.gsap || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  gsap.from('.p2-hero .hero-copy > *, .hero-architecture', { y: 22, opacity: 0, duration: .7, stagger: .08, ease: 'power3.out' });
  gsap.utils.toArray('.metric-card, .table-card, .audit-list > div, .storage-pipeline > div, .deliver-list > div').forEach(group => gsap.from(group, { y: 18, opacity: 0, duration: .55, ease: 'power2.out', scrollTrigger: { trigger: group, start: 'top 88%', once: true } }));
  gsap.utils.toArray('.split, .pit-timeline > div').forEach(item => gsap.from(item, { scale: .96, opacity: 0, duration: .5, scrollTrigger: { trigger: item, start: 'top 88%', once: true } }));
})();
