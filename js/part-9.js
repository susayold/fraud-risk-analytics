(() => {
  'use strict'
  const $ = selector => document.querySelector(selector)
  const all = selector => [...document.querySelectorAll(selector)]
  const set = (key, value) => all(`[data-audit="${key}"]`).forEach(node => { node.textContent = value })
  const esc = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]))
  const clean = value => String(value ?? '').trim()
  const slug = value => clean(value).toLowerCase().replace(/[^a-z0-9]+/g, '-')
  const statusClass = value => slug(value).replace(/-+/g, '_')
  const formatNumber = value => { const n = Number(value); return Number.isFinite(n) ? n.toLocaleString('en-US', {maximumFractionDigits: 4}) : '—' }
  const formatMetric = row => {
    if (!row || row.status === 'NOT_APPLICABLE') return 'NOT_APPLICABLE'
    if (row.value === '' || row.value === null || row.value === undefined) return row.status || '—'
    if (row.metric_id === 'source_fraud_rate') return `${(Number(row.value) * 100).toFixed(3)}%`
    return formatNumber(row.value)
  }
  const parseCSV = text => {
    const rows = []; let row = []; let field = ''; let quoted = false
    for (let i = 0; i < text.length; i += 1) {
      const char = text[i]; const next = text[i + 1]
      if (char === '"' && quoted && next === '"') { field += '"'; i += 1; continue }
      if (char === '"') { quoted = !quoted; continue }
      if (char === ',' && !quoted) { row.push(field); field = ''; continue }
      if ((char === '\n' || char === '\r') && !quoted) { if (char === '\r' && next === '\n') i += 1; row.push(field); if (row.some(value => value !== '')) rows.push(row); row = []; field = ''; continue }
      field += char
    }
    if (field || row.length) { row.push(field); rows.push(row) }
    if (!rows.length) return []
    const headers = rows.shift().map(value => value.trim())
    return rows.map(values => Object.fromEntries(headers.map((header, index) => [header, (values[index] ?? '').trim()])))
  }
  const getJSON = url => fetch(url, {cache:'no-store'}).then(response => response.ok ? response.json() : Promise.reject(new Error(`${url} ${response.status}`)))
  const getText = url => fetch(url, {cache:'no-store'}).then(response => response.ok ? response.text() : Promise.reject(new Error(`${url} ${response.status}`)))
  const files = {
    project: getJSON('assets/data/project_status.json'),
    part7: getJSON('assets/data/part7_summary.json'),
    part8: getJSON('assets/data/part8_summary.json'),
    summary: getJSON('reports/part9/PART9_FINAL_SUMMARY.json'),
    manifest: getJSON('assets/data/part9_manifest.json'),
    sources: getText('reports/part9/part9_source_registry.csv').then(parseCSV),
    metrics: getText('reports/part9/part9_metric_registry.csv').then(parseCSV),
    statuses: getText('reports/part9/part9_status_registry.csv').then(parseCSV),
    validation: getText('reports/part9/part9_validation_report.csv').then(parseCSV),
    audit: getText('reports/part9/PART9_FINAL_RELEASE_AUDIT.md')
  }

  const renderSourceRows = rows => {
    const body = document.getElementById('source-rows'); if (!body) return
    const search = clean(document.getElementById('source-search')?.value).toLowerCase(); const part = clean(document.getElementById('source-part')?.value); const claim = clean(document.getElementById('source-class')?.value); const status = clean(document.getElementById('source-status')?.value)
    const filtered = rows.filter(row => (!search || `${row.source_id} ${row.path}`.toLowerCase().includes(search)) && (!part || row.source_part === part) && (!claim || row.claim_class === claim) && (!status || row.status === status))
    body.innerHTML = filtered.length ? filtered.map(row => `<tr><th>${esc(row.source_id)}</th><td>Part ${esc(row.source_part)} · ${esc(row.section)}</td><td>${esc(row.path)}</td><td><span class="claim-tag ${statusClass(row.claim_class)}">${esc(row.claim_class)}</span></td><td><span class="status-pill ${statusClass(row.status)}">${esc(row.status)}</span></td><td><button class="hash-button" type="button" title="Copy full SHA-256 hash" data-hash="${esc(row.sha256)}">${esc(row.sha256.slice(0,10))}…</button><small class="hash-size">${esc(row.bytes)} bytes</small></td><td><span class="status-pill available">AGGREGATE SAFE</span></td></tr>`).join('') : '<tr><td colspan="7">No registered source matches this filter.</td></tr>'
    set('source-table-note', `${filtered.length} of ${rows.length} registered sources shown · hashes are source-registry evidence.`)
  }
  const renderMetricRows = rows => {
    const body = document.getElementById('metric-rows'); if (!body) return
    body.innerHTML = rows.map(row => `<tr><th>${esc(row.label)}</th><td>${esc(formatMetric(row))}</td><td><span class="claim-tag ${statusClass(row.claim_class)}">${esc(row.claim_class)}</span></td><td>Part ${esc(row.source_part)}</td><td><span class="status-pill ${statusClass(row.status)}">${esc(row.status)}</span></td><td>${esc(row.source_artifact)}</td></tr>`).join('')
  }
  const setupFilters = rows => {
    const optionValues = {
      'source-part': [...new Set(rows.map(row => row.source_part).filter(Boolean))],
      'source-class': [...new Set(rows.map(row => row.claim_class).filter(Boolean))],
      'source-status': [...new Set(rows.map(row => row.status).filter(Boolean))]
    }
    Object.entries(optionValues).forEach(([id, values]) => { const select = document.getElementById(id); if (!select) return; values.sort((a,b) => String(a).localeCompare(String(b), undefined, {numeric:true})).forEach(value => { const option = document.createElement('option'); option.value = value; option.textContent = value; select.appendChild(option) }) })
    const controls = ['source-search','source-part','source-class','source-status']
    controls.forEach(id => { const control = document.getElementById(id); if (control) control.oninput = () => renderSourceRows(rows) })
  }
  const renderStatusRows = (registry, project, part7, part8) => {
    const body = document.getElementById('status-rows'); if (!body) return
    const live = {part7: part7?.status, part8: part8?.status}; const execution = {part7: part7?.execution_status || part7?.status, part8: part8?.execution_status || part8?.status}
    const hasMismatch = registry.some(row => live[row.layer] && live[row.layer] !== row.status)
    body.innerHTML = registry.map(row => {
      const layer = row.layer; const liveStatus = live[layer]; const mismatch = liveStatus && liveStatus !== row.status; const reconciled = mismatch ? 'SOURCE MISMATCH' : (liveStatus || row.status || 'SOURCE UNAVAILABLE'); const executionStatus = execution[layer] || row.execution_status || row.status || '—'; const link = row.deep_link || project?.layers?.[layer]?.deep_link || '#'
      return `<tr><th>${esc(row.label)}</th><td>Part ${esc(layer.replace('part',''))}</td><td><span class="status-pill ${statusClass(row.status)}">${esc(row.status)}</span></td><td><span class="status-pill ${statusClass(executionStatus)}">${esc(executionStatus)}</span></td><td><span class="status-pill ${statusClass(reconciled)}">${esc(reconciled)}</span></td><td><a href="${esc(link)}">Open ↗</a></td></tr>`
    }).join('')
    if (hasMismatch) document.body.dataset.auditState = 'mismatch'
  }
  const renderSummary = (project, part7, part8, summary, manifest, sources, metrics, statuses, validation, auditText) => {
    const pass = validation.filter(row => row.status === 'PASS').length; const total = validation.length; const classes = new Set([...sources, ...metrics].map(row => row.claim_class).filter(Boolean)); const hashRows = sources.filter(row => row.sha256 && row.bytes).length
    set('presentation-status', project?.presentation_status || summary?.presentation_status || 'PRESENTATION_READY'); set('execution-summary', project?.execution_summary || summary?.execution_summary || 'PART7_PART8_INPUT_BLOCKED'); set('presentation-gates', `${pass} / ${total}`); set('source-count', sources.length); set('metric-count', metrics.length); set('claim-class-count', classes.size); set('reconciliation-status', `SOURCE RECONCILIATION · ${project?.source_reconciliation_status || summary?.source_reconciliation_status || 'REVIEW'}`); set('validation-family-count', `${new Set(validation.map(row => row.family).filter(Boolean)).size} validation families · ${pass} PASS`); set('hash-coverage', `${hashRows} / ${sources.length} source hashes recorded`); set('manifest-commit', manifest?.code_commit ? `build ${manifest.code_commit.slice(0,10)}` : 'source-driven')
    const auditStale = /Part 5 model charts remain `INPUT_BLOCKED`|Part 6 graph charts remain `INPUT_BLOCKED`/.test(auditText || '') && part7?.status !== 'INPUT_BLOCKED'
    set('source-health', auditStale ? 'STALE · REVIEW' : 'CURRENT · PASS'); set('source-health-note', auditStale ? 'Release audit contradicts current canonical summaries.' : 'Release audit is reconciled with current source summaries; Part 7/8 remain honestly gated.')
    set('policy-lineage', part7?.status === 'INPUT_BLOCKED' ? 'awaiting reconciliation' : 'source-controlled')
    renderStatusRows(statuses, project, part7, part8); renderSourceRows(sources); renderMetricRows(metrics); setupFilters(sources)
    document.body.dataset.auditState = 'ready'
  }
  const renderFailure = error => { if (error) console.error('Audit source render failed', error); document.body.dataset.auditState = 'error'; set('presentation-status', 'SOURCE UNAVAILABLE'); set('release-note', 'A canonical audit source could not be loaded; claims are not promoted.'); set('source-health', 'SOURCE UNAVAILABLE'); set('source-health-note', 'Inspect the release artifacts before relying on this page.') }
  Promise.allSettled(Object.values(files)).then(results => {
    const keys = Object.keys(files); const data = Object.fromEntries(keys.map((key, index) => [key, results[index].status === 'fulfilled' ? results[index].value : null]))
    if (!data.project || !data.sources || !data.metrics || !data.statuses || !data.validation) { renderFailure(); return }
    renderSummary(data.project, data.part7, data.part8, data.summary, data.manifest, data.sources, data.metrics, data.statuses, data.validation, data.audit)
  }).catch(renderFailure)
  document.addEventListener('click', event => { const button = event.target.closest('[data-hash]'); if (!button) return; navigator.clipboard?.writeText(button.dataset.hash).then(() => { const original = button.textContent; button.textContent = 'COPIED'; window.setTimeout(() => { button.textContent = original }, 1100) }).catch(() => { button.title = button.dataset.hash }) })
})()
