(() => {
  const nf = new Intl.NumberFormat('en-US');
  const money = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
  const num = value => Number(value);
  const valid = value => value !== null && value !== undefined && value !== '' && Number.isFinite(num(value));
  const number = value => valid(value) ? nf.format(num(value)) : '—';
  const currency = value => valid(value) ? money.format(num(value)) : '—';
  const rate = value => valid(value) ? `${(num(value) * 100).toFixed(2)}%` : '—';
  const share = value => valid(value) ? `${(num(value) * 100).toFixed(1)}%` : '—';
  const lift = value => valid(value) ? `${num(value).toFixed(2)}x` : '—';
  const safe = value => String(value ?? '—').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
  const setText = (key, value) => document.querySelectorAll(`[data-summary="${key}"]`).forEach(el => { el.textContent = value; });
  const cell = value => `<td>${safe(value)}</td>`;
  const chartRefs = [];
  const chartTheme = { text: '#5f6b64', axis: '#dfe5e0', green: '#198754', greenSoft: '#b8dfc5', red: '#d8343a', amber: '#e28a00', blue: '#2671cf', purple: '#6f2dbd' };

  const initChart = id => {
    const node = document.getElementById(id);
    if (!node || !window.echarts) return null;
    const chart = window.echarts.init(node, null, { renderer: 'canvas' });
    chartRefs.push(chart);
    return chart;
  };
  const tooltip = (formatter, extra = {}) => Object.assign({ trigger: 'axis', backgroundColor: '#13231b', borderWidth: 0, textStyle: { color: '#fff', fontSize: 11 }, formatter }, extra);
  const axis = { axisLine: { lineStyle: { color: chartTheme.axis } }, axisTick: { show: false }, axisLabel: { color: chartTheme.text, fontSize: 10 } };

  function renderTrend(data) {
    const rows = [...(data.monthly_trend || [])].sort((a, b) => String(a.month).localeCompare(String(b.month)));
    const chart = initChart('trend-chart');
    if (!chart || !rows.length) return;
    const months = rows.map(row => row.month);
    chart.setOption({ animationDuration: 700, grid: { left: 48, right: 28, top: 24, bottom: 52 }, legend: { top: 0, right: 0, textStyle: { color: chartTheme.text, fontSize: 10 } }, tooltip: tooltip(params => { const row = rows[params[0]?.dataIndex] || {}; return `<b>${safe(row.month)}</b><br>Fraud rate: ${rate(row.fraud_rate)}<br>Fraud-labeled txns: ${number(row.fraud_transactions)}<br>Transactions: ${number(row.transactions)}`; }), xAxis: { ...axis, type: 'category', data: months, axisLabel: { ...axis.axisLabel, interval: Math.max(0, Math.floor(months.length / 10)), rotate: 25 } }, yAxis: [{ ...axis, type: 'value', name: 'Rate', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, { ...axis, type: 'value', name: 'Fraud txns', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, splitLine: { show: false }, axisLabel: { ...axis.axisLabel, formatter: value => nf.format(value) } }], series: [{ name: 'Fraud rate', type: 'line', smooth: true, yAxisIndex: 0, symbol: 'none', lineStyle: { width: 2, color: chartTheme.green }, areaStyle: { color: 'rgba(25,135,84,.10)' }, data: rows.map(row => num(row.fraud_rate) * 100) }, { name: 'Fraud transactions', type: 'bar', yAxisIndex: 1, barMaxWidth: 8, itemStyle: { color: chartTheme.greenSoft }, data: rows.map(row => num(row.fraud_transactions)) }] });
    const peak = rows.reduce((best, row) => num(row.fraud_rate) > num(best?.fraud_rate) ? row : best, rows[0]);
    setText('peakMonth', peak ? `${safe(peak.month)} · ${rate(peak.fraud_rate)}` : '—');
    setText('yearRange', rows.length ? `${String(rows[0].month).slice(0, 4)} → ${String(rows.at(-1).month).slice(0, 4)}` : '—');
  }

  function renderChannels(rows) {
    const chart = initChart('channel-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 108, right: 24, top: 12, bottom: 38 }, tooltip: tooltip(params => { const row = rows[params[0]?.dataIndex] || {}; return `<b>${safe(row.segment_value)}</b><br>Fraud rate: ${rate(row.fraud_rate)}<br>Lift: ${lift(row.fraud_lift)}<br>Fraud share: ${share(row.fraud_capture_share)}`; }), xAxis: { ...axis, type: 'value', axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, yAxis: { ...axis, type: 'category', data: rows.map(row => row.segment_value), inverse: true }, series: [{ type: 'bar', barMaxWidth: 26, itemStyle: { color: chartTheme.green, borderRadius: [0, 6, 6, 0] }, data: rows.map(row => num(row.fraud_rate) * 100) }] });
    const table = document.getElementById('channel-table');
    if (table) table.innerHTML = rows.map(row => `<tr>${cell(row.segment_value)}${cell(number(row.transactions))}<td class="emphasis">${rate(row.fraud_rate)}</td><td>${lift(row.fraud_lift)}</td><td>${share(row.fraud_capture_share)}</td></tr>`).join('');
  }

  function renderAmount(rows) {
    const order = ['NEGATIVE / REFUND-LIKE', 'ZERO', '>0–25', '25–50', '50–100', '100–250', '250–500', '500+'];
    const sorted = [...rows].sort((a, b) => order.indexOf(a.segment_value) - order.indexOf(b.segment_value));
    const chart = initChart('amount-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 52, right: 24, top: 18, bottom: 44 }, tooltip: tooltip(params => { const row = sorted[params[0]?.dataIndex] || {}; return `<b>${safe(row.segment_value)}</b><br>Transaction share: ${share(row.transaction_share)}<br>Fraud lift: ${lift(row.fraud_lift)}<br>Fraud txns: ${number(row.fraud_transactions)}<br>Amount capture: ${share(row.fraud_amount_capture_share)}`; }, { trigger: 'item' }), xAxis: { ...axis, type: 'value', name: 'Transaction share', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, yAxis: { ...axis, type: 'value', name: 'Fraud lift', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, axisLabel: { ...axis.axisLabel, formatter: value => `${value}x` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, series: [{ type: 'scatter', symbolSize: value => Math.max(12, Math.min(38, Math.sqrt(value[2]) * .65)), itemStyle: { color: chartTheme.green, opacity: .82 }, data: sorted.map(row => ({ value: [num(row.transaction_share) * 100, num(row.fraud_lift), num(row.fraud_transactions)], name: row.segment_value })) }] });
    const table = document.getElementById('amount-table');
    if (table) table.innerHTML = sorted.map(row => `<tr>${cell(row.segment_value)}${cell(number(row.transactions))}<td>${rate(row.fraud_rate)}</td><td class="emphasis">${lift(row.fraud_lift)}</td><td>${share(row.fraud_amount_capture_share)}</td><td><span class="support ${row.support_status === 'SUFFICIENT' ? 'good' : 'low'}">${safe(row.support_status)}</span></td></tr>`).join('');
  }

  function renderMcc(rows) {
    const top = [...rows].sort((a, b) => num(b.fraud_lift) - num(a.fraud_lift)).slice(0, 10).reverse();
    const chart = initChart('mcc-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 48, right: 25, top: 10, bottom: 30 }, tooltip: tooltip(params => { const row = top[params[0]?.dataIndex] || {}; return `<b>MCC ${safe(row.segment_value)}</b><br>Lift: ${lift(row.fraud_lift)}<br>Fraud rate: ${rate(row.fraud_rate)}<br>Fraud txns: ${number(row.fraud_transactions)}`; }), xAxis: { ...axis, type: 'value', axisLabel: { ...axis.axisLabel, formatter: value => `${value}x` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, yAxis: { ...axis, type: 'category', data: top.map(row => row.segment_value), inverse: false }, series: [{ type: 'bar', barMaxWidth: 18, itemStyle: { color: chartTheme.blue, borderRadius: [0, 5, 5, 0] }, data: top.map(row => num(row.fraud_lift)) }] });
    const table = document.getElementById('mcc-table');
    if (table) table.innerHTML = [...rows].sort((a, b) => num(b.fraud_lift) - num(a.fraud_lift)).slice(0, 8).map(row => `<tr>${cell(row.segment_value)}${cell(number(row.transactions))}${cell(number(row.fraud_transactions))}<td class="emphasis">${lift(row.fraud_lift)}</td><td><span class="priority ${row.priority_class || 'MONITOR'}">${safe(row.priority_class || 'MONITOR')}</span></td></tr>`).join('');
  }

  function renderGeography(rows) {
    const top = [...rows].sort((a, b) => num(b.fraud_capture_share) - num(a.fraud_capture_share)).slice(0, 10).reverse();
    const unknown = rows.find(row => row.segment_value === '<UNKNOWN>');
    setText('unknownStateShare', share(unknown?.transaction_share));
    setText('unknownStateFraudShare', share(unknown?.fraud_capture_share));
    const chart = initChart('geo-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 70, right: 26, top: 12, bottom: 32 }, tooltip: tooltip(params => { const row = top[params[0]?.dataIndex] || {}; return `<b>${safe(row.segment_value)}</b><br>Fraud capture: ${share(row.fraud_capture_share)}<br>Lift: ${lift(row.fraud_lift)}<br>Transactions: ${number(row.transactions)}`; }), xAxis: { ...axis, type: 'value', axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, yAxis: { ...axis, type: 'category', data: top.map(row => row.segment_value), inverse: true }, series: [{ type: 'bar', barMaxWidth: 20, itemStyle: { color: chartTheme.green, borderRadius: [0, 5, 5, 0] }, data: top.map(row => num(row.fraud_capture_share) * 100) }] });
  }

  function renderConcentration(concentration) {
    const types = ['USER', 'CARD', 'MERCHANT_IDENTIFIER'];
    const chart = initChart('concentration-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 40, right: 20, top: 20, bottom: 42 }, tooltip: tooltip(params => { const row = concentration[types[params[0]?.dataIndex]] || {}; return `<b>${safe(row.entity_type)}</b><br>Top 1% fraud share: ${share(row.top_1pct_fraud_share)}<br>Top 100 fraud share: ${share(row.top_100_fraud_share)}`; }), xAxis: { ...axis, type: 'category', data: types.map(type => type === 'MERCHANT_IDENTIFIER' ? 'MERCHANT' : type) }, yAxis: { ...axis, type: 'value', axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, series: [{ type: 'bar', barMaxWidth: 44, itemStyle: { color: chartTheme.purple, borderRadius: [6, 6, 0, 0] }, data: types.map(type => num(concentration[type]?.top_1pct_fraud_share) * 100) }] });
    const holder = document.getElementById('concentration-cards');
    if (holder) holder.innerHTML = types.map(type => { const row = concentration[type] || {}; return `<article class="concentration-card"><span>${safe(type.replace('_', ' '))}</span><b>${share(row.top_1pct_fraud_share)}</b><small>top 1% fraud share · ${number(row.fraud_affected_entities)} affected entities · ${number(row.repeat_fraud_entities)} repeat-label entities</small></article>`; }).join('');
  }

  function renderPriority(rows) {
    const chartRows = [...rows].slice(0, 12);
    const colors = { PRIORITY_1: chartTheme.red, PRIORITY_2: chartTheme.amber, MONITOR: chartTheme.blue, LOW_PRIORITY: '#87918b' };
    const chart = initChart('priority-chart');
    if (chart) chart.setOption({ animationDuration: 700, grid: { left: 52, right: 24, top: 30, bottom: 50 }, legend: { top: 0, textStyle: { color: chartTheme.text, fontSize: 10 } }, tooltip: tooltip(params => { const row = chartRows[params[0]?.dataIndex] || {}; return `<b>${safe(row.segment_type)} · ${safe(row.segment_value)}</b><br>Transaction share: ${share(row.transaction_share)}<br>Lift: ${lift(row.fraud_lift)}<br>Fraud capture: ${share(row.fraud_capture_share)}<br>Class: ${safe(row.priority_class)}`; }, { trigger: 'item' }), xAxis: { ...axis, type: 'value', name: 'Transaction share', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, axisLabel: { ...axis.axisLabel, formatter: value => `${value}%` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, yAxis: { ...axis, type: 'value', name: 'Fraud lift', nameTextStyle: { color: chartTheme.text, fontSize: 10 }, axisLabel: { ...axis.axisLabel, formatter: value => `${value}x` }, splitLine: { lineStyle: { color: '#edf1ed' } } }, series: Object.keys(colors).map(priority => ({ name: priority, type: 'scatter', symbolSize: value => Math.max(10, Math.min(34, Math.sqrt(value[2]) * .75)), itemStyle: { color: colors[priority], opacity: .82 }, data: chartRows.filter(row => row.priority_class === priority).map(row => ({ value: [num(row.transaction_share) * 100, num(row.fraud_lift), num(row.fraud_transactions)], name: `${row.segment_type} · ${row.segment_value}` })) })) });
    const list = document.getElementById('priority-list');
    if (list) list.innerHTML = chartRows.slice(0, 10).map(row => `<div class="priority-row"><span class="class ${row.priority_class === 'PRIORITY_1' ? 'p1' : row.priority_class === 'PRIORITY_2' ? 'p2' : 'monitor'}">${safe(row.priority_class)}</span><b title="${safe(row.segment_type)} · ${safe(row.segment_value)}">${safe(row.segment_type)} · ${safe(row.segment_value)}</b><small>${lift(row.fraud_lift)}<br>${share(row.fraud_capture_share)} capture</small></div>`).join('');
  }

  function renderStability(rows) {
    const holder = document.getElementById('stability-grid');
    if (!holder) return;
    const order = { DEVELOPMENT: 'dev', VALIDATION: 'val', OUT_OF_TIME_OOT: 'oot' };
    holder.innerHTML = [...rows].sort((a, b) => ({ DEVELOPMENT: 0, VALIDATION: 1, OUT_OF_TIME_OOT: 2 }[a.split_name] ?? 9) - ({ DEVELOPMENT: 0, VALIDATION: 1, OUT_OF_TIME_OOT: 2 }[b.split_name] ?? 9)).map(row => `<div class="stability-row ${order[row.split_name] || ''}"><b>${safe(row.split_name.replace('_', ' '))}</b><span>${rate(row.fraud_rate)}</span><small>${number(row.transactions)} transactions · ${number(row.fraud_transactions)} fraud-labeled · ${share(row.fraud_amount_share)} signed amount share</small></div>`).join('');
  }

  function renderFindings(rows) {
    const holder = document.getElementById('finding-grid');
    if (!holder) return;
    holder.innerHTML = (rows || []).map((row, index) => `<article class="finding-card"><span class="finding-number">${String(index + 1).padStart(2, '0')}</span><h3>${safe(row.title)}</h3><p><strong>Evidence:</strong> ${safe(row.evidence)}</p><p><strong>Meaning:</strong> ${safe(row.meaning)}</p><p class="next"><strong>Next:</strong> ${safe(row.next_action)}</p></article>`).join('');
  }

  fetch('assets/data/part3_summary.json').then(response => response.ok ? response.json() : Promise.reject(new Error('summary unavailable'))).then(data => {
    const dev = data.development || {};
    setText('statusLabel', data.status === 'PORTFOLIO_READY' ? 'PORTFOLIO READY' : 'PORTFOLIO PENDING');
    setText('transactions', number(dev.transactions)); setText('fraudTransactions', number(dev.fraud_transactions)); setText('fraudRate', rate(dev.fraud_rate)); setText('fraudAmountShare', share(dev.fraud_amount_share));
    setText('totalAmount', currency(dev.total_amount)); setText('fraudAmount', currency(dev.fraud_amount)); setText('avgFraudAmount', currency(dev.avg_fraud_amount)); setText('medianFraudAmount', currency(dev.median_fraud_amount));
    document.querySelectorAll('[data-status]').forEach(el => { el.dataset.status = data.status === 'PORTFOLIO_READY' ? 'pass' : 'review'; });
    renderTrend(data); renderChannels(data.channel || []); renderAmount(data.amount_bands || []); renderMcc(data.mcc || []); renderGeography(data.geography || []); renderConcentration(data.concentration || {}); renderPriority(data.priority_segments || []); renderStability(data.stability || []); renderFindings(data.findings || []);
  }).catch(() => { setText('statusLabel', 'PORTFOLIO PENDING'); });

  window.addEventListener('resize', () => chartRefs.forEach(chart => chart.resize()));
  if (window.gsap && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    gsap.from('.p3-hero .hero-copy > *, .hero-visual', { y: 22, opacity: 0, duration: .7, stagger: .08, ease: 'power3.out' });
    gsap.utils.toArray('.metric-card, .snapshot-stat, .chart-card, .finding-card, .concentration-card, .stability-row').forEach(item => gsap.from(item, { y: 16, opacity: 0, duration: .55, ease: 'power2.out', scrollTrigger: { trigger: item, start: 'top 89%', once: true } }));
  }
})();
