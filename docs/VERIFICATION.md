# Verification

The public repository contains 61 blank real-company templates and one synthetic
DEMO. Tests do not require private financial data.

## Continuous integration

[![Tests](https://github.com/cocomonster421/PSE-Valuation/actions/workflows/tests.yml/badge.svg)](https://github.com/cocomonster421/PSE-Valuation/actions/workflows/tests.yml)

GitHub Actions runs the suite on Linux and Windows with Python 3.11 and 3.14 on
pushes and pull requests. The badge links to the actual run status. Browser checks
remain a separate local Windows check; they are not included in this badge.

## Automated checks

| Check | Coverage |
| --- | --- |
| `python -m unittest discover -s tests -v` | All 14 valuation methods, invalid inputs, source conflicts, backups, report parsing, readiness checks and public-package rebuilding |
| `python scripts/replay_tel_case.py` | Sourced TEL dividend case, EPS roll-forward and 15-cell sensitivity grid |
| `python scripts/replay_bdo_case.py` | Common-book reconciliation, justified P/B, residual income/DDM consistency and ROE/return sensitivity |
| `python scripts/replay_example.py` | Independent replay of the synthetic dividend example and sensitivity cases |
| `python scripts/browser_check.py` | DDM/DCF, rate and cash-flow helpers, company/policy edits, imports, sensitivity, save/load/export and mobile width |
| `python scripts/first_user_review.py` | Fresh-package onboarding, missing-data safeguards, advanced-method reopening, DCF evidence preservation, and TEL/BDO examples without modifying their brains |
| `python scripts/verify_package.py` | Extracted tests, example, standalone launch, health/UI, company templates and occupied-port handling |
| `node --check frontend/app.js` | JavaScript syntax |

Run the package builder before checks that consume the release ZIP. Browser checks
require Playwright and installed Microsoft Edge on Windows. They use temporary data,
block external browser requests and record page errors. Their screenshots and JSON
results are generated under `runtime/`; they are not bundled source files.

## Calculation checks

Synthetic P/E: EPS 5 × comparison P/E 12 = PHP 60. Using current P/E 10 with EPS 5
returns the reference price of PHP 50.

Synthetic DCF: annual cash 5,000,000 at 10%, with zero forecast and terminal growth,
has enterprise value 50,000,000. Subtracting net claims 2,000,000 and dividing by
1,000,000 shares gives PHP 48. Changing annual cash to 6,000,000 gives PHP 58.

Saved-analysis checks cover fresh confirmation, advanced-method selection, edited
inputs, export, retention of helper records and removal of evidence for manually
overridden outputs. Formula tests cover the remaining methods and invalid parameters.

## Scope

Windows verification uses Python 3.14, Microsoft Edge and an isolated dependency
environment. Python 3.11 is the minimum version required by the implementation, but
not every supported Python version or operating system has been tested.

No independent human usability study or separate physical-machine installation is
claimed. Live PSE availability is outside the offline regression suite. Report
extraction is assisted and layout-dependent; see [report checks](REAL_REPORT_CHECK.md).

The app has no trading, scheduled market refresh or news scoring. Prices are saved
references. Source checks identify missing, mixed-period and stale inputs; they do
not certify financial accuracy. Model suitability and assumptions require review.

## Additional DCF checks

`tests/test_dcf_properties.py` compares nonzero-growth DCF against a closed-form
growing annuity, checks share/debt scaling, rejects invalid growth/rates/shares and
verifies warnings for nonpositive modeled equity. `tests/test_tel_case.py` replays
the published research case and checks sensitivity direction.

`tests/test_dividend_properties.py` checks DDM against 1,000 individually discounted
payments, equivalence to FCFE under full distribution and identical growth/risk,
and independence of model value from the reference market price. The TEL replay
verifies arithmetic only; its source-review qualification remains separate.

## Bank example walkthrough

The browser check opens **BDO bank example**, checks the FY2025 inputs and visible
historical-scenario qualification, calculates PHP 145.48, and saves the analysis.
It checks that source notes and ROE survive saving and that the BDO company file
is byte-for-byte unchanged. The package verifier also checks the bundled example
endpoint. These checks establish workflow and calculation reproducibility, not
the forecasting quality of the selected return, growth or ROE assumptions.
