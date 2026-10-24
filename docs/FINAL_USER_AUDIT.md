# Release audit — 24 October 2026

This audit covers the offline manual valuation workspace and public portfolio.
It does not claim that all Philippine equities have verified financial data or
that the platform produces independently validated investment targets.

## Current evidence

- 101 automated tests passed from a newly extracted public archive.
- The archive started through `run.py`; health, UI and occupied-port checks passed.
- A fresh-package Edge walkthrough completed with zero page errors and zero
  external browser requests. Blank URC inputs were blocked; synthetic P/E, DCF,
  advanced methods, save/load and export reproduced their expected values.
- The extracted TEL example produced PHP 844.73, showed the reporting qualification,
  ran sensitivity, and left its company brain byte-for-byte unchanged.
- The extracted BDO example produced PHP 145.48, exposed the payout-policy gap,
  saved its audited common-equity evidence in notes, and left its company brain
  byte-for-byte unchanged. Its modeled payout is not a declared dividend.
- Local browser regressions also verified cash-flow and SOTP component baseline
  saving, source evidence restoration, and financial/assumption review resets.
- [GitHub Actions for commit `5bf132e`](https://github.com/cocomonster421/PSE-Valuation/actions/runs/40056209229)
  completed successfully on all four Linux/Windows and Python 3.11/3.14 jobs.
  Browser checks are separate local checks and are not covered by that badge.
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
| Inspect real examples quickly | Opening-screen TEL and BDO cases, sources, sensitivity and saved notes | Both verified in extracted package |
| Demonstrate investment research | TEL statement reconciliation; BDO audited common equity and dividend-policy comparison | Source-based findings reproduced; forward assumptions remain illustrative |
| Demonstrate reliability across company types | Bank model replay, AC ownership/claims worksheet, cash-flow and SOTP helpers | Bank arithmetic and common equity reconciled; complete operating-company and holding-company valuations remain unfinished |
| GitHub presentation and reuse | README, screenshots, CI workflow and MIT license | Present; source rights and data exclusions documented |

## Remaining completion gates

- Resolve the earnings-series comparability used in a real valuation, or use a
  separate company with traceable comparable financials for the completed example.
- Demonstrate a report-to-cash-flow reconciliation with company-specific interest,
  leases, investment, financing and ownership treatment.
- Support forecast and discount-rate assumptions with dated reasoning, and compare
  the result against another appropriate valuation method.
- Complete the holding-company valuation using dated attributable component values,
  matched common shares and remaining parent claims. AC's source-scope check and
  the app's component helper are complete; the real component values are not.

## Research and workflow changes since the previous audit

- BDO common equity reconciles to its audited group statements after removing
  noncontrolling interests and preferred capital. Its justified P/B, residual-income
  and matching-payout DDM examples reproduce the same conditional value.
- The BDO cash-dividend policy does not by itself support the payout assumed by
  those equivalent models. The case now quantifies that gap instead of presenting
  agreement as independent investment corroboration.
- Cash-flow bridges and SOTP components can be explicitly saved in company brains,
  restored for editing and replayed by offline checks. Parent claims remain separate
  from component equity. Missing or contradictory evidence remains visible.
- Changed financial figures cannot inherit an earlier review through an app/API
  save. Changed assumptions with an unchanged explanation become illustrative.
  Direct external file edits bypass save-time rules; review labels remain user
  declarations, not certifications.

TEL's original dividend arithmetic remains reproducible. Its annual EPS conflict
and withdrawn original audit opinions remain unresolved. Formula tests, review
checkboxes and documentation do not clear those qualifications.

The visual walkthrough identified a wording issue: method availability was based
on the company brain even when scenario inputs were complete. The dropdown now
states “missing from brain”; overridden values are labelled “Scenario input”.

No separate-machine installation or independent human usability study is claimed.
Live PSE availability and arbitrary PDF layouts are outside this offline audit.
