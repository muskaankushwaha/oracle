# Teammate 1 — full Node.js/GitHub code submission

## Code file

Use the full source module at [`node/github_client.js`](../node/github_client.js). It provides a read-only GitHub API client with validated names and refs, safe URL construction, request timeouts, bounded retries, safe error messages, verified-email selection, bounded repository pagination, and repository/tree/file read methods.

## Progress notes

The source contains 20 `Progress 01/20` through `Progress 20/20` comments describing its implementation sections. This is a complete standalone client module, but it has not yet replaced the corresponding helpers in `server.js`.

Before submitting, wire `createGitHubClient` into `server.js`, check the existing OAuth token/session boundary, add mocked-fetch tests, and verify that no write method is exposed. Keep OAuth credentials and response bodies out of logs and PRs.

## Suggested PR sequence

1. Add validation and the `GitHubApiError` type.
2. Add the timeout and read-only request method with bounded retry handling.
3. Add profile, email, repository, tree, and file methods.
4. Replace duplicated GitHub request code in `server.js` after review.
5. Add tests and document required OAuth permissions.

Use a separate commit for each meaningful completed change; record the commit SHA and reviewer feedback.
