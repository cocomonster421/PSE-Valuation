# Company data and assumptions

The repository contains 61 blank real-company templates and one synthetic DEMO.
Company names, source links and profiles are saved metadata, not a guarantee of
current index membership or method suitability. Unclassified industries require
manual review. DEMO values are invented and are not investment estimates.

## Company figures

Use **Edit company data** to record a value, effective date, financial period, source
URL, review status and notes. Populated figures require a date and a source or note.
Changes made through the app are backed up under `runtime/revisions/`.

Alternatively, edit a company's TOML file as described in the [file guide](../brain/README.md).
Malformed files are flagged rather than replaced with defaults. Publication dates
and financial period ends are distinct. Report imports remain subject to review;
unsupported values are not inferred.

## Assumptions

Policy defaults such as 3% forecast growth, 2% terminal growth and 15% asset-value
discount are illustrative. They are not company forecasts or market averages.
Company-specific assumptions take priority over global defaults. Missing company
facts and required discount rates remain blank unless explicitly supplied.

The discount-rate helper can use a saved benchmark with its date. Its fallback
risk-free rate, beta, equity premium, debt cost, tax rate and capital weights are
illustrative until verified. Applying a rate records the components in analysis notes.

FCFF and FCFE use separate baseline fields. Review taxes, financing, ownership scope,
working capital and capital investment before calculating either measure. Do not
assume operating cash flow minus capital expenditure is automatically FCFF.

## Saved analyses

Saved analyses include inputs, engine version, results, company/policy snapshots,
source-readiness checks and applicable helper derivations. Company or policy changes
are checked before saving. Loading an analysis requires review against the current
baseline; retained helper records describe the original calculation and its sources.
Manual changes to a derived output remove the old evidence for that output.

Private reports, scenarios and revision backups are ignored by Git. Company TOML
files are tracked: use the release builder to strip personal figures before sharing.

## Model limits

DCF assumes five years of constant forecast growth. DDM uses a constant-growth
perpetuity. Asset models accept reviewed component totals. Embedded value accepts
actuarial estimates rather than generating them. Readiness checks flag missing,
stale and mixed-period data but do not verify its accuracy.
