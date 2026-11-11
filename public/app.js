const $ = selector => document.querySelector(selector);
const state = { repos: [], result: null, search: '', severity: 'all', me: null };
function applyTheme(theme) {
  const selected = theme === 'light' ? 'light' : 'dark';
  const light = selected === 'light';
  document.documentElement.dataset.theme = selected;
  const toggle = $('#theme-toggle');
  if (toggle) {
    toggle.setAttribute('aria-pressed', String(light));
    toggle.setAttribute('aria-label', `Switch to ${light ? 'dark' : 'light'} mode`);
    toggle.title = `Switch to ${light ? 'dark' : 'light'} mode`;


  }
  const themeColor = $('meta[name="theme-color"]');
  if (themeColor) themeColor.content = light ? '#f4f7fb' : '#080e18';
}

function savedTheme() {
  try { return localStorage.getItem('oracle-theme') === 'light' ? 'light' : 'dark'; }
  catch { return 'dark'; }
}

applyTheme(savedTheme());

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

async function request(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options, headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Request failed. Please try again.');
  return data;
}

function notify(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.remove('hidden');
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => toast.classList.add('hidden'), 2800);
}

function severityCounts(findings) {
  return findings.reduce((counts, finding) => {
    counts[finding.severity] = (counts[finding.severity] || 0) + 1;
    return counts;
  }, { critical: 0, high: 0, medium: 0, low: 0 });
}

function renderTree(files) {
  const tree = $('#repo-tree');
  const selected = files || [];
  if (!selected.length) {
    tree.innerHTML = '<span class="tree-empty">No supported source files were readable.</span>';
    return;
  }
  const dirs = new Set();
  selected.forEach(file => {
    const parts = file.split('/');
    for (let i = 1; i < parts.length; i++) dirs.add(parts.slice(0, i).join('/'));
  });
  const entries = [...dirs].map(path => ({ path, folder: true })).concat(selected.map(path => ({ path, folder: false })));
  entries.sort((a, b) => a.path.localeCompare(b.path) || Number(b.folder) - Number(a.folder));
  tree.innerHTML = `<div class="tree-root">▾ <span class="folder-icon">▰</span> ${escapeHtml(state.result.repository.name)}</div>${entries.slice(0, 24).map(entry => {
    const depth = entry.path.split('/').length - 1;
    const name = entry.path.split('/').at(-1);
    return `<span class="tree-entry" style="padding-left:${12 + depth * 14}px" title="${escapeHtml(entry.path)}"><span class="${entry.folder ? 'folder-icon' : 'file-icon'}">${entry.folder ? '▰' : '▤'}</span> ${escapeHtml(name)}</span>`;
  }).join('')}${entries.length > 24 ? '<span class="tree-entry tree-empty">… more files in this scan</span>' : ''}`;
}

function renderEvidence() {
  const findings = state.result.findings.filter(item => {
    const matchesSeverity = state.severity === 'all' || item.severity === state.severity;
    const searchable = [item.title, item.file, item.evidence, item.category].join(' ').toLowerCase();
    return matchesSeverity && (!state.search || searchable.includes(state.search));
  });
  $('#finding-count').textContent = `${findings.length} of ${state.result.findings.length} finding${state.result.findings.length === 1 ? '' : 's'}`;
  if (!findings.length) {
    $('#findings-list').innerHTML = state.result.findings.length
      ? '<div class="panel-empty">No findings match this search.</div>'
      : '<div class="panel-empty">No signals matched the current checks in the files scanned. A clean heuristic scan is not a security guarantee.</div>';
    $('#code-snippet').innerHTML = '<span class="code-muted">No matching evidence to preview.</span>';
    $('#snippet-file').textContent = 'Source file preview';
    return;
  }
  $('#findings-list').innerHTML = findings.map(finding => `<article class="finding-row"><span class="finding-mark ${escapeHtml(finding.severity)}"></span><div class="finding-main"><div class="finding-title">${escapeHtml(finding.title)}</div><div class="finding-location">${escapeHtml(finding.file)}:${finding.line} · ${escapeHtml(finding.category)}</div></div><span class="finding-conf">${Math.round(finding.confidence * 100)}%</span><pre class="finding-evidence">${escapeHtml(finding.evidence)}</pre></article>`).join('');
  const lead = findings[0];
  $('#snippet-file').textContent = `${lead.file}:${lead.line}`;
  $('#code-snippet').innerHTML = `<span class="code-line-number">${lead.line}</span>${escapeHtml(lead.evidence)}`;
}

function renderFixes(findings) {
  const list = $('#fix-list');
  if (!findings.length) {
    list.innerHTML = '<div class="panel-empty">No fix suggestions are needed for the current scan signals.</div>';
    return;
  }
  list.innerHTML = findings.slice(0, 8).map(finding => `<article class="fix-item"><b>${escapeHtml(finding.title)} <span class="finding-location">· ${escapeHtml(finding.file)}:${finding.line}</span></b><p>${escapeHtml(finding.suggestion)}</p></article>`).join('');
}

function renderHypotheses(investigation) {
  const list = $('#hypotheses-list');
  const hypotheses = investigation?.hypotheses || [];
  $('#hypothesis-count').textContent = `${hypotheses.length} candidate${hypotheses.length === 1 ? '' : 's'}`;
  $('#hypothesis-summary').textContent = investigation?.summary || 'No investigation summary is available.';
  if (!hypotheses.length) {
    list.innerHTML = '<div class="panel-empty">No checked source pattern produced a candidate. A clean scan does not confirm the issue is absent.</div>';
    return;
  }
  list.innerHTML = hypotheses.slice(0, 8).map((hypothesis, index) => {
    const matches = hypothesis.matchedTerms?.length
      ? `Incident terms: ${hypothesis.matchedTerms.map(escapeHtml).join(', ')}`
      : 'No incident terms matched';
    const risk = hypothesis.riskAssessment;
    return `<article class="hypothesis-row"><div class="hypothesis-heading"><b>${index + 1}. ${escapeHtml(hypothesis.title)}</b><span class="hypothesis-priority">Bayes estimate ${Math.round((hypothesis.bayesian?.posterior ?? hypothesis.priorityScore) * 100)}%</span></div><div class="hypothesis-meta"><span>${escapeHtml(hypothesis.severity)} severity</span><span>Rule confidence ${Math.round(hypothesis.confidence * 100)}%</span><span>Fuzzy risk ${risk ? `${escapeHtml(risk.level)} · ${risk.score}/100` : 'unavailable'}</span><span>${matches}</span></div><p class="hypothesis-evidence"><b>Evidence</b> · ${escapeHtml(hypothesis.file)}:${hypothesis.line} — ${escapeHtml(hypothesis.evidence)}</p><p class="hypothesis-reason">${escapeHtml(hypothesis.reason)}</p><p class="hypothesis-reason">${escapeHtml(risk?.explanation || 'Fuzzy risk assessment is unavailable.')}</p><p class="hypothesis-suggestion">${escapeHtml(hypothesis.suggestion)}</p></article>`;
  }).join('');
}

function renderLogClassifications(logAnalysis) {
  const classifications = logAnalysis?.classifications || [];
  $('#log-count').textContent = `${classifications.length} line${classifications.length === 1 ? '' : 's'} classified`;
  $('#log-model-note').textContent = logAnalysis?.note || 'Log classifier results are unavailable.';
  if (!classifications.length) {
    $('#log-classifications').innerHTML = '<div class="panel-empty">No log lines were supplied.</div>';
    return;
  }
  $('#log-classifications').innerHTML = classifications.slice(0, 20).map(item =>
    `<article class="log-classification-row"><div class="log-classification-heading"><b>Line ${item.line} · ${escapeHtml(item.category.replaceAll('_', ' '))}</b><span>${Math.round(item.modelScore * 100)}% model score</span></div><pre>${escapeHtml(item.message)}</pre><p>${escapeHtml(item.explanation)}</p></article>`
  ).join('') + (classifications.length > 20 ? '<div class="panel-empty">Showing the first 20 classifications.</div>' : '');
}

function renderTestPlan(testPlan) {
  const tests = testPlan?.tests || [];
  if (!tests.length) {
    $('#test-plan-list').innerHTML = `<div class="panel-empty">${escapeHtml(testPlan?.objective || 'No test files were identified.')}</div>`;
    return;
  }
  $('#test-plan-list').innerHTML = tests.slice(0, 12).map(test =>
    `<article class="test-priority-row"><div><b>${test.rank}. ${escapeHtml(test.id)}</b><span>${escapeHtml(test.reason)}</span></div><small>${test.estimatedDurationSeconds}s · ${escapeHtml(test.durationSource)} · ${escapeHtml(test.coverageSource)}</small>${test.covers?.length ? `<code>Likely covers: ${test.covers.map(escapeHtml).join(', ')}</code>` : ''}</article>`
  ).join('') + `<p class="hypothesis-note">${escapeHtml([testPlan.note, testPlan.historyNote].filter(Boolean).join(' ') || 'Suggested order only; tests were not run.')}</p>`;
}

function showResults(result) {
  state.result = result;
  state.search = '';
  state.severity = 'all';
  $('#search-findings').value = '';
  $('#severity-filter').value = 'all';
  $('#report-content').classList.remove('hidden');
  $('#crumb-repo').textContent = result.repository.name;
  $('#page-title').textContent = `${result.repository.name} — Codebase Investigation`;
  $('#repo-subtitle-link').textContent = result.repository.name;
  $('#repo-subtitle-link').href = result.repository.url;
  $('#repo-link').href = result.repository.url;
  $('#branch-label').textContent = `${result.repository.branch} branch`;

  const counts = severityCounts(result.findings);
  const lead = result.findings[0];
  const fuzzyRisk = result.riskAssessment;
  const risk = fuzzyRisk ? `${fuzzyRisk.level[0].toUpperCase()}${fuzzyRisk.level.slice(1)}` : (counts.critical || counts.high ? 'High' : counts.medium ? 'Medium' : counts.low ? 'Low' : 'No signals');
  $('#headline-severity').textContent = result.findings.length ? `${risk} risk` : 'No signals found';
  $('#headline-severity').classList.toggle('clear', !result.findings.length);
  $('#lead-title').textContent = lead ? lead.title : 'No signals found';
  $('#lead-copy').textContent = lead ? `${lead.category} in ${lead.file}:${lead.line}. Review the evidence below.` : 'No checked patterns matched the sampled source files.';
  const confidence = lead ? Math.round(lead.confidence * 100) : 0;
  $('#confidence-value').textContent = lead ? `${confidence}%` : '—';
  $('#confidence-track-fill').style.width = `${confidence}%`;
  $('#risk-value').textContent = risk;
  $('#risk-value').classList.toggle('clear', !result.findings.length);
  $('#risk-copy').textContent = fuzzyRisk
    ? `Mamdani fuzzy score ${fuzzyRisk.score}/100 · ${result.findings.length} source signal${result.findings.length === 1 ? '' : 's'}.`
    : `${result.findings.length} heuristic signal${result.findings.length === 1 ? '' : 's'} detected.`;
  $('#status-value').textContent = 'Investigation Complete';
  $('#status-copy').textContent = 'Read-only source scan finished.';
  $('#scan-time').textContent = new Date(result.analyzedAt).toLocaleString();
  $('#summary-copy').textContent = `Reviewed ${result.scan.filesScanned} source files from the ${result.repository.branch} branch and found ${result.findings.length} heuristic signal${result.findings.length === 1 ? '' : 's'}. Findings include their source location, evidence, confidence, and a suggested next step.`;
  $('#metric-findings').textContent = result.findings.length;
  $('#metric-files').textContent = result.scan.filesScanned;
  $('#metric-large').textContent = result.scan.filesFound;
  $('#metric-branch').textContent = result.repository.branch;
  $('#activity-title').textContent = 'Source investigation completed';
  $('#activity-copy').textContent = `${result.scan.filesScanned} files reviewed · ${result.findings.length} findings`;
  $('#activity-time').textContent = new Date(result.analyzedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  renderTree(result.files);
  renderEvidence();
  renderFixes(result.findings);
  renderHypotheses(result.investigation);
  renderLogClassifications(result.logAnalysis);
  renderTestPlan(result.testPlan);

  const notes = [
    result.scan.truncated ? `The repository file list was truncated or the scan stopped at ${result.scan.fileLimit} source files.` : '',
    result.scan.failedFiles ? `${result.scan.failedFiles} file${result.scan.failedFiles === 1 ? '' : 's'} could not be read.` : '',
    result.scan.scannedBytes ? `${Math.round(result.scan.scannedBytes / 1024)} KB of source text reviewed.` : ''
  ].filter(Boolean);
  $('#disclaimer').innerHTML = `${escapeHtml(result.disclaimer)}${notes.length ? `<span class="coverage-note"> Coverage: ${notes.map(escapeHtml).join(' ')}</span>` : ''}`;
  $('#overview').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function boot() {
  try {
    const me = await request('/api/me');
    state.me = me;
    $('#welcome-panel').classList.add('hidden');
    $('#dashboard').classList.remove('hidden');
    $('#repository-control').classList.remove('hidden');
    $('#user-menu').innerHTML = `<span class="account-avatar" title="Signed in as ${escapeHtml(me.name || me.login)}"><img src="${escapeHtml(me.avatar)}" alt="Signed in as ${escapeHtml(me.name || me.login)}"></span>`;
    $('#settings-avatar').src = me.avatar;
    $('#settings-avatar').alt = `Profile icon for ${me.name || me.login}`;
    $('#settings-name').textContent = me.name || me.login;
    $('#settings-email').textContent = me.email || 'Email unavailable';
    state.repos = await request('/api/repos');
    const select = $('#repo-select');
    if (!state.repos.length) {
      select.innerHTML = '<option value="">No public repositories found</option>';
    } else {
      select.innerHTML = '<option value="">Select repository…</option>' + state.repos.map(repo => `<option value="${escapeHtml(repo.fullName)}">${escapeHtml(repo.fullName)}</option>`).join('');
      select.addEventListener('change', () => { $('#analyze').disabled = !select.value; });
    }
  } catch (error) {
    if (error.message !== 'Connect GitHub to continue.') notify(error.message);
  }
}

async function runInvestigation() {
  const pastedRepo = $('#repo-url').value.trim();
  let owner = '';
  let repo = '';
  if (pastedRepo) {
    try {
      const normalized = pastedRepo.includes('://') ? pastedRepo : `https://github.com/${pastedRepo}`;
      const url = new URL(normalized);
      const parts = url.pathname.split('/').filter(Boolean);
      if (url.hostname.toLowerCase() !== 'github.com' || parts.length !== 2) throw new Error();
      owner = parts[0];
      repo = parts[1].replace(/\.git$/i, '');
    } catch {
      $('#error-banner').textContent = 'Enter a GitHub URL like https://github.com/owner/repository or use owner/repository.';
      $('#error-banner').classList.remove('hidden');
      return;
    }
  } else {
    [owner, repo] = $('#repo-select').value.split('/');
  }
  if (!owner || !repo) return;
  $('#error-banner').classList.add('hidden');
  $('#report-content').classList.add('hidden');
  $('#loading').classList.remove('hidden');
  $('#analyze').disabled = true;
  const issueReport = $('#issue-report').value.trim();
  const logText = $('#log-text').value;
  try { showResults(await request('/api/analyze', { method: 'POST', body: JSON.stringify({ owner, repo, issue_report: issueReport, log_text: logText }) })); }
  catch (error) { $('#error-banner').textContent = error.message; $('#error-banner').classList.remove('hidden'); }
  finally { $('#loading').classList.add('hidden'); $('#analyze').disabled = !$('#repo-select').value && !$('#repo-url').value.trim(); }
}

$('#analyze').addEventListener('click', runInvestigation);
$('#repo-select').addEventListener('change', () => { if ($('#repo-select').value) $('#repo-url').value = ''; $('#analyze').disabled = !$('#repo-select').value && !$('#repo-url').value.trim(); });
$('#repo-url').addEventListener('input', () => { if ($('#repo-url').value.trim()) $('#repo-select').value = ''; $('#analyze').disabled = !$('#repo-select').value && !$('#repo-url').value.trim(); });
$('#search-findings').addEventListener('input', event => {
  state.search = event.target.value.trim().toLowerCase();
  if (state.result) renderEvidence();
});
$('#severity-filter').addEventListener('change', event => {
  state.severity = event.target.value;
  if (state.result) renderEvidence();
});
$('#search-findings').addEventListener('keydown', event => { if (event.key === 'Enter') $('#evidence-section').scrollIntoView({ behavior: 'smooth' }); });
document.addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#search-findings').focus(); } });

document.querySelectorAll('[data-target]').forEach(button => button.addEventListener('click', () => {
  const target = document.getElementById(button.dataset.target);
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.querySelectorAll('.report-tabs button').forEach(tab => tab.classList.toggle('active', tab.dataset.target === button.dataset.target));
}));

$('#share-button').addEventListener('click', async () => {
  const url = state.result?.repository.url || window.location.href;
  try { await navigator.clipboard.writeText(url); notify('Repository link copied.'); }
  catch { notify(url); }
});

$('#account-settings').addEventListener('click', async event => {
  const button = event.target.closest('#settings-logout');
  if (!button) return;
  button.disabled = true;
  button.textContent = 'Logging out…';
  try {
    await request('/auth/logout', { method: 'POST' });
    window.location.assign('/');
  } catch (error) {
    button.disabled = false;
    button.textContent = 'Log out';
    notify(`Could not log out: ${error.message}`);
  }
});

document.querySelectorAll('.side-link').forEach(button => button.addEventListener('click', () => {
  const action = button.dataset.action;
  const connected = Boolean($('#user-menu').querySelector('.account-avatar'));
  const settings = $('#account-settings');
  const openDashboard = () => {
    settings.classList.add('hidden');
    $('#repository-control').classList.toggle('hidden', !connected);
    $('#dashboard').classList.toggle('hidden', !connected);
    $('#welcome-panel').classList.toggle('hidden', connected);
  };
  if (action === 'new') {
    openDashboard();
    if (connected) $('#repo-select').focus();
  } else if (action === 'dashboard' || action === 'investigations') {
    openDashboard();
  } else if (action === 'settings') {
    if (connected) {
      $('#welcome-panel').classList.add('hidden');
      $('#dashboard').classList.add('hidden');
      $('#repository-control').classList.add('hidden');
      settings.classList.remove('hidden');
    } else {
      openDashboard();
      notify('Connect GitHub to view your account settings.');
    }
  } else if (action === 'repositories') { openDashboard(); if (connected) $('#repo-select').focus(); }
  else if (action === 'logs') { openDashboard(); if (connected) document.querySelector('.history-panel').scrollIntoView({ behavior: 'smooth' }); }
  else { openDashboard(); notify(`${button.textContent.trim()} is planned for a later ORACLE build.`); }
  document.querySelectorAll('.side-link').forEach(item => item.classList.toggle('active', item === button));
}));

document.querySelectorAll('.product-nav button').forEach(button => button.addEventListener('click', () => {
  if (button.dataset.flow !== 'Investigate') notify(`${button.dataset.flow} workflow is planned for a later ORACLE build.`);
  document.querySelectorAll('.product-nav button').forEach(item => item.classList.toggle('active', item === button));
}));

$('#theme-toggle').addEventListener('click', () => {
  const next = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  try { localStorage.setItem('oracle-theme', next); } catch { /* Theme still works for this page. */ }
  applyTheme(next);
});
boot();
