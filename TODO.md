# Completion checklist

Items are checked only after implementation and verification. Local company data stays private.

- [x] 1. Correct financial guidance: FCFE, rate selection and growth consistency.
- [x] 2. Verify report imports on real downloaded reports; retain page/row/units evidence and identify unsupported layouts.
- [x] 3. Finish guided DCF preparation: cash flow, working capital, debt, cash and other claims.
- [x] 4. Show assumption type, basis, source and date without confusing facts and estimates.
- [x] 5. Show readiness, freshness and reporting-period checks before valuation.
- [x] 6. Preserve a reproducible calculation trail, including derived figures and intermediate calculations.
- [x] 7. Verify isolated installation, launch, offline use and error recovery on Windows.
- [x] 8. Finish GitHub materials: walkthrough, examples, formula sources, data exclusions and MIT license.

## Verification boundaries

A clean virtual environment and extracted archive can be checked on this laptop. A separate physical Windows machine and first-time human usability session cannot be claimed from those tests.

## Decisions

- Software license: MIT. Third-party reports are excluded.
- Do not redistribute downloaded reports in the public archive. Include blank company templates, a clearly synthetic demo, and compact sourced case-study inputs with their qualifications.

## Evidence

- Financial formulas and caveats: docs/FORMULAS.md; formula regression tests.
- Actual report layouts and limitations: docs/REAL_REPORT_CHECK.md.
- Readiness/source metadata: tests/test_review.py.
- Guided DCF and saved helper trail: scripts/browser_check.py, synthetic DEMO verifies PHP 60 P/E and PHP 48 DCF.

- Isolated Windows verification: clean Python 3.14 environment, pinned parser dependencies, extracted public archive, 101 tests, health/UI/company reads and occupied-port recovery passed on 24 October 2026.
- Public archive: MIT, blank real-company templates, synthetic DEMO, no private research histories or report PDFs.
- JavaScript syntax and offline Edge workflow passed; no browser page errors or external requests.

## Remaining research

- [x] Record AC's six listed holdings with dated ownership and market values; replay the PHP 587.5699 billion partial subtotal and document Mynt/Globe overlap.
- [ ] Complete AC's unlisted assets, remaining parent claims, matched common shares and supported holding discount before publishing a fair value.

The checked implementation tasks above do not establish completed investment
research. [The release audit](docs/FINAL_USER_AUDIT.md) records the remaining
operating-company cash-flow reconciliation, holding-company valuation and supported
forecast/required-return work. [The reliability checklist](docs/RELIABILITY_CHECKLIST.md)
tracks the source and review safeguards separately.
