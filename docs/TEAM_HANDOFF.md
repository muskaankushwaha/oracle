# ORACLE four-person GitHub handoff

This index links to four separate work plans, each with 20 commit-sized tasks and an owned area. Replace “Teammate 1–3” with their names and GitHub handles before sharing.

## Work plans

| Owner | Area | Plan |
|---|---|---|
| Iman (you) | Frontend, dashboard UX, integration and release coordination | [docs/TEAM_IMAN.md](TEAM_IMAN.md) |
| Teammate 1 | Node.js server, GitHub OAuth, sessions and API security | [docs/TEAM_MEMBER_1.md](TEAM_MEMBER_1.md) |
| Teammate 2 | FastAPI, repository analysis and LangGraph workflow | [docs/TEAM_MEMBER_2.md](TEAM_MEMBER_2.md) |
| Teammate 3 | Soft computing, model data and evaluation | [docs/TEAM_MEMBER_3.md](TEAM_MEMBER_3.md) |

## Code submission bundles

For contributors who need starter code, use the matching bundle below. Each contains 20 small code snippets with a target file, suggested commit message, and progress comment. The snippets are prepared for contributors to apply and review; they are **not integrated into the ORACLE runtime**. Apply one change at a time, adapt it to the current code, add relevant tests, and record the resulting commit SHA.

| Owner | Code bundle |
|---|---|
| Iman | [docs/CODE_SUBMISSION_IMAN.md](CODE_SUBMISSION_IMAN.md) |
| Teammate 1 | [docs/CODE_SUBMISSION_MEMBER_1.md](CODE_SUBMISSION_MEMBER_1.md) |
| Teammate 2 | [docs/CODE_SUBMISSION_MEMBER_2.md](CODE_SUBMISSION_MEMBER_2.md) |
| Teammate 3 | [docs/CODE_SUBMISSION_MEMBER_3.md](CODE_SUBMISSION_MEMBER_3.md) |

Each work plan lists the existing files for that area, the proposed scope of 20 separate commits, and a safe branch/PR procedure. These are future work plans; the tasks are not already implemented just because they appear in the handoff.

## Important: publish the current local baseline first

At handoff time, `origin` points to `https://github.com/muskaankushwaha/oracle.git` and the current branch is `main`. Several major project files are still untracked or locally modified. They are not available to teammates on GitHub yet. The owner should first review and publish the current MVP as one baseline pull request. Do this before teammates start their 20-task tracks.

Start by inspecting the exact local changes:

```powershell
git status --short
git diff -- .gitignore README.md requirements.txt oracle/config.py
```

Then make a branch and stage only the intended project files. Review the staged list before committing:

```powershell
git switch -c feature/oracle-mvp-baseline
git add .gitignore AGENTS.md README.md requirements.txt package.json server.js public oracle_api oracle/softcomputing data scripts docs/ORACLE_CHANGELOG.md docs/ROLLBACK_CHECKPOINTS.md docs/TEAM_HANDOFF.md docs/DATA_VALIDATION.md tests/test_oracle_api.py tests/test_oracle_workflow.py tests/test_softcomputing.py
git diff --cached --stat
git diff --cached
```

If you add the four work-plan files to that baseline, include `docs/TEAM_IMAN.md` and `docs/TEAM_MEMBER_1.md` through `docs/TEAM_MEMBER_3.md` in `git add`. Do **not** stage `.env`, `.oracle-history/`, virtual environments, caches, or secrets. Review `oracle/config.py` separately; it has a local modification and is intentionally omitted from the example staging command. Include it only if you understand and intend that change. Do not push directly to `main`.

After reviewing and running the project's checks, commit, push the branch, and open a pull request:

```powershell
git commit -m "Add ORACLE web investigation MVP"
git push -u origin feature/oracle-mvp-baseline
```

Wait until the baseline is merged before asking the other three people to branch from `main`.

## Each contributor's GitHub steps

For each numbered task, use a fresh branch based on the latest merged `main`, commit only that task's files, and open a pull request. A person can complete their 20 tasks as 20 small PRs or group closely related tasks into fewer reviewed PRs; do not create empty or artificial commits just to reach a number.

```powershell
git switch main
git pull origin main
git switch -c feature/<short-task-name>
# edit the files listed for the task, then run the relevant checks
git add <only-files-for-this-task>
git diff --cached
git commit -m "<plain-English task message>"
git push -u origin feature/<short-task-name>
```

Open the pushed branch on GitHub and create a pull request into `main`. Ask another teammate to review it, address comments, and merge only after required checks pass. Then start the next task from updated `main`. If project rules require one PR per task, follow that rule. Commit authors should configure their own Git identity with the name and email tied to their GitHub account; never share credentials.

## Shared project boundaries

- GitHub repository analysis remains read-only. No code changes, test execution against a selected repository, or PR creation without explicit user approval.
- Keep OAuth secrets in each developer's local ignored `.env`; share `.env.example`, never `.env`.
- Avoid editing another contributor's owned files in parallel. Coordinate cross-area API/schema changes first and assign one person to integrate them.
- Add tests for behavior changes and run the relevant checks before opening a PR. Update `docs/ORACLE_CHANGELOG.md` for project changes.
- The local rollback snapshots in `.oracle-history/` must never be committed.
