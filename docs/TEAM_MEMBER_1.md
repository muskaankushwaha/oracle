# Teammate 1 — Node.js server and GitHub integration plan

**Ownership:** OAuth, session lifecycle, GitHub API access, server-side validation and Node service operations. Replace this heading with the contributor’s name and GitHub handle.

## Existing code in this area

- `server.js` — local HTTP server, OAuth login/callback, signed HttpOnly session cookie, logout, GitHub profile/repository calls, request limits and API forwarding to FastAPI.
- `package.json` — Node commands and engine requirement.
- `.env.example` — names and shape of local configuration (never put real secrets here).
- `tests/` — current tests focus on Python; add a Node test harness for server behavior.

The existing server already supports GitHub sign-in, account email retrieval, repository listing and logout. Keep OAuth secrets server-side. The app currently analyzes public repositories; do not silently widen permissions or claim private-repository support.

## 20 commit-sized tasks

1. **Add Node test command** — Add a small built-in Node test setup and a first test for config parsing. Files: `package.json`, `tests/node/`.
2. **Extract environment configuration** — Move env parsing and validated settings into a focused module. Files: `server.js`, `oracle_api` excluded; add `node/config.js`.
3. **Test OAuth state verification** — Cover valid, missing and mismatched state without calling GitHub. Files: `server.js` or extracted auth module, `tests/node/`.
4. **Harden session cleanup** — Expire stale sessions predictably and provide safe cleanup behavior. Files: `server.js` or `node/session-store.js`, `tests/node/`.
5. **Extract session cookie helpers** — Test HttpOnly, SameSite, Secure-on-HTTPS and clearing behavior. Files: `server.js` or `node/session-store.js`, `tests/node/`.
6. **Add session rotation after OAuth** — Avoid reusing the short-lived pre-login session identifier for the authenticated session. Files: auth/session module, `tests/node/`.
7. **Make OAuth scopes configurable and documented** — Keep requested scopes minimal and explain the effect of each. Files: `server.js`, `.env.example`, `README.md`.
8. **Improve account email fallback** — Handle no primary verified email and GitHub errors consistently. Files: GitHub profile module, `tests/node/`.
9. **Extract GitHub API client** — Centralize version, user-agent, auth header and error handling. Files: `server.js`, `node/github-client.js`, `tests/node/`.
10. **Add GitHub request timeout** — Bound stalled upstream calls and return a safe user-facing error. Files: GitHub client, `tests/node/`.
11. **Handle GitHub rate limits** — Map rate-limit headers to a retry-later response without exposing tokens. Files: GitHub client, `tests/node/`.
12. **Validate repository route inputs** — Cover owner/repository validation and encoded route construction. Files: `server.js` or route module, `tests/node/`.
13. **Paginate repository listing safely** — Support more than one page with an explicit maximum and tests. Files: repository route, `tests/node/`.
14. **Improve logout behavior tests** — Verify the server deletes the session and sends an expired cookie. Files: auth/session module, `tests/node/`.
15. **Add request origin protection for state-changing routes** — Define and test same-origin behavior for local API routes. Files: `server.js` or middleware module, `tests/node/`.
16. **Add security response headers** — Set an appropriate baseline and document any inline-script/style constraints. Files: `server.js`, `tests/node/`.
17. **Harden static-file path checks** — Test traversal, encoded path and directory-index requests. Files: `server.js`, `tests/node/`.
18. **Add structured server diagnostics** — Log request IDs and error categories while excluding cookies, tokens and source code. Files: `server.js` or `node/logger.js`, `tests/node/`.
19. **Document local OAuth setup and callback URL** — Explain GitHub OAuth App setup, required local variables and re-consent after scope changes. Files: `README.md`, `.env.example`.
20. **Review Node/API contract with Teammate 2** — Document request/response fields and error cases, then update integration tests. Files: `server.js`, `oracle_api/` only by coordination, `docs/API_CONTRACT.md`, tests.

## Commit and PR routine

Follow [`docs/TEAM_HANDOFF.md`](TEAM_HANDOFF.md). Use a fresh branch for each task. Never commit `.env`, access tokens, cookies or captured private repository content. Add tests for each server behavior change and ask a different teammate to review auth/security changes.
