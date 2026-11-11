# Iman — full frontend code submission

## Code file

Use the full source module at [`public/report_export.js`](../public/report_export.js). It adds a safe report export API for JSON, CSV, and Markdown. The module projects an allowlisted set of report fields, bounds output, redacts common credential formats, escapes CSV cells, and excludes raw pasted logs.

## Progress notes

The source contains 20 `Progress 01/20` through `Progress 20/20` comments. Each comment marks a substantive implementation section that can be reviewed as a separate commit. The module is prepared but not yet loaded by `public/index.html` or called by `public/app.js`.

Before submitting, add a script tag for `/report_export.js`, add export controls, connect those controls to `state.result`, review the generated files for sensitive content, and test the browser download behavior. The current source file is the full code, not a short example snippet.

## Suggested PR sequence

1. Add the module and its pure formatting/redaction helpers.
2. Add JSON export and safe report projection.
3. Add CSV export and escaping.
4. Add Markdown export and formatting.
5. Connect the UI controls and document the final flow.

Keep one honest commit per completed code change. Add the commit SHA and reviewer feedback to your team progress record.
