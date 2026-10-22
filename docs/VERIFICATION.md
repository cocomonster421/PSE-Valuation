# Verification and scope

The offline manual valuation workbench is implemented and prepared for source upload.
No GitHub remote was created and nothing has been published to an external service.

## Requirement audit

| Requested behavior | Implementation and verification |
| --- | --- |
| Search/select a stock on one page | Local search across 61 records; browser selects TEL, BDO and AREIT |
| Light company information and price | Company, industry/profile and dated saved price; source link in price input |
| Business-based method recommendations | Editable stock-to-profile mapping and profile recommendations; browser verifies telecom, bank and REIT choices |
| Different fundamental methods | 14 independent methods; hand-calculated tests cover each implementation |
| Required fields and editable inputs | Catalog-driven forms; browser exercises DDM and FCFF with confirmation |
| Prefilled local inputs with provenance | Value/date/source/status plus policy defaults; unreviewed figures labeled |
| Shares, beta and assumption experiments | Editable shares and beta/WACC; browser verifies WACC and persistent share update |
| Reproducible fair value | Pure engine, breakdown, version and stored inputs; API replay test |
| Assumption comparisons | Lower/base/higher sensitivity results saved with analysis; formula and browser checks |
| Separate editable stock data | Per-company TOML plus structured and advanced editors; backup/conflict tests |
| Separate editable method policies | JSON catalog, default/recommendation controls and advanced editor; browser persists changed growth |
| Offline without Codex | Parsing tools installed once; browser blocks non-local requests during offline workflows and reports zero attempted external requests |
| Report updates | PDF/text/saved EDGE HTML proposals, source rows, reviewed apply, duplicate tracking and changed-file/older-period rejection |
| Optional online refresh | Explicit EDGE fetch for EPS/book value and dated price; read-only URC verification succeeded, including previous-close fallback |
| Save personal research | Snapshot-backed scenarios, export and reload; browser and API checks |
| Standalone GitHub project | Archive extracted separately; tests, example and run.py pass there |
| Employer presentation | Screenshots, walkthrough, assumptions documentation, reproducible example and upload guide |

## Verification performed

- `python -m unittest discover -s tests -v`: 39 tests pass, covering each valuation
  method, invalid assumptions, sensitivity, scenario replay, source conflicts,
  backups, malformed files, non-finite values and protected formula units.
- `node --check frontend/app.js`: passes.
- `python scripts/browser_check.py`: passes in installed Edge using temporary data.
  Covers DDM/DCF, beta/WACC, saved sensitivity, export/load, baseline edits surviving
  reload, policy edits, report scan/apply, all 61 dropdown entries, bank/REIT recommendations and a 390px viewport. No page errors
  or attempted external requests. Desktop and mobile screenshots are in docs/screenshots.
- All 61 company records pass editable-file validation. Nine missing industry labels
  are marked unclassified rather than filled with invented facts.
- `python scripts/replay_example.py` reproduces the documented PHP 102.00 illustrative
  value and the independently recalculated sensitivity cases.
- Archive checks use an explicit source allowlist and verify an extracted copy's
  tests, example and standalone run.py, including UI, health, 61 blank real-company templates and synthetic DEMO.

## Deliberate limitations

Prices are saved references, not live quotes. Imported financial data requires review
and may predate the latest disclosure; dates and candidate status remain visible.
Missing cash-flow and specialist inputs are not fabricated. Nine industry labels
need manual classification. Not every company has enough verified inputs for every
recommended method.

DCF has five constant-growth explicit years; DDM is constant-growth; NAV/SOTP and
insurance methods accept reviewed component totals. This manual workbench has no
trading, news scoring or scheduled market refresh. The offline report extractor
supports only recognized text rows and requires review; scanned PDFs need manual entry.
Missing company facts are not replaced with illustrative assumptions. Comparison
P/E defaults use a saved peer sample where available, not a live industry-wide average.

Private scenarios, downloaded financial snapshots, research histories and revision backups are excluded from the upload archive. The owner selected MIT for original code. Browser QA is an optional
Windows development script. Parsing uses BeautifulSoup and pypdf; valuation itself
uses standard-library Python.

## Audit fixes

Negative Unicode signs are preserved. Ambiguous note/year columns and opening-cash rows are skipped. Each report is selected individually before applying its period and units. Tests cover working-capital current/prior balances and mixed-report folders. Browser checks cover the working-capital bridge, blank-tax rejection, resetting assumptions between companies and NAV-specific labels. NAV/RNAV formulas now distinguish gross assets and corresponding claims from SOTP component equity values.

## Completion verification

- Guided cash-flow preparation includes other capital investment, other non-cash adjustments, other working-capital movements and other claims; missing adjustments require explicit review rather than becoming zero.
- Saved analyses include structured helper derivations and source-readiness results. scripts/replay_saved.py verifies a saved fair value offline.
- The public archive includes synthetic DEMO, a synthetic dividend example, formula references and MIT licensing; private financial brains are replaced with blank templates only inside the archive.
- Isolated dependency installation uses requirements-lock.txt in a clean Python 3.14 virtual environment on Windows. A separate physical laptop and a first-time human usability session were not tested.

Final isolated release verification passed on 2026-10-22: 39 tests, offline example replay, independent server startup, UI/health, all public templates and occupied-port recovery. Windows sockets now use exclusive binding to prevent two launchers serving the same port.
