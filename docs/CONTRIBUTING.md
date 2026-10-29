# How we work on ORACLE

## One-time setup (every member)

```bash
git config --global user.name  "Your Real Name"
git config --global user.email "the-email-on-your-github-account@example.com"
```

Use the same email as your GitHub account, or your commits will not count for you.

## Daily loop

```bash
git checkout main && git pull            # get the latest code
git checkout -b feature/fuzzy-risk       # one branch per task (one GitHub Issue)
# ... write code, run pytest ...
git add <the files you changed>
git commit -m "feat(fuzzy): add membership functions for risk level"
git push -u origin feature/fuzzy-risk    # then open a Pull Request on GitHub
```

## Rules

- Branch names: `feature/…`, `fix/…`, `docs/…`, `test/…`.
- Commit messages: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` + a short present-tense summary.
- Small PRs: one task, ideally under 300 changed lines. Write `Closes #12` in the PR description.
- Every PR needs 1 approval and a green CI tick before it is merged ("Squash and merge").
- Never commit `.env`, API keys, `venv/`, `__pycache__/` or `workspace/`.
  If a key is ever pushed, revoke it immediately; deleting the file does not remove it from history.
- Never force-push to `main`. Never commit code you have not run.
- Teach-back: be ready to explain every line of your PR to the team.

## Your first PR (Week 0)

1. `git checkout -b docs/add-<yourname>`
2. Add your row to the **Team** table in `README.md`:
   `| Paulmi Maji | @your-github-username | Code analysis + fuzzy | Fuzzy risk and confidence |`
3. `git commit -am "docs: add <Your Name> to team table"` → push → open a PR → ask Muskan to review.
