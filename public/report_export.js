/*
 * ORACLE report export module — Iman
 * Submission source for public/report_export.js. This is not loaded by the
 * dashboard yet; review the integration notes in docs/CODE_SUBMISSION_IMAN.md.
 * Progress markers divide the module into small, independently reviewable commits.
 */
(function attachOracleReportExport(root) {
  'use strict';

  const MAX_TEXT = 4000;
  const SECRET_PATTERNS = [
    /\bgh[pousr]_[A-Za-z0-9_]{20,}\b/g,
    /\bgithub_pat_[A-Za-z0-9_]{20,}\b/g,
    /\bBearer\s+[A-Za-z0-9._~+/-]+=*/gi,
    /\b(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*[^\s,;]+/gi
  ];
  const ALLOWED_SEVERITIES = new Set(['critical', 'high', 'medium', 'low']);

  // Progress 01/20 — Normalize unknown text and bound report fields.
  function text(value, limit = MAX_TEXT) {
    return String(value ?? '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').slice(0, limit);
  }

  // Progress 02/20 — Redact credential-shaped evidence before export.
  function redact(value) {
    let output = text(value);
    for (const pattern of SECRET_PATTERNS) output = output.replace(pattern, '[REDACTED]');
    return output;
  }

  // Progress 03/20 — Normalize severity values to the dashboard vocabulary.
  function severity(value) {
    const normalized = text(value, 20).toLowerCase();
    return ALLOWED_SEVERITIES.has(normalized) ? normalized : 'low';
  }

  // Progress 04/20 — Keep exported repository metadata minimal.
  function repositorySummary(repository = {}) {
    return {
      fullName: text(repository.fullName || repository.name, 200),
      branch: text(repository.branch, 200),
      url: safeHttpsUrl(repository.url),
      analyzedAt: text(repository.analyzedAt, 80)
    };
  }

  // Progress 05/20 — Accept only HTTPS GitHub links in report metadata.
  function safeHttpsUrl(value) {
    try {
      const url = new URL(String(value || ''));
      return url.protocol === 'https:' && url.hostname === 'github.com' ? url.href : '';
    } catch { return ''; }
  }

  // Progress 06/20 — Project findings onto an explicit export schema.
  function findingSummary(finding = {}) {
    return {
      id: text(finding.id, 100), title: redact(finding.title),
      severity: severity(finding.severity), file: text(finding.file, 500),
      line: Number.isInteger(finding.line) && finding.line > 0 ? finding.line : null,
      evidence: redact(finding.evidence), suggestion: redact(finding.suggestion),
      confidence: finiteScore(finding.confidence)
    };
  }

  // Progress 07/20 — Bound numeric score fields and reject NaN/Infinity.
  function finiteScore(value) {
    const number = Number(value);
    return Number.isFinite(number) ? Math.max(0, Math.min(100, number)) : null;
  }

  // Progress 08/20 — Omit raw supplied log lines from downloadable reports.
  function hypothesisSummary(item = {}) {
    return {
      title: redact(item.title), file: text(item.file, 500),
      line: Number.isInteger(item.line) && item.line > 0 ? item.line : null,
      severity: severity(item.severity), confidence: finiteScore(item.confidence),
      priorityScore: finiteScore(item.priorityScore), evidence: redact(item.evidence),
      suggestion: redact(item.suggestion), reason: redact(item.reason)
    };
  }

  // Progress 09/20 — Export only reviewed report fields, never tokens or UI state.
  function toSafeReport(report = {}) {
    const findings = Array.isArray(report.findings) ? report.findings : [];
    const hypotheses = Array.isArray(report.hypotheses) ? report.hypotheses : [];
    return {
      schemaVersion: '1.0', exportedAt: new Date().toISOString(),
      repository: repositorySummary(report.repository),
      scan: {
        filesScanned: Math.max(0, Number(report.scan?.filesScanned) || 0),
        filesFound: Math.max(0, Number(report.scan?.filesFound) || 0),
        failedFiles: Math.max(0, Number(report.scan?.failedFiles) || 0),
        truncated: Boolean(report.scan?.truncated)
      },
      findings: findings.filter(item => item && typeof item === 'object').slice(0, 500).map(findingSummary),
      hypotheses: hypotheses.filter(item => item && typeof item === 'object').slice(0, 100).map(hypothesisSummary),
      disclaimer: redact(report.disclaimer || 'Findings are heuristic candidates for human review.')
    };
  }

  // Progress 10/20 — Create safe cross-platform filenames.
  function filename(repository, extension) {
    const name = text(repository?.fullName || 'oracle-report', 120)
      .replace(/[^A-Za-z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'oracle-report';
    return `${name}-${new Date().toISOString().slice(0, 10)}.${extension}`;
  }

  // Progress 11/20 — Quote CSV cells using RFC-style double-quote escaping.
  function csvCell(value) { return `"${text(value).replace(/"/g, '""')}"`; }

  // Progress 12/20 — Render a spreadsheet-friendly findings table.
  function toCsv(report) {
    const safe = toSafeReport(report);
    const rows = [['Severity', 'Title', 'File', 'Line', 'Evidence', 'Suggested action']];
    for (const finding of safe.findings) rows.push([
      finding.severity, finding.title, finding.file, finding.line ?? '', finding.evidence, finding.suggestion
    ]);
    return rows.map(row => row.map(csvCell).join(',')).join('\r\n');
  }

  // Progress 13/20 — Escape Markdown table pipes and newlines.
  function markdownCell(value) { return text(value).replace(/\|/g, '\\|').replace(/[\r\n]+/g, ' '); }

  // Progress 14/20 — Render a human-readable report without raw log text.
  function toMarkdown(report) {
    const safe = toSafeReport(report);
    const lines = [
      `# ORACLE report: ${safe.repository.fullName || 'Repository'}`,
      '', `Branch: ${safe.repository.branch || 'Unknown'}`,
      `Analyzed: ${safe.repository.analyzedAt || safe.exportedAt}`,
      '', `Files scanned: ${safe.scan.filesScanned} · Findings: ${safe.findings.length}`,
      '', '## Findings', '', '| Severity | Finding | File | Line |', '|---|---|---|---:|'
    ];
    for (const item of safe.findings) lines.push(
      `| ${item.severity} | ${markdownCell(item.title)} | ${markdownCell(item.file)} | ${item.line ?? ''} |`
    );
    lines.push('', '## Evidence and suggested actions', '');
    for (const item of safe.findings) lines.push(
      `### ${item.title}`, '', `- Evidence: ${item.evidence || 'Not supplied'}`,
      `- Suggested action: ${item.suggestion || 'Review manually'}`, ''
    );
    lines.push(safe.disclaimer);
    return lines.join('\n');
  }

  // Progress 15/20 — Download text through a temporary object URL.
  function download(name, body, mime) {
    const blob = new Blob([body], { type: `${mime};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = name; anchor.hidden = true;
    document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // Progress 16/20 — Export JSON from the allowlisted report projection.
  function downloadJson(report) {
    const safe = toSafeReport(report);
    download(filename(safe.repository, 'json'), JSON.stringify(safe, null, 2), 'application/json');
  }

  // Progress 17/20 — Export CSV for spreadsheet review.
  function downloadCsv(report) {
    const safe = toSafeReport(report);
    download(filename(safe.repository, 'csv'), toCsv(safe), 'text/csv');
  }

  // Progress 18/20 — Export a Markdown summary for pull request discussion.
  function downloadMarkdown(report) {
    const safe = toSafeReport(report);
    download(filename(safe.repository, 'md'), toMarkdown(safe), 'text/markdown');
  }

  // Progress 19/20 — Reject missing reports with a useful caller-facing error.
  function assertReport(report) {
    if (!report || typeof report !== 'object') throw new TypeError('Run an investigation before exporting.');
    return report;
  }

  // Progress 20/20 — Expose a small stable browser API for UI integration.
  root.OracleReportExport = Object.freeze({
    toSafeReport, toCsv, toMarkdown,
    downloadJson: report => downloadJson(assertReport(report)),
    downloadCsv: report => downloadCsv(assertReport(report)),
    downloadMarkdown: report => downloadMarkdown(assertReport(report))
  });
})(window);
