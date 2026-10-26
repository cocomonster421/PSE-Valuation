# Release audit — 24 October 2026

This audit covers the offline manual valuation workspace and public portfolio.
It does not claim that all Philippine equities have verified financial data or
that the platform produces independently validated investment targets.

## Current evidence

- 102 automated tests passed from a newly extracted public archive.
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
- [GitHub Actions for commit `b0a40f1`](https://github.com/cocomonster421/PSE-Valuation/actions/runs/40056747481)
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

## Release decision and boundaries

The release scope is a manual offline valuation tool with one reproducible worked
example, not completed investment coverage across company types. BDO is the primary
modeling demonstration: its historical common equity is sourced, its forward
assumptions are illustrative, and its payout limitation remains explicit. TEL
illustrates unresolved source evidence; AC remains an incomplete worksheet.

The final release checks cover calculations, missing-input handling, local editing,
save/load/export, source qualifications, offline browser behavior and the public
archive. No blocking defect was found in these checks. Further company research is
tracked in the [non-blocking backlog](../TODO.md#research-backlog-non-blocking).

A full operating-company cash-flow case, AC's remaining unlisted values and claims,
and calibrated forecast/required-return assumptions would strengthen investment
research. They are not prerequisites for releasing this manual tool. Do not interpret
passing software checks as validation of a price target.

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

## P/E follow-up — 26 October 2026

Explicit historical, normalized and forecast earnings bases now accompany P/E
scenarios. The one-step annual EPS helper, matching multiple basis, period and
source explanation survive save/load/export. Backend checks reject mismatches and
stale helper arithmetic. Forecast/normalized EPS remains an assumption even when
numerically equal to historical EPS. Old inputs retain an unspecified-basis warning.

108 tests passed in the extracted package. Standalone startup and the offline Edge
walkthrough passed, including an illustrative 10 × (1 + 10%) × 12 = 132 forecast,
saved helper restoration, export and mismatched-basis rejection. No browser page
errors or external browser requests occurred. This verifies the workflow, not the
quality of an entered EPS forecast or comparison multiple.
