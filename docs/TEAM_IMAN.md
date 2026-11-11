# Iman — Frontend, dashboard and integration plan

**Ownership:** Browser interface, account/settings presentation, dashboard navigation and final cross-area integration. Work from the latest merged baseline; coordinate API changes with the relevant owner before touching server or analyzer code.

## Existing code in this area

- `public/index.html` — dashboard shell, repository controls, account Settings card, evidence and report sections.
- `public/app.js` — GitHub-session bootstrap, repository selection, investigation request, result rendering, search/filter, theme toggle, Settings and logout interaction.
- `public/styles.css` — dark/light themes, responsive layout, logo and dashboard styling.
- `docs/TEAM_HANDOFF.md` — shared merge and contributor instructions.

The current tree already has the main UI, settings logout, repository selection, findings, evidence, fix suggestions, log predictions, and test ordering. The following are proposed follow-up commits; don’t re-add features already merged by someone else.

## 20 commit-sized tasks

1. **Add browser-side UI behavior tests** — Set up a light test harness for navigation and DOM behavior; cover Settings and logout. Files: `package.json`, `tests/ui/`.
2. **Separate view navigation helpers** — Centralize showing dashboard, welcome and Settings views. Files: `public/app.js`.
3. **Add Settings loading state** — Prevent an empty profile card while account information is loading. Files: `public/index.html`, `public/app.js`, `public/styles.css`.
4. **Improve missing-email presentation** — Make the unavailable-email state readable in both themes. Files: `public/app.js`, `public/styles.css`, `tests/ui/`.
5. **Add logout confirmation feedback** — Provide clear signed-out and failure states while keeping the server session authoritative. Files: `public/app.js`, `public/index.html`, `tests/ui/`.
6. **Fix focus after navigation** — Move keyboard focus to the new page heading or first useful control. Files: `public/index.html`, `public/app.js`.
7. **Announce scan progress accessibly** — Add screen-reader announcements for start, completion and failure. Files: `public/index.html`, `public/app.js`.
8. **Show scan progress stages** — Reflect repository listing, source reading and report building without implying unsupported AI actions. Files: `public/index.html`, `public/app.js`, `public/styles.css`.
9. **Improve scan error recovery** — Keep the selected repository and inputs after a failed request and make retry clear. Files: `public/app.js`, `public/index.html`.
10. **Add a clear-search action** — Let users quickly reset search and severity filters. Files: `public/index.html`, `public/app.js`, `public/styles.css`.
11. **Persist harmless report filters** — Remember severity/search choices for the current browser only; do not persist source text or logs. Files: `public/app.js`, `tests/ui/`.
12. **Improve empty-results states** — Explain no findings, no tests and no supplied logs accurately. Files: `public/app.js`, `public/index.html`.
13. **Add report export as JSON** — Export only the displayed report data with a clear file name. Files: `public/app.js`, `public/index.html`, `tests/ui/`.
14. **Add a print-friendly report view** — Hide controls and make evidence readable on printed pages. Files: `public/styles.css`, `public/index.html`.
15. **Improve narrow-screen Settings layout** — Check profile card and logout placement on small screens. Files: `public/styles.css`.
16. **Respect reduced-motion preference** — Ensure dashboard transitions and theme animations honor the OS preference. Files: `public/styles.css`, `public/app.js`.
17. **Add clear focus and contrast states** — Review buttons, selects, filters and nav in both themes. Files: `public/styles.css`.
18. **Improve dashboard source coverage summary** — Present file limits and skipped-file counts plainly from API fields. Files: `public/app.js`, `public/index.html`.
19. **Add a reproducible UI review checklist** — Document desktop, mobile, themes, guest and signed-in flows. Files: `docs/UI_REVIEW.md`.
20. **Integrate the four work areas** — Review API response changes with the other owners, resolve UI mismatches, and document the final user workflow. Files: `public/`, `README.md`, `docs/ORACLE_CHANGELOG.md`.

## Commit and PR routine

Follow the shared instructions in [`docs/TEAM_HANDOFF.md`](TEAM_HANDOFF.md). Use one branch per task, stage only the listed UI files, explain visual changes in the PR, and include screenshots when layout changes. Don’t include `.env` or `.oracle-history/`.
