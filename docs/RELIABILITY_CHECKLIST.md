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

## Remaining

- [ ] Reconcile individual dividend payment periods and revised earnings/share bases
  used in trailing-year calculations; period labels alone do not prove comparability.
- [ ] Validate cash-flow adjustments against company-specific report notes; the
  structured bridge cannot establish accounting classifications automatically.
- [ ] Independently reconcile worked examples across company types against filings
  and a separate calculation before relying on their valuation conclusions.

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
