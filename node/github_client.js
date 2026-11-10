/**
 * GitHub read client — Teammate 1 contribution.
 * Submission source for extraction from server.js into node/github_client.js.
 * All methods are read-only. Never log the token or return it to a browser.
 */
'use strict';

const API_ROOT = 'https://api.github.com';
const API_VERSION = '2022-11-28';
const DEFAULT_TIMEOUT_MS = 12_000;
const MAX_RETRIES = 2;
const RETRYABLE_STATUS = new Set([429, 502, 503, 504]);
const NAME_PATTERN = /^[A-Za-z0-9_.-]{1,100}$/;

// Progress 01/20 — Represent upstream errors without carrying response secrets.
class GitHubApiError extends Error {
  constructor(status, message, retryAfter = null) {
    super(message); this.name = 'GitHubApiError'; this.status = status;
    this.retryAfter = retryAfter; this.retryable = RETRYABLE_STATUS.has(status);
  }
}

// Progress 02/20 — Validate path segments before URL construction.
function validateName(value, label = 'name') {
  if (typeof value !== 'string' || !NAME_PATTERN.test(value)) throw new TypeError(`Invalid GitHub ${label}.`);
  return value;
}

// Progress 03/20 — Validate branch names separately because GitHub refs may contain slashes.
function validateRef(value) {
  const forbidden = new Set(['~', '^', ':', '?', '*', '[', '\\']);
  if (typeof value !== 'string' || value.length < 1 || value.length > 200
      || value.startsWith('/') || value.endsWith('/') || value.includes('..') || value.includes('@{')
      || value.endsWith('.') || [...value].some(char => char.charCodeAt(0) <= 32 || forbidden.has(char))) {
    throw new TypeError('Invalid GitHub branch name.');
  }
  return value;
}

// Progress 04/20 — Reject non-GitHub or non-HTTPS API endpoints.
function apiUrl(path) {
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//')) throw new TypeError('GitHub path must be absolute.');
  const url = new URL(path, API_ROOT);
  if (url.origin !== API_ROOT || url.protocol !== 'https:') throw new TypeError('Invalid GitHub API origin.');
  return url;
}

// Progress 05/20 — Build the minimal authenticated headers.
function requestHeaders(token) {
  if (typeof token !== 'string' || token.length < 10) throw new TypeError('A GitHub access token is required.');
  return {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': API_VERSION,
    'User-Agent': 'ORACLE-read-only-investigator',
    Authorization: `Bearer ${token}`
  };
}

// Progress 06/20 — Parse Retry-After safely and cap wait time.
function retryDelay(response, attempt) {
  const header = Number(response.headers.get('retry-after'));
  return Number.isFinite(header) && header > 0 ? Math.min(header * 1000, 5000) : Math.min(250 * (2 ** attempt), 2000);
}

// Progress 07/20 — Delay helper used only between bounded safe retries.
function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

// Progress 08/20 — Convert error statuses to safe public messages.
function publicErrorMessage(status) {
  if (status === 401 || status === 403) return 'GitHub denied the request. Check account access.';
  if (status === 404) return 'GitHub resource was not found.';
  if (status === 429) return 'GitHub rate limit reached. Try again later.';
  return 'GitHub request failed. Try again shortly.';
}

// Progress 09/20 — Read JSON responses without exposing raw upstream bodies.
async function parseJson(response) {
  try { return await response.json(); }
  catch { throw new GitHubApiError(response.status, 'GitHub returned an invalid response.'); }
}

// Progress 10/20 — Retry only GET requests that GitHub marks transient.
async function request(path, token, options = {}) {
  const method = String(options.method || 'GET').toUpperCase();
  if (method !== 'GET') throw new TypeError('This ORACLE client only permits read-only GET requests.');
  const timeoutMs = Math.max(1000, Math.min(Number(options.timeoutMs) || DEFAULT_TIMEOUT_MS, 30_000));
  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (typeof fetchImpl !== 'function') throw new Error('Fetch is unavailable in this Node runtime.');
  const url = apiUrl(path);

  for (let attempt = 0; ; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    let response;
    try {
      response = await fetchImpl(url, { method: 'GET', headers: requestHeaders(token), signal: controller.signal });
    } catch (error) {
      if (attempt < MAX_RETRIES && error.name !== 'AbortError') { await wait(250 * (attempt + 1)); continue; }
      throw new GitHubApiError(502, 'Could not reach GitHub. Try again shortly.');
    } finally { clearTimeout(timer); }

    if (response.ok) return parseJson(response);
    if (RETRYABLE_STATUS.has(response.status) && attempt < MAX_RETRIES) {
      await wait(retryDelay(response, attempt)); continue;
    }
    throw new GitHubApiError(response.status, publicErrorMessage(response.status), response.headers.get('retry-after'));
  }
}

// Progress 11/20 — Fetch a signed-in user's public profile metadata.
function getProfile(token, options) { return request('/user', token, options); }

// Progress 12/20 — Fetch only profile email data allowed by the OAuth scope.
function getEmails(token, options) { return request('/user/emails', token, options); }

// Progress 13/20 — Select verified primary email only.
function primaryVerifiedEmail(emails) {
  if (!Array.isArray(emails)) return '';
  const entry = emails.find(item => item && item.primary === true && item.verified === true);
  return typeof entry?.email === 'string' ? entry.email : '';
}

// Progress 14/20 — Bound repository pagination.
function repositoryPath(login, page = 1) {
  validateName(login, 'login');
  const safePage = Math.max(1, Math.min(3, Math.trunc(Number(page) || 1)));
  const query = new URLSearchParams({ type: 'all', sort: 'updated', per_page: '100', page: String(safePage) });
  return `/users/${encodeURIComponent(login)}/repos?${query}`;
}

// Progress 15/20 — Return only public repositories to match product behavior.
async function listPublicRepositories(login, token, options) {
  const visible = [];
  for (let page = 1; page <= 3; page += 1) {
    const rows = await request(repositoryPath(login, page), token, options);
    if (!Array.isArray(rows)) throw new GitHubApiError(502, 'GitHub returned an invalid repository list.');
    visible.push(...rows.filter(row => row && row.private === false));
    if (rows.length < 100) break;
  }
  return visible.map(row => ({
    name: String(row.name || ''), fullName: String(row.full_name || ''),
    description: String(row.description || ''), branch: String(row.default_branch || ''),
    language: String(row.language || ''), updatedAt: String(row.updated_at || ''),
    url: String(row.html_url || '')
  }));
}

// Progress 16/20 — Construct repository metadata paths from validated segments.
function repositoryPathFor(owner, repo) {
  return `/repos/${encodeURIComponent(validateName(owner, 'owner'))}/${encodeURIComponent(validateName(repo, 'repository'))}`;
}

// Progress 17/20 — Fetch repository metadata without write methods.
function getRepository(owner, repo, token, options) {
  return request(repositoryPathFor(owner, repo), token, options);
}

// Progress 18/20 — Fetch a bounded default-branch Git tree.
function getTree(owner, repo, branch, token, options) {
  const base = repositoryPathFor(owner, repo);
  const ref = encodeURIComponent(validateRef(branch));
  return request(`${base}/git/trees/${ref}?recursive=1`, token, options);
}

// Progress 19/20 — Fetch one file's content metadata using a safe path.
function getFile(owner, repo, path, token, options) {
  if (typeof path !== 'string' || !path || path.length > 1000 || path.startsWith('/')
      || path.split('/').some(part => !part || part === '.' || part === '..')) throw new TypeError('Invalid repository file path.');
  const encodedPath = path.split('/').map(encodeURIComponent).join('/');
  return request(`${repositoryPathFor(owner, repo)}/contents/${encodedPath}`, token, options);
}

// Progress 20/20 — Expose a read-only client interface for server integration.
function createGitHubClient(token, options = {}) {
  return Object.freeze({
    profile: () => getProfile(token, options),
    emails: () => getEmails(token, options),
    publicRepositories: login => listPublicRepositories(login, token, options),
    repository: (owner, repo) => getRepository(owner, repo, token, options),
    tree: (owner, repo, branch) => getTree(owner, repo, branch, token, options),
    file: (owner, repo, path) => getFile(owner, repo, path, token, options)
  });
}

// Export only the integration surface and safe error type.
module.exports = { createGitHubClient, GitHubApiError, validateName, validateRef, primaryVerifiedEmail };
