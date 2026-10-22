# Portfolio walkthrough

## What this project demonstrates

Fundamental is a local valuation workbench for Philippine equities. It connects
business classification to valuation method selection, separates sourced financial
data from assumptions, and preserves the inputs behind each result.

The application uses Python, HTML, CSS and JavaScript, with BeautifulSoup and pypdf
for report extraction. It needs no AI calls, trading functions or remote fonts. A loopback
server serves the interface and reads two editable stores: company TOML files and
a method-policy catalog. Saved analyses are a third, separate output store.

## A five-minute demonstration

1. Run the launcher. The browser opens on localhost.
2. In the public release, choose **DEMO — Example Consumer Company (synthetic)**.
3. Select **P/E**. EPS 5 × comparison P/E 12 gives PHP 60; current P/E is 50 / 5 = 10. Explain why current P/E is not the valuation benchmark.
4. Choose **DCF**. The synthetic company has annual business cash of PHP 5 million, a 10% required return, zero growth, PHP 2 million net debt and 1 million shares. Value = (5 million / 10% − 2 million) / 1 million = PHP 48.
5. Open the cash-flow helper. Verify the synthetic inputs and explicit zero adjustments; calculate working capital and business cash. The 25% tax input is illustrative.
6. Change the comparison P/E or required return, calculate again and compare sensitivity cases.
7. Save an analysis and inspect the JSON: inputs, model version, company/policy snapshots, source checks and helper derivations remain together.
8. Select URC. The public template is intentionally blank. Populate it using your own EDGE summary or reviewed annual report; the private laptop workspace can already contain saved data.
9. For report updates choose the specific file, annual period and scale, optionally restrict PDF pages, review source rows and apply. Missing/unsupported rows remain manual.

Use your own reviewed analysis and thesis when presenting actual investment views.
The included example demonstrates mechanics and traceability, not research conclusions.

## Design decisions worth discussing

- FCFF and FCFE are distinct: WACC and debt bridging apply to FCFF, while cost of
  equity applies to FCFE without another debt subtraction. Baseline cash flows are
  stored separately so the two cannot be silently substituted.
- Financial totals are actual PHP, per-share metrics are PHP/share, and rates are
  decimal fractions in files but percentages in forms.
- Incomplete information remains missing. Historical extracted candidates are
  visible as evidence but do not automatically become valuation inputs.
- Methods use explicit equations rather than a model-generated answer.
- A policy edit can change recommendations and defaults, but cannot redefine the
  formula's required units or remove a required input.
- Atomic file replacement, backups and revision checks protect manual work.
- The browser workflow is tested with external network requests blocked.

## Suggested CV description

> Built an offline Philippine equity valuation workbench in Python and JavaScript,
> supporting 14 fundamental valuation methods, editable sourced company data,
> sensitivity analysis, and reproducible saved scenarios; verified calculations
> and local API behavior with automated tests and browser workflows.

Adapt this to the work you can personally explain and defend. Do not claim the
application produces verified live data or profitable investment recommendations.
