# Release audit — 23 October 2026

This audit covers the offline manual valuation workspace and public portfolio.
It does not claim that all Philippine equities have verified financial data or
that the platform produces independently validated investment targets.

## Current evidence

- 82 automated tests passed from a newly extracted public archive.
- The archive started through `run.py`; health, UI and occupied-port checks passed.
- A fresh-package Edge walkthrough completed with zero page errors and zero
  external browser requests. Blank URC inputs were blocked; synthetic P/E, DCF,
  advanced methods, save/load and export reproduced their expected values.
- The extracted TEL example produced PHP 844.73, showed the reporting qualification,
  ran sensitivity, and left its company brain byte-for-byte unchanged.
- GitHub Actions passed for commit `1683817` on its four configured OS/Python jobs.
  Later revisions have their own run status; consult the badge rather than treating
  this statement as a permanent guarantee.
- The release contains 61 blank real-company brains and a synthetic DEMO; private
  reports and working research histories are excluded by the package verifier.

Commands, test scope and platform limits are in [VERIFICATION.md](VERIFICATION.md).
The walkthrough records local evidence under `runtime/user-walkthrough/`.

## Goal acceptance matrix

| Requirement | Evidence | Assessment |
| --- | --- | --- |
| Run locally without an assistant | Extracted `run.py`, health/UI and browser checks | Verified in the tested Windows environment |
| Select stocks and appropriate models | All-stock selector, policy recommendations and browser tests | Implemented; suitability still needs analyst judgment |
| Edit data and assumptions offline | TOML brains, policy editor, company editor and saved scenarios | Verified workflows |
| Explain formulas and reproduce results | Formula tests, replay scripts, snapshots and helper evidence | Arithmetic verified within test coverage |
| Update from downloaded reports | Selected-file import, previews, hashes, period checks and source-conflict evidence | Assisted extraction; some real PDF layouts require manual entry |
| Inspect a real case quickly | Opening-screen TEL case, sources, sensitivity and saved notes | Implemented and verified in extracted package |
| Demonstrate defensible investment research | TEL statement reconciliation and explicit qualifications | Partial: sourced investigation, but no calibrated target |
| Demonstrate reliability across company types | Method regression tests and profile recommendations | Partial: real worked examples across types still needed |
| GitHub presentation and reuse | README, screenshots, CI workflow and MIT license | Present; source rights and data exclusions documented |

## Remaining completion gates

- Resolve the earnings-series comparability used in a real valuation, or use a
  separate company with traceable comparable financials for the completed example.
- Demonstrate a report-to-cash-flow reconciliation with company-specific interest,
  leases, investment, financing and ownership treatment.
- Support forecast and discount-rate assumptions with dated reasoning, and compare
  the result against another appropriate valuation method.
- Add worked checks for the materially different bank and holding-company methods;
  synthetic arithmetic alone does not validate financial-statement interpretation.

TEL's original dividend arithmetic remains reproducible. Its annual EPS conflict
and withdrawn original audit opinions remain unresolved. Formula tests, review
checkboxes and documentation do not clear those qualifications.

The visual walkthrough identified a wording issue: method availability was based
on the company brain even when scenario inputs were complete. The dropdown now
states “missing from brain”; overridden values are labelled “Scenario input”.

No separate-machine installation or independent human usability study is claimed.
Live PSE availability and arbitrary PDF layouts are outside this offline audit.
