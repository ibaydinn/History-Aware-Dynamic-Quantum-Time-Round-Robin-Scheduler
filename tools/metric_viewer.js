/* Offline overall-metrics comparison; calculation remains in the Python metrics module. */
'use strict';
const METRICS = [
  ['context_switch_count', 'Context switches', 'count'],
  ['average_turnaround_time', 'Average turnaround time', 'time units'],
  ['average_response_time', 'Average response time', 'time units'],
  ['average_waiting_time', 'Average waiting time', 'time units'],
  ['deadline_miss_count', 'Deadlines missed', 'count'],
  ['average_deadline_miss_time', 'Average deadline miss time', 'time units · missed cycles only'],
];
function improvement(base, value) {
  if (base === null || value === null) return null;
  if (base === 0) return value === 0 ? 0 : null;
  const result = (base - value) / base * 100;
  return Number.isFinite(result) ? result : null;
}
function parseReport(report, filename) {
  if (!report || typeof report !== 'object' || !report.overall || typeof report.overall !== 'object') {
    throw Error('Expected a metrics report with an overall object. Use calculate_metrics on simulation results first.');
  }
  const averagedScene = report.scope === 'scene' && report.aggregation === 'equal_weight_tests';
  const overall = {};
  for (const key of ['cycle_count', ...METRICS.map(m => m[0])]) {
    const value = report.overall[key];
    if (value !== null && (typeof value !== 'number' || !Number.isFinite(value) || value < 0)) throw Error(`Invalid or missing ${key}.`);
    if (key.endsWith('_count') && (value === null || (!averagedScene && !Number.isSafeInteger(value)))) throw Error(`${key} must be a non-negative integer.`);
    overall[key] = value;
  }
  if (overall.deadline_miss_count > overall.cycle_count) throw Error('Deadline miss count exceeds cycle count.');
  const scheduler = report.scheduler;
  const name = typeof scheduler?.name === 'string' && scheduler.name.trim() ? scheduler.name : filename.replace(/\.json$/i, '');
  return {
    overall, label: name, filename,
    scope: report.scope === 'scene' ? 'scene' : 'test',
    aggregation: averagedScene ? 'equal_weight_tests' : 'pooled',
    testCount: report.scope === 'scene' ? report.test_count : null,
    hash: typeof report.scene_input_hash === 'string' ? report.scene_input_hash : typeof report.task_input_hash === 'string' && report.task_input_hash ? report.task_input_hash : null
  };
}
// Expose the pure comparison rules to Node's built-in test runner.
if (typeof module !== 'undefined' && module.exports) module.exports = { improvement, parseReport };
if (typeof document !== 'undefined') (() => {
  const $ = id => document.getElementById(id);
  const ns = 'http://www.w3.org/2000/svg';
  let runs = [], nextId = 0, mode = 'direct', baselineId = null, loading = false;
  let charts = [], exporting = false;
  const selected = new Set(METRICS.map(m => m[0]));
  const palette = ['#4386cd', '#dd9551', '#65a97b', '#a17cc8', '#cd7889', '#64a5aa'];
  const color = i => palette[i] || `hsl(${(i * 137.508) % 360} 60% 58%)`;
  const format = value => value === null ? 'N/A' : new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value);
  const percent = value => value === null ? 'N/A' : `${value > 0 ? '+' : ''}${format(value)}%`;
  function element(tag, text, parent, attrs = {}) {
    const n = document.createElement(tag); if (text !== null) n.textContent = text;
    for (const [key, value] of Object.entries(attrs)) n.setAttribute(key, value);
    if (parent) parent.appendChild(n); return n;
  }
  function svgNode(tag, attrs, parent, text) {
    const n = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs)) n.setAttribute(key, value);
    if (text !== undefined) n.textContent = text;
    parent.appendChild(n); return n;
  }
  function render() {
    const base = runs.find(r => r.id === baselineId) || runs[0];
    baselineId = base?.id ?? null;
    const relative = mode === 'relative';
    $('direct').setAttribute('aria-pressed', String(!relative));
    $('relative').setAttribute('aria-pressed', String(relative));
    $('baseline-label').hidden = !relative;
    $('baseline').replaceChildren();
    for (const run of runs) element('option', run.label + ` — ${run.filename}`, $('baseline'), { value: run.id });
    if (base) $('baseline').value = String(base.id);
    $('baseline').disabled = !runs.length;
    $('clear').disabled = !runs.length || loading;
    $('empty').hidden = runs.length > 0;
    $('explanation').textContent = relative
      ? 'Improvement = (baseline − result) / baseline × 100. Positive is better; negative is worse. Zero → zero is 0%; a nonzero result against zero is N/A.'
      : (runs.some(r=>r.aggregation==='equal_weight_tests') ? 'Scene values are averages per test, with equal weight for each test (including counts). Lower values are better.' : 'Each chart shows one overall metric. Lower values are better. Cycle counts are shown with each run.');
    const hashes = new Set(runs.map(r => r.hash).filter(Boolean));
    const notes = [];
    if (hashes.size > 1) notes.push('Input hashes differ: these runs use different task inputs.');
    if (runs.length > 1 && runs.some(r => !r.hash)) notes.push('Some reports have no input hash; identical inputs cannot be verified.');
    if (new Set(runs.map(r => r.overall.cycle_count)).size > 1) notes.push('Completed cycle counts differ.');
    if (new Set(runs.map(r=>r.scope)).size > 1) notes.push('Scene summaries and individual tests cannot be compared as equivalent runs.');
    const mixedAggregation = new Set(runs.map(r=>r.aggregation)).size > 1;
    if(mixedAggregation)notes.push('Aggregation methods differ. Regenerate scene reports to compare equal-weight test averages.');
    const mismatch = mixedAggregation || new Set(runs.map(r=>r.scope)).size > 1 || hashes.size > 1 || new Set(runs.map(r => r.overall.cycle_count)).size > 1;
    if (relative && mismatch) notes.push('Improvement charts are unavailable until the loaded runs have matching inputs and cycle counts.');
    if (relative && runs.length === 1) notes.push('Load another scheduler report to compare with the baseline.');
    $('notice').textContent = notes.join(' ');
    $('runs').replaceChildren();
    for (const run of runs) {
      const item = element('div', null, $('runs'), { class: 'run' });
      const swatch = element('i', null, item, { class: 'swatch', 'aria-hidden': 'true' }); swatch.style.background = run.color;
      const description = element('span', `${run.label}${run.scope==='scene'?` · ${run.testCount} tests`: ''} · ${format(run.overall.cycle_count)} ${run.aggregation==='equal_weight_tests'?'cycles/test':'cycles'}`, item);
      description.title = `${run.filename}\n${run.hash || 'No input hash'}`;
      const remove = element('button', '×', item, { type: 'button', 'aria-label': `Remove ${run.label}` });
      remove.disabled = loading;
      remove.addEventListener('click', () => { runs = runs.filter(r => r.id !== run.id); render(); });
    }
    $('charts').replaceChildren(); $('values').replaceChildren(); $('values').hidden = true;
    charts = []; updateExportControls();
    if (!runs.length || (relative && mismatch)) return;
    const displayed = relative ? runs.filter(r => r.id !== baselineId) : runs;
    if (!displayed.length) return;
    const valueFor = (run, key) => relative ? improvement(base.overall[key], run.overall[key]) : run.overall[key];
    for (const [key, title, units] of METRICS) {
      const card = element('section', null, $('charts'), { class: 'card' });
      const actions = element('div', null, card, { class: 'card-actions' });
      const label = element('label', null, actions);
      const checkbox = element('input', null, label, { type: 'checkbox', 'aria-label': `Select ${title} for export` });
      checkbox.checked = selected.has(key);
      element('span', ' Include in export', label);
      checkbox.addEventListener('change', () => { if (checkbox.checked) selected.add(key); else selected.delete(key); updateExportControls(); });
      for (const type of ['svg', 'png']) {
        const button = element('button', type.toUpperCase(), actions, { type: 'button' });
        button.addEventListener('click', () => exportCharts(type, [key]));
      }
      element('h2', title, card);
      element('p', relative ? '% improvement against selected baseline' : units + (displayed[0]?.aggregation==='equal_weight_tests'?' · average per test':''), card, { class: 'hint' });
      const svg = document.createElementNS(ns, 'svg'); card.appendChild(svg);
      const height = 54 + displayed.length * 44, left = 30, right = 490, width = right - left;
      charts.push({ key, title, units, svg, height, checkbox });
      svg.setAttribute('viewBox', `0 0 650 ${height}`); svg.setAttribute('role', 'img'); svg.setAttribute('aria-label', title);
      const values = displayed.map(r => valueFor(r, key));
      const scale = Math.max(1, ...values.filter(v => v !== null).map(Math.abs));
      const zero = relative ? (left + right) / 2 : left;
      svgNode('line', { x1: zero, x2: zero, y1: 16, y2: height - 25, stroke: 'var(--border)' }, svg);
      svgNode('text', { x: zero, y: height - 5, 'text-anchor': 'middle' }, svg, '0');
      svgNode('text', { x: right, y: height - 5, 'text-anchor': 'end' }, svg, relative ? percent(scale) : format(scale));
      if (relative) svgNode('text', { x: left, y: height - 5, 'text-anchor': 'start' }, svg, percent(-scale));
      displayed.forEach((run, i) => {
        const y = 20 + i * 44, value = values[i];
        const swatch = svgNode('rect', { x: 8, y: y + 8, width: 9, height: 9, rx: 2, fill: run.color }, svg);
        svgNode('title', {}, swatch, run.label + ' — ' + run.filename);
        if (value !== null) {
          const length = Math.abs(value) / scale * width / (relative ? 2 : 1);
          const bar = svgNode('rect', { x: value < 0 ? zero - length : zero, y, width: length, height: 25, rx: 5, fill: run.color }, svg);
          svgNode('title', {}, bar, `${run.label}: ${relative ? percent(value) : format(value)}`);
        }
        const text = relative ? percent(value) : format(value);
        const labelValue = svgNode('text', { x: 505, y: y + 17 }, svg, text);
        if (relative && value === null) svgNode('title', {}, labelValue, `Baseline: ${format(base.overall[key])}; result: ${format(run.overall[key])}. Percentage unavailable.`);
      });
    }
    updateExportControls();
    $('values').hidden = false;
    element('caption', relative ? 'Overall improvement (%)' : 'Overall values', $('values'));
    const head = element('tr', null, element('thead', null, $('values')));
    element('th', 'Scheduler', head, { scope: 'col' });
    for (const [, title] of METRICS) element('th', title, head, { scope: 'col' });
    const body = element('tbody', null, $('values'));
    for (const run of displayed) {
      const row = element('tr', null, body); element('th', run.label + ' — ' + run.filename, row, { scope: 'row' });
      for (const [key] of METRICS) {
        const cell = element('td', relative ? percent(valueFor(run, key)) : format(valueFor(run, key)), row);
        cell.title = relative ? `Baseline: ${format(base.overall[key])}; result: ${format(run.overall[key])}` : String(run.overall[key]);
      }
    }
  }
  function updateExportControls() {
    const count = charts.filter(c => selected.has(c.key)).length;
    for (const type of ['svg', 'png']) $('export-' + type).disabled = exporting || loading || !count;
    $('export-status').textContent = exporting ? 'Exporting…' : `${count} charts selected`;
  }
  function buildExport(items) {
    const width = 710;
    const output = document.createElementNS(ns, 'svg');
    output.setAttribute('xmlns', ns);
    if ($('export-background').value === 'white') svgNode('rect', { x: 0, y: 0, width: '100%', height: '100%', fill: '#ffffff' }, output);
    let y = 30;
    function textLine(text, x = 24, size = 13) {
      svgNode('text', { x, y, fill: '#20242b', 'font-family': 'system-ui, sans-serif', 'font-size': size }, output, text);
      y += 20;
    }
    function wrapped(text, x = 24) {
      // Bound long names/configurations, including strings without spaces.
      const chars = 48;
      for (let i = 0; i < text.length; i += chars) textLine(text.slice(i, i + chars), x);
    }
    textLine(mode === 'relative' ? 'Overall improvement (%)' : 'Overall results', 24, 20);
    y += 8;
    if (mode === 'relative') {
      wrapped('Baseline: ' + runs.find(r => r.id === baselineId).label);
      wrapped('Positive = better; negative = worse. N/A = percentage unavailable.');
    }
    if ($('notice').textContent) wrapped($('notice').textContent);
    y += 8;
    for (const run of runs) {
      svgNode('rect', { x: 24, y: y - 10, width: 12, height: 12, rx: 3, fill: run.color }, output);
      wrapped(run.label + (mode === 'relative' && run.id === baselineId ? ' [baseline]' : ''), 46);
      y += 4;
    }
    for (const chart of items) {
      y += 20;
      textLine(chart.title, 24, 17);
      textLine(mode === 'relative' ? '% improvement against selected baseline' : chart.units + (runs[0]?.aggregation==='equal_weight_tests'?' · average per test':''));
      const copy = chart.svg.cloneNode(true);
      copy.setAttribute('x', 24); copy.setAttribute('y', y);
      copy.setAttribute('width', 650); copy.setAttribute('height', chart.height);
      for (const n of copy.querySelectorAll('*')) {
        if (n.tagName.toLowerCase() === 'text') {
          n.setAttribute('fill', '#20242b'); n.setAttribute('font-family', 'system-ui, sans-serif'); n.setAttribute('font-size', 12);
        }
        if (n.getAttribute('stroke') === 'var(--border)') n.setAttribute('stroke', '#aab2bc');
      }
      output.appendChild(copy); y += chart.height;
    }
    const height = y + 24;
    output.setAttribute('width', width); output.setAttribute('height', height);
    output.setAttribute('viewBox', `0 0 ${width} ${height}`);
    return {
      width, height, content: new XMLSerializer().serializeToString(output),
      name: `results-${mode}-${items.length === 1 ? items[0].key : 'selected'}`
    };
  }
  function download(blob, name) {
    const url = URL.createObjectURL(blob);
    const link = element('a', null, document.body, { href: url, download: name });
    link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function pngBlob(result) {
    const url = URL.createObjectURL(new Blob([result.content], { type: 'image/svg+xml;charset=utf-8' }));
    try {
      const image = new Image();
      await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = () => reject(Error('Could not render SVG for PNG export.')); image.src = url; });
      const scale = Math.min(2, 8192 / result.width, 8192 / result.height, Math.sqrt(16000000 / (result.width * result.height)));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.floor(result.width * scale)); canvas.height = Math.max(1, Math.floor(result.height * scale));
      const context = canvas.getContext('2d'); if (!context) throw Error('Canvas is unavailable.');
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      if (!blob) throw Error('PNG creation failed. Try fewer charts or SVG.');
      return blob;
    } finally { URL.revokeObjectURL(url); }
  }
  async function exportCharts(type, keys) {
    if (exporting || loading) return;
    const items = charts.filter(c => keys.includes(c.key)); if (!items.length) return;
    exporting = true; updateExportControls();
    try {
      // Capture the current mode, baseline, legend and charts before asynchronous PNG work.
      const results = ($('export-layout').value === 'separate' ? items.map(c => [c]) : [items]).map(buildExport);
      for (const result of results) {
        const blob = type === 'svg' ? new Blob([result.content], { type: 'image/svg+xml;charset=utf-8' }) : await pngBlob(result);
        download(blob, result.name + '.' + type);
      }
      $('error').textContent = '';
    } catch (error) { $('error').textContent = 'Export failed: ' + error.message; }
    finally { exporting = false; updateExportControls(); }
  }
  for (const type of ['svg', 'png']) $('export-' + type).addEventListener('click', () => exportCharts(type, [...selected]));
  for (const [id, enabled] of [['select-all', true], ['select-none', false]]) $(id).addEventListener('click', () => {
    for (const chart of charts) { chart.checkbox.checked = enabled; if (enabled) selected.add(chart.key); else selected.delete(chart.key); }
    updateExportControls();
  });
  $('load').addEventListener('click', () => $('files').click());
  $('files').addEventListener('change', async () => {
    const files = [...$('files').files]; if (!files.length || loading) return;
    loading = true; $('load').disabled = true; render();
    const errors = [];
    try {
      for (const file of files) {
        try {
          const run = parseReport(JSON.parse(await file.text()), file.name);
          const id = nextId++; runs.push({ ...run, id, color: color(id) });
        } catch (error) { errors.push(`${file.name}: ${error.message}`); }
      }
    } finally {
      loading = false; $('load').disabled = false; $('files').value = '';
      $('error').textContent = errors.join('\n'); render();
    }
  });
  $('clear').addEventListener('click', () => { runs = []; nextId = 0; baselineId = null; $('error').textContent = ''; render(); });
  for (const next of ['direct', 'relative']) $(next).addEventListener('click', () => { mode = next; render(); });
  $('baseline').addEventListener('change', () => { baselineId = Number($('baseline').value); render(); });
  render();
})();
