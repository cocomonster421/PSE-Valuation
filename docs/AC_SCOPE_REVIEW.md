# AC: reconcile ownership and claims before SOTP

Reviewed 23 October 2026; FY2025 evidence. This worksheet is incomplete and produces
no fair value. It identifies the source work needed before using the app's SOTP.

## Figures checked

The [2025 integrated report](https://ayala.com/app/uploads/2026/04/Ayala-Corporation-2025-Integrated-Report.pdf),
PDF page 75, printed pages 146–147, was checked as both text and a rendered page.
It distinguishes parent cash of PHP 13.8 billion and parent net debt of PHP 136.3
billion from consolidated cash of PHP 67.3 billion and net debt of PHP 637.2 billion.
The 11.5% LTV definition excludes fixed-for-life perpetuals. It therefore does not
establish common-share NAV by mechanically dividing net debt by that ratio.
The local worksheet records the report hash; the report itself is not redistributed.

The [PSE EDGE annual summary](https://edge.pse.com.ph/companyPage/financial_reports_view.do?cmpy_id=57)
uses PHP thousands for balance-sheet totals:

```text
Consolidated assets       1,891,567,429
Less liabilities         1,081,718,856
Consolidated equity        809,848,573
Less parent equity         511,662,496
Noncontrolling equity      298,186,077
```

This reproduces group equity, not common-share NAV. Parent-attributable equity can
still contain claims other than ordinary common equity. Reported BVPS is 748.41;
do not divide consolidated equity by the latest common share count to recreate it.

## Which input goes where?

In the app, choose SOTP and open **Add up owned businesses**. Enter each
component's value type, value in full pesos, owned percentage, valuation date and
source explanation. **Use component total** fills the owned-asset total. Enter
remaining parent claims, common shares and the holding discount separately.
Saving the analysis retains the rows; loading its inputs restores them for editing.
The helper does not change the company brain or supply missing AC valuations.

For a synthetic check, enterprise value 1,000 minus subsidiary net claims 200,
owned 60%, contributes 480. Entering equity value 800 at 60% gives the same result.
An already-owned equity value of 480 uses 100% and no further subsidiary deduction.
With remaining parent claims 80, ten common shares and a 10% holding discount,
the result is (480 − 80) × 90% / 10 = 36 per share. These are invented numbers.

The helper rejects duplicate component names, missing sources, ownership outside
0–100%, debt deductions from equity values, and a second ownership adjustment to
already-owned equity. It flags mixed valuation dates and negative component equity.
It cannot discover overlapping investments with different names or certify that
the values, ownership stakes and claims are economically appropriate.

| Starting value | Required treatment |
| --- | --- |
| Subsidiary enterprise value | Deduct that subsidiary's net claims to obtain equity, then apply the owned percentage |
| Subsidiary equity value | Apply the owned percentage; do not deduct its debt again |
| Already attributable equity value | Neither reapply ownership nor subtract subsidiary debt again |
| Sum of attributable equity values | Reconcile remaining parent claims, then divide by matched common shares |
| Consolidated book assets | Use matching liabilities and ownership claims; this is a book-asset calculation, not a market SOTP |

Using consolidated instead of parent net debt changes the deduction by **PHP 500.9
billion**. That difference is not a ready-made valuation adjustment: the correct
claims depend on how each component was valued. Review preferred/perpetual claims,
intercompany balances, guarantees, taxes and corporate costs separately, avoiding
items already captured in component cash flows or prices.

A holding discount is an analyst assumption, not a standard percentage supplied
by an annual report. It may reflect governance, costs or realization constraints.
Do not apply it to compensate for missing components or duplicate claims.

## Unfinished evidence

- Dated equity values and ownership percentages for listed and unlisted components.
- Remaining parent claims and their treatment, beyond the headline net debt figure.
- A common-share denominator matched to the valuation date and capital structure.
- A documented discount, or a reasoned zero-discount case with sensitivity.

```sh
python scripts/replay_ac_scope.py
```

The replay checks the balance-sheet arithmetic and scope difference, and returns
`fair_value: null`. These checks demonstrate why a plausible total is insufficient;
they do not complete AC's valuation. The [editable worksheet](../examples/ac_scope_check.json)
keeps missing inputs explicit.
