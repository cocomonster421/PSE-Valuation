# Cash-flow reconciliation

Under either DCF method, open **Reconcile a cash-flow statement**. Use a full year
or trailing 12 months in full PHP. Identify the period, sources, ownership scope,
lease treatment and adjustments before applying the result. The inputs and
calculation trail are retained in saved analyses and replayed by the review check.

## Calculation

The standard CFO approaches distinguish firm cash flow from equity cash flow.
FCFF adds back after-tax financing interest to operating cash after interest and
deducts investment. FCFE retains financing interest and incorporates net borrowing.
[CFA Institute: free cash flow valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation)

The helper first subtracts financing interest reported outside operating cash flow
so that the starting cash measure is consistently after interest. It then applies
the chosen signed adjustments. These are reviewed inputs, not automatic accounting
reclassifications. Positive adjustments add cash; negative adjustments reduce it.

```text
Normalized operating cash = Reported operating cash flow
  − That interest paid outside operating cash flow
  + Other operating-cash adjustments

After-tax financing interest = Interest paid on financing debt
  × (1 − Tax rate for the interest deduction)

FCFF = Normalized operating cash + After-tax financing interest
  − Equipment and property investment − Other capital investment
  + Investment adjustments

FCFE = FCFF − After-tax financing interest
  + New debt financing − Debt principal repaid
  + Adjustment to cash attributable to common shareholders

Net claims (FCFF only) = Financing debt balance − Available excess cash
  + Other claims ahead of common shareholders
```

Do not subtract working-capital changes again: reported operating cash already
reflects them. Avoid counting capitalized interest in both interest and investment.
The tax input represents the assumed interest tax shield; a headline tax rate may
be inappropriate where deductions are limited or cannot be used.

## Lease and ownership consistency

- **Financing leases:** align lease interest, asset investment, new lease financing,
  principal repayments and the debt balance. Include relevant non-cash additions
  consistently in investment and financing; cash capex alone may be incomplete.
- **Operating leases:** normalized operating cash must include the relevant lease
  cash cost. Exclude lease financing from debt and borrowing inputs. Document any
  payments outside operating cash and related adjustments.
- **No material leases:** explicitly document that assessment; the app cannot infer it.

Consolidated cash flows may include subsidiary cash not attributable to the parent's
common shareholders. Explain minority/preferred treatment and avoid subtracting
the same claim both within cash flow and from enterprise value. Debt, ownership
claims and excess cash may also require valuation adjustments beyond book balances.

This helper requires a consistent accounting interpretation; it does not establish
one from the report automatically. Do not use it to force an enterprise DCF on a
bank or to treat temporarily high cash generation as a sustainable forecast.

## Independent checks

The tests verify that moving the same interest payment between operating and
financing classifications leaves reconciled value unchanged, and that FCFE agrees
with the direct after-interest cash calculation. Browser tests verify both methods,
the resulting valuation, and saved reconciliation evidence. Passing these tests
verifies arithmetic and persistence, not the quality of the supplied adjustments.
