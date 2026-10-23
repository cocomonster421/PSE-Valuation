# Valuation reliability checklist

## Implemented

- [x] Confirmation acknowledges inputs without removing unresolved warnings.
- [x] Show data review and assumption evidence separately, including beside results.
- [x] Default and changed assumptions remain illustrative until their matching saved
  values have an explicit documented status, basis and review date within 365 days.
- [x] Edit assumption explanations and dates without replacing them with generic text.
- [x] Store reporting review status and reconciliation notes in each company brain.
  Unresolved issues remain visible even when individual figures are marked reviewed.
- [x] Preserve evidence in company-file round trips and saved analysis snapshots.
- [x] Check missing/stale inputs, units and mixed periods; independently test key
  dividend and DCF calculations.
- [x] Applying financial imports invalidates an earlier reporting review and records
  affected fields and time. Existing unresolved issues and prior review notes persist.
  Previewing a report or importing only a price does not reset financial review.
- [x] Record annual, trailing-year, quarter, YTD or point-in-time periods explicitly.
  Flag nonannual or unknown flow inputs, including cash-flow helper sources. Generic
  imports no longer claim annual coverage from an end date alone.
- [x] Automatically run an editable one-input sensitivity test after calculation,
  describe the illustrative range and flag values crossing the reference price.
  Invalid stress inputs show an explicit unavailable result, without altering the
  base calculation. Saved comparisons reproduce their three tested cases.
- [x] Check all saved companies offline with per-method issues, repair messages for
  broken files, links to open inputs and a JSON export containing inputs, review
  evidence, calculation status, timestamps and source/policy revision identifiers.
  The scan uses recommended methods, or all methods if no recommendation exists.
- [x] Screen downloaded report text for possible restatement, audit-opinion,
  control-weakness and going-concern passages. Show excerpts and page references;
  save only selected passages as unresolved review items, preserving file hashes.
  Keyword matches are not accounting conclusions; negation and context need review.
- [x] Add a structured cash-statement bridge for FCFF and FCFE, explicit interest
  classification, signed adjustments, financing and ownership claims, with required
  period/source/lease explanations and a saved, replayable calculation trail.
- [x] Save cash-flow reconciliation inputs and explanations in the company brain
  through the helper. Offline reviews replay the baseline and flag missing or
  inconsistent evidence. Changes reset reporting review without clearing unresolved
  issues; matching arithmetic does not clear accounting-quality warnings.

- [x] Preserve imported trailing-EPS components and dates in the company brain;
  replay their arithmetic and period alignment in offline reviews. Flag missing
  component evidence and undated or expired comparability reviews.

- [x] Flag changed imported figures with the same period end. Preview warns before
  applying; applying preserves both source observations and marks reporting unresolved.
  Offline reviews show the conflict. Different period ends and price refreshes are
  excluded. This detects a discrepancy, not which source is correct.

## Remaining

As of 23 October 2026, the regression suite has 89 passing tests. This establishes
tested software behavior, not the accuracy of every company's fair value.

- [x] Reproduce the BDO bank example using justified P/B, dividend discounting and
  residual income under consistent assumptions. See [the BDO study](BDO_CASE_STUDY.md).
  Agreement is a model consistency check, not independent forecast evidence.
- [x] Separate parent and consolidated debt/equity in the
  [AC source worksheet](AC_SCOPE_REVIEW.md). Its replay returns no fair value
  because component values, remaining claims and matched common shares are missing.

- [ ] Reconcile individual dividend payment periods and revised earnings/share bases
  used in trailing-year calculations; period labels alone do not prove comparability.
- [ ] Validate cash-flow adjustments against company-specific report notes; the
  structured bridge cannot establish accounting classifications automatically.
- [ ] Independently reconcile worked examples across company types against filings
  and a separate calculation before relying on their valuation conclusions.
- [ ] Complete AC's attributable component values, remaining parent claims and
  matched common shares; justify the holding discount without double-counting debt.
- [ ] Support the worked examples' required returns and forecasts with dated
  evidence and a reasoned sensitivity range. Agreement with market price is not
  an acceptance criterion.

The next milestone is one complete, report-reconciled cash-flow case, followed by
the completed bank and holding-company research. Each needs reproducible source
inputs, supported assumptions and an independent calculation. No single percentage
can summarize readiness across blank templates, reviewed figures and forecasts.

## How to record evidence

Open **Edit company data**. Under **Valuation assumptions**, explain each saved
assumption, enter the review date and choose **Basis documented by me**. Changing
an input on the valuation screen does not inherit documentation for a different
saved value. Documentation is a user's record, not independent verification.

Under **Reporting review**, record any unresolved disclosure or revision. Change
it to **Issue reconciled by me** only after checking the affected figures, with a
date and explanation. Reviews older than 90 days are flagged. These thresholds
are review reminders, not guarantees that newer data is reliable.

Offline checks cannot discover new disclosures that have not been downloaded or
recorded. Blank company templates remain blank; these checks do not fabricate data.
The arithmetic can be tested independently, but forecast confidence must be judged
company by company using evidence, sensitivity and model suitability.

## Trailing EPS evidence

Use **Edit company data → EPS → Trailing-year EPS calculation and review** to
inspect or enter the three components and dates. **Use calculated trailing EPS**
applies their sum to the baseline. Saving changed components or baseline periods
resets comparability review, including edits through the API. Reopen the saved
record to document your new review. The arithmetic and period warnings still apply.

An imported calendar-year EPS bridge is saved under `sources.eps.eps_bridge` in
its company TOML file. The three EPS values and period ends remain individually
editable. The offline check reproduces annual + current YTD - prior YTD and
checks date alignment. Older TTM figures without this evidence are flagged.

A correct sum does not establish a comparable share basis. IAS 33 uses earnings
attributable to ordinary shareholders and weighted-average shares; changes in
share counts or revised earnings can invalidate simple addition of per-share
figures. See [IAS 33](https://www.ifrs.org/issued-standards/list-of-standards/ias-33-earnings-per-share.html/).

After checking the underlying statements, record `review_status = "reconciled"`,
`reviewed_on = "YYYY-MM-DD"` and a specific `review_note` within that bridge.
Explain revisions, corporate actions and denominator comparability. This records
user review, not independent verification. If the bases differ, reconstruct EPS
from comparable earnings and an appropriate trailing-period share denominator;
do not mark an incompatible bridge reconciled. New imports reset the bridge
review. The general reporting-review check still applies separately.

## Conflicting figures

When a selected import changes a saved financial figure for the same period end,
both observations are retained under `reports.source_conflicts` in the company
brain. Applying it still requires the normal explicit selection and confirmation.
The new figure becomes the working baseline; the previous value, source, dates,
units and file hash (when available) remain in the conflict evidence and backup.

Use **Reporting review** to explain whether the difference came from duration,
units, scope, revisions or a parsing error before marking it reconciled. This
review is a user declaration. The evidence remains saved after reconciliation.
Only downloaded/scanned and selected imports are covered: this does not compare
every available filing or detect an undisclosed change automatically.
