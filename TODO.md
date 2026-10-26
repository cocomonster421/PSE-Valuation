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

## Frozen release audit — 24 October 2026

- [x] Freeze features and distinguish software acceptance from company research.
- [x] Lead the README with the BDO worked example and its assumptions.
- [x] Run 102 tests from the public archive and check standalone startup.
- [x] Complete offline Edge regressions and a fresh-package walkthrough.
- [x] Verify save/load/export, input blocking and preserved source qualifications.
- [x] Record limitations and move additional company research to the backlog.

No blocking defect was found in this audit.

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

- Isolated Windows verification: clean Python 3.14 environment, pinned parser dependencies, extracted public archive, 102 tests, health/UI/company reads and occupied-port recovery passed on 24 October 2026.
- Public archive: MIT, blank real-company templates, synthetic DEMO, no private research histories or report PDFs.
- JavaScript syntax and offline Edge workflow passed; no browser page errors or external requests.

## Research backlog (non-blocking)

- [x] Record AC's six listed holdings with dated ownership and market values; replay the PHP 587.5699 billion partial subtotal and document Mynt/Globe overlap.
- [ ] Complete AC's unlisted assets, remaining parent claims, matched common shares and supported holding discount before publishing a fair value.

- [ ] Complete an operating-company report-to-cash-flow research case.
- [ ] Develop dated forecast and required-return research for investment targets.
- [ ] Resolve TEL reporting comparability before promoting provisional earnings ratios.

These are research extensions, not software release gates. Feature scope is frozen;
future changes should address reproducible defects or a separately selected enhancement.

The checked implementation tasks above do not establish completed investment
research. [The release audit](docs/FINAL_USER_AUDIT.md) records the remaining
operating-company cash-flow reconciliation, holding-company valuation and supported
forecast/required-return work. [The reliability checklist](docs/RELIABILITY_CHECKLIST.md)
tracks the source and review safeguards separately.

## P/E earnings-basis improvement — 26 October 2026

- [x] Separate historical, normalized and forecast annual EPS.
- [x] Add an editable one-step EPS forecast helper and period/source fields.
- [x] Validate matched multiple bases and helper arithmetic on the backend.
- [x] Preserve basis metadata in saved analyses and exported inputs.
- [x] Keep older analyses reproducible with an unspecified-basis warning.
- [x] Verify 108 tests, extracted standalone startup and offline forward-P/E save/load/export walkthrough.

## P/E audit fixes — 26 October 2026

- [x] Require explicit EPS and comparison-multiple bases for new API calculations, comparisons and saves.
- [x] Validate the growth helper's one-year horizon using consecutive FY labels or annual end dates.
- [x] Preserve stored legacy results without silently classifying their earnings.
- [x] Verify 110 regression tests and the extracted offline workflow, including both rejected audit cases.
