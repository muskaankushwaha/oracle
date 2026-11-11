const http = require('node:http');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

loadEnvFile();

const PORT = Number(process.env.PORT || 3000);
const APP_URL = (process.env.APP_URL || process.env.RENDER_EXTERNAL_URL || `http://localhost:${PORT}`).replace(/\/$/, '');
const CLIENT_ID = process.env.GITHUB_CLIENT_ID || '';
const CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET || '';
const SESSION_SECRET = process.env.SESSION_SECRET || '';
const oracleToolsHostPort = process.env.ORACLE_TOOLS_HOSTPORT || '';
const ORACLE_TOOLS_URL = (process.env.ORACLE_TOOLS_URL || (oracleToolsHostPort ? `http://${oracleToolsHostPort}` : 'http://127.0.0.1:8001')).replace(/\/$/, '');
const COOKIE_NAME = 'oracle_session';
const SESSION_MAX_AGE_MS = 8 * 60 * 60 * 1000;
const sessions = new Map();
const publicDir = path.join(__dirname, 'public');

function loadEnvFile() {
  const envPath = path.join(__dirname, '.env');
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
    if (!match || Object.hasOwn(process.env, match[1])) continue;
    process.env[match[1]] = match[2].replace(/^(['"])(.*)\1$/, '$2');
  }
}

function sign(value) {
  return crypto.createHmac('sha256', SESSION_SECRET).update(value).digest('base64url');
}

function safeEqual(left, right) {
  const a = Buffer.from(left || '');
  const b = Buffer.from(right || '');
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

function getCookie(req, name) {
  const entry = (req.headers.cookie || '').split(';').map(part => part.trim()).find(part => part.startsWith(`${name}=`));
  return entry ? decodeURIComponent(entry.slice(name.length + 1)) : '';
}

function getSession(req) {
  const value = getCookie(req, COOKIE_NAME);
  const dot = value.lastIndexOf('.');
  if (dot < 1 || !SESSION_SECRET) return null;
  const id = value.slice(0, dot);
  if (!safeEqual(value.slice(dot + 1), sign(id))) return null;
  const session = sessions.get(id);
  if (!session) return null;
  if (Date.now() - session.createdAt > SESSION_MAX_AGE_MS) {
    sessions.delete(id);
    return null;
  }
  return session;
}

function cookieHeader(id, req, clear = false) {
  const secure = APP_URL.startsWith('https://') ? '; Secure' : '';
  const value = clear ? '' : `${id}.${sign(id)}`;
  return `${COOKIE_NAME}=${encodeURIComponent(value)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${clear ? 0 : 60 * 60 * 8}${secure}`;
}

function sendJson(res, status, data, headers = {}) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers });
  res.end(JSON.stringify(data));
}

function sendText(res, status, text) {
  res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' });
  res.end(text);
}

async function github(pathname, token, options = {}) {
  const response = await fetch(`https://api.github.com${pathname}`, {
    ...options,
    headers: {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'ORACLE-read-only-investigator',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    const error = new Error(`GitHub returned ${response.status}`);
    error.status = response.status;
    error.rateLimit = response.headers.get('x-ratelimit-remaining');
    throw error;
  }
  return response.json();
}

async function githubRepositoryAnalyzeTool(owner, repo, token, issueReport, logText) {
  const endpoint = `${ORACLE_TOOLS_URL}/tools/github/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/analyze`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ issue_report: issueReport, log_text: logText })
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const error = new Error(payload.detail || 'The repository analysis service could not read this repository.');
    error.status = response.status;
    error.rateLimit = response.headers.get('x-github-ratelimit-remaining');
    throw error;
  }
  return response.json();
}

function apiError(res, error) {
  if (error.status === 401 || error.status === 403) {
    return sendJson(res, error.status, { error: error.rateLimit === '0' ? 'GitHub API rate limit reached. Try again later.' : 'GitHub denied the request. Check the repository visibility and try again.' });
  }
  if (error.status === 404) return sendJson(res, 404, { error: 'Repository or file was not found.' });
  console.error('GitHub request failed:', error.message);
  return sendJson(res, 502, { error: 'GitHub could not complete the request. Try again shortly.' });
}

async function readBody(req) {
  let body = '';
  for await (const chunk of req) {
    body += chunk;
    if (body.length > 100_000) throw new Error('Request too large');
  }
  return body ? JSON.parse(body) : {};
}

async function handle(req, res) {
  const url = new URL(req.url, APP_URL);
  if (req.method === 'GET' && url.pathname === '/health') return sendJson(res, 200, { ok: true });

  if (req.method === 'GET' && url.pathname === '/auth/login') {
    if (!CLIENT_ID || !CLIENT_SECRET || !SESSION_SECRET) return sendText(res, 503, 'Set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, and SESSION_SECRET in .env first.');
    const id = crypto.randomBytes(32).toString('base64url');
    const state = crypto.randomBytes(32).toString('base64url');
    sessions.set(id, { state, createdAt: Date.now() });
    const redirect = new URL('https://github.com/login/oauth/authorize');
    redirect.searchParams.set('client_id', CLIENT_ID);
    redirect.searchParams.set('redirect_uri', `${APP_URL}/auth/callback`);
    redirect.searchParams.set('scope', 'read:user user:email');
    redirect.searchParams.set('state', state);
    return res.writeHead(302, { Location: redirect.toString(), 'Set-Cookie': cookieHeader(id, req), 'Cache-Control': 'no-store' }).end();
  }

  if (req.method === 'GET' && url.pathname === '/auth/callback') {
    const session = getSession(req);
    const id = getCookie(req, COOKIE_NAME).split('.')[0];
    const state = url.searchParams.get('state') || '';
    const code = url.searchParams.get('code') || '';
    if (!session || !session.state || !safeEqual(state, session.state) || !code) {
      if (id) sessions.delete(id);
      return sendText(res, 400, 'GitHub sign-in could not be verified. Please try connecting again.');
    }
    try {
      const exchange = await fetch('https://github.com/login/oauth/access_token', {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: CLIENT_ID, client_secret: CLIENT_SECRET, code })
      });
      const credentials = await exchange.json();
      if (!exchange.ok || credentials.error || !credentials.access_token) throw new Error('OAuth exchange failed');
      const user = await github('/user', credentials.access_token);
      let email = user.email || '';
      try {
        const emails = await github('/user/emails', credentials.access_token);
        email = emails.find(item => item.primary && item.verified)?.email || email;
      } catch { /* Keep the account usable if GitHub does not return an email. */ }
      sessions.set(id, { token: credentials.access_token, login: user.login, name: user.name || user.login, email, avatar: user.avatar_url, createdAt: Date.now() });
      return res.writeHead(302, { Location: '/', 'Set-Cookie': cookieHeader(id, req), 'Cache-Control': 'no-store' }).end();
    } catch {
      sessions.delete(id);
      return sendText(res, 502, 'GitHub sign-in failed. Check the OAuth app settings and try again.');
    }
  }

  if (req.method === 'POST' && url.pathname === '/auth/logout') {
    const raw = getCookie(req, COOKIE_NAME);
    const id = raw.split('.')[0];
    if (id) sessions.delete(id);
    return sendJson(res, 200, { ok: true }, { 'Set-Cookie': cookieHeader('', req, true) });
  }

  if (url.pathname.startsWith('/api/')) {
    const session = getSession(req);
    if (!session?.token) return sendJson(res, 401, { error: 'Connect GitHub to continue.' });
    if (req.method === 'GET' && url.pathname === '/api/me') {
      return sendJson(res, 200, { login: session.login, name: session.name || session.login, email: session.email || '', avatar: session.avatar });
    }
    if (req.method === 'GET' && url.pathname === '/api/repos') {
      try {
        const repos = await github(`/users/${encodeURIComponent(session.login)}/repos?type=all&sort=updated&per_page=100`, session.token);
        return sendJson(res, 200, repos.filter(repo => !repo.private).map(repo => ({
          name: repo.name, fullName: repo.full_name, description: repo.description,
          branch: repo.default_branch, language: repo.language, updatedAt: repo.updated_at, url: repo.html_url
        })));
      } catch (error) { return apiError(res, error); }
    }
    if (req.method === 'POST' && url.pathname === '/api/analyze') {
      let body;
      try { body = await readBody(req); } catch { return sendJson(res, 400, { error: 'Invalid request.' }); }
      const owner = String(body.owner || '');
      const repo = String(body.repo || '');
      const issueReport = typeof body.issue_report === 'string' ? body.issue_report.trim() : '';
      const logText = typeof body.log_text === 'string' ? body.log_text : '';
      if (!/^[A-Za-z0-9_.-]{1,100}$/.test(owner) || !/^[A-Za-z0-9_.-]{1,100}$/.test(repo)) return sendJson(res, 400, { error: 'Select a valid repository.' });
      if (issueReport.length > 1000) return sendJson(res, 400, { error: 'Keep the issue description under 1,000 characters.' });
      if (logText.length > 20000) return sendJson(res, 400, { error: 'Keep pasted logs under 20,000 characters.' });
      try {
        const result = await githubRepositoryAnalyzeTool(owner, repo, session.token, issueReport, logText);
        return sendJson(res, 200, result);
      } catch (error) {
        if (error.status === 400) return sendJson(res, 400, { error: error.message });
        return apiError(res, error);
      }
    }
    return sendJson(res, 404, { error: 'API route not found.' });
  }

  if (req.method === 'GET') {
    const requested = url.pathname === '/' ? 'index.html' : decodeURIComponent(url.pathname.slice(1));
    const filePath = path.resolve(publicDir, requested);
    if (!filePath.startsWith(`${publicDir}${path.sep}`)) return sendText(res, 403, 'Forbidden');
    try {
      const contents = await fs.promises.readFile(filePath);
      const contentType = filePath.endsWith('.css') ? 'text/css; charset=utf-8' : filePath.endsWith('.js') ? 'text/javascript; charset=utf-8' : 'text/html; charset=utf-8';
      res.writeHead(200, { 'Content-Type': contentType, 'Cache-Control': 'no-cache' });
      return res.end(contents);
    } catch { return sendText(res, 404, 'Not found'); }
  }
  return sendJson(res, 405, { error: 'Method not allowed.' });
}

const server = http.createServer((req, res) => {
  handle(req, res).catch(error => {
    console.error('Request failed:', error.message);
    if (!res.headersSent) sendJson(res, 500, { error: 'Something went wrong. Try again.' });
    else res.end();
  });
});

if (require.main === module) {
  if (!SESSION_SECRET) console.warn('SESSION_SECRET is not configured. GitHub sign-in will stay disabled until .env is set.');
  server.listen(PORT, () => console.log(`ORACLE is running at ${APP_URL}`));
}

module.exports = { server };
