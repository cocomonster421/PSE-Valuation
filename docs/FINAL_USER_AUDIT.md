# Final audit — 22 October 2026

All six fixes in [FIX_CHECKLIST.md](FIX_CHECKLIST.md) are implemented and verified. The two defects from the original [first-user review](FIRST_TIME_USER_REVIEW.md) no longer reproduce in the tested flows.

| Check | Result |
| --- | --- |
| Fresh public package | Try demo is visible and opens DEMO. Public-template explanation is concise. |
| Empty real-company data | URC calculation remains blocked when required inputs are absent. |
| Empty reports folder | Explicit empty message, disabled scan button, absolute company-folder path and manual-entry guidance. Scan button says Scan selected report. |
| Comparison P/E guidance | Details explains dated peer/history comparisons, consistent earnings basis and recording sources; 12× is explicitly a practice example, not an industry average. |
| P/E arithmetic | EPS 5 × 12 = 60; substituting current P/E 10 returns current price 50. |
| DCF arithmetic | Cash flow 5,000,000, net claims 2,000,000, zero growth, 10% discount rate, 1,000,000 shares produce 48. |
| DCF save/reload/recalculate/resave | Value remains 48; both structured helper records survive with original source snapshots and saved-origin context. |
| DCF manual edit | Cash flow changed to 6,000,000 produces 58. Cash-flow derivation is removed; unchanged net-debt evidence remains. |
| Advanced save/reload | AFFO option is automatically restored and Advanced methods enabled. Fresh input confirmation is required. |
| Advanced edit/resave/export | Comparison ratio changed from 12 to 10 produces 50; saved and exported result matches. |
| Readable arithmetic | Large numbers use ordinary grouped notation, with input labels in DCF steps. Numeric precision in calculations is unchanged; display is rounded. |
| Browser errors / external requests | Zero in the final fresh-package walkthrough. |

Validation performed:

- 39 Python tests passed, both locally and inside the extracted public package.
- `scripts/first_user_review.py` passed against the rebuilt ZIP. It now asserts the repaired behavior, including helper evidence and export.
- `scripts/browser_check.py` passed: company and policy editing, DDM/DCF, rate helper, report import, sensitivity, save/export/load, bank/REIT recommendations and mobile-width checks.
- `scripts/verify_package.py` passed using the isolated environment: extracted tests, example replay, standalone server startup, health/UI, blank public templates, DEMO and port-conflict handling.
- JavaScript syntax check passed. Landing screenshot inspected visually.

Evidence: `runtime/user-walkthrough/results.json` and screenshots in that folder. Tests use temporary data; private company files and existing saved analyses were not altered. The release ZIP was rebuilt after the audit to include these documents; application code is the same as tested.

Limits: this was a deterministic browser walkthrough, not a study with independent novice participants. Live PSE refresh and installation on a computer without Python were not tested in this pass. Report extraction still requires review and does not support every PDF layout. No live industry averages were added. Saved helper evidence records what was entered and its reference sources; it is not certification that those entries match a financial report. A saved method must still exist in the current policies; unsupported methods now produce a readable error.

Verdict: the requested fix list passes the tested workflows. The app remains an offline valuation workspace with explicit user-reviewed assumptions and assisted report extraction.
