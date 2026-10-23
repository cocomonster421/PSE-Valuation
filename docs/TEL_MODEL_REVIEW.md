# TEL formula and assumption review

Review date: 22 October 2026. Scope: the published TEL dividend example and the
discounted-cash-flow calculations that could be used to cross-check it.

## Finding

No arithmetic error was found in the TEL dividend calculation. Its low result is
driven by the chosen required return and growth rate. Calling it a base-case fair
value gives those uncalibrated assumptions too much weight. The case and README
now describe it as an illustrative scenario; the original inputs remain reproducible.

The [CFA Institute's dividend valuation reference](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/discounted-dividend-valuation)
defines the constant-growth value as next year's dividend divided by required
equity return minus growth. The engine correctly grows the base dividend once:

```text
Next annual dividend = 92 × 1.01 = 92.92
Scenario value = 92.92 / (0.12 - 0.01) = PHP 844.73
```

The input is annual dividends per common share, not one semiannual payment or a
company-wide amount. There is no second share-count division or debt deduction.
The August [PLDT filing](https://www.sec.gov/Archives/edgar/data/78150/000119312526348006/phi-ex99_1.htm)
confirms the PHP 46 September common dividend. The
[FY2025 release](https://www.sec.gov/Archives/edgar/data/78150/000119312526073891/phi-ex99_1.htm)
provides the final PHP 46 used with it. These are declared payment schedules, not a promise
of future distributions. Using the FY2025 earnings-year dividend of PHP 94 instead
would produce PHP 863.09 under the same assumptions, only 2.17% higher.

## What changes the result?

All rows use a PHP 92 base annual dividend. These are arithmetic scenarios, not
recommended assumptions or a probability range.

| Required equity return | Perpetual dividend growth | Value per share |
| --- | --- | ---: |
| 12% | 1% | 844.73 |
| 10% | 2% | 1,173.00 |
| 12% | 4% | 1,196.00 |

The PHP 1,190 reference price implies approximately 3.96% perpetual dividend growth
at a 12% required return. This reverse calculation describes market-implied
assumptions; it does not validate them. Revenue growth is not automatically dividend
growth: payout policy, reinvestment, leverage and financing also matter.

## Checks completed

- Summed 1,000 separately discounted annual dividends, independently of the Gordon
  formula, to reproduce the TEL result.
- Compared DDM with five-year FCFE plus continuing value when all shareholder cash
  is distributed and growth/risk assumptions match, including declining dividends.
- Checked that changing the market price changes the valuation gap, not model value.
- Re-ran the growing-annuity DCF check, share scaling, debt bridge and invalid-input
  tests. FCFF subtracts net debt once; FCFE does not subtract it again. The continuing
  cash flow starts in year 6 and its value is discounted from year 5.

FCFF requires WACC and FCFE requires the cost of equity; the same rate should not
be copied between them without justification.
[CFA Institute: free cash flow valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation)

## Additional source review

### Financial reporting status

PLDT's [13 August disclosure](https://www.sec.gov/Archives/edgar/data/78150/000119312526347926/phi-ex99_1.htm)
reports a material weakness in financial-reporting controls, planned revisions and
withdrawal of SGV's original 2025 financial-statement and internal-control opinions.
Management did not expect a material impact on net income, EPS or cash flows, but
that expectation is not a completed reconciliation. The
[25 September clarification](https://www.sec.gov/Archives/edgar/data/78150/000119312526401539/phi-ex99_1.htm)
explicitly directs readers to read the original annual report with that disclosure.
The EPS bridge remains provisional pending reconciliation of revisions. These
disclosures do not themselves change the historical common dividend payments.

### Cash generation cross-check

The [H1 2026 interim filing](https://www.sec.gov/Archives/edgar/data/78150/000119312526347861/phi_6-k_2q2026_v2.htm),
cash-flow statements and liquidity discussion, reports the following in PHP millions:

| Item | H1 2026 | H1 2025 |
| --- | ---: | ---: |
| Net cash from operating activities | 45,776 | 46,705 |
| Cash purchase of property/equipment, including capitalized interest | 23,736 | 34,078 |
| Difference, before remaining adjustments | 22,040 | 12,627 |

This difference improved despite lower operating cash generation, because cash
investment spending fell. It is neither normalized FCFF nor cash distributable to
common shareholders. The filing also identifies PHP 7,835 million of lease-obligation
settlements in H1 2026, versus PHP 6,944 million in H1 2025. Interest, financing, leases, other investments and minority
claims must be reconciled before using the difference in a valuation. Do not double
the half-year difference and label it annual FCFF. Cash purchases also differ from
the headline PHP 20.7 billion capex measure.

### Required return context

The [20 October BTr auction](https://www.treasury.gov.ph/wp-content/uploads/2026/10/Treasury-Bond-Auction-Result-on-20-October-2026.pdf)
reported a 7.830% average yield for a bond with 4.8 years remaining. Its 8% coupon
is not the auction yield, and its original 20-year label is not its remaining tenor.
This is market context, not a replacement for the app's short-term benchmark policy
or a measured TEL cost of equity. A 12% equity hurdle is 4.17 percentage points above
that yield; the spread alone does not establish the appropriate equity premium.
Lowering the hurdle solely to obtain a higher valuation would be unsupported.

## Still needed for a defensible TEL target

- A dated, supported cost-of-equity estimate with consistent currency, risk-free
  benchmark and equity risk assumptions, instead of the selected 12% hurdle.
- A forecast of sustainable distributions based on cash generation, investment,
  debt service and payout policy. Use multiple growth stages if appropriate.
- An independently sourced FCFE or FCFF reconciliation and a justified peer/history
  valuation cross-check. Avoid plugging reported free cash flow into FCFF without
  reconciling interest, leases and financing.

Passing formula tests does not establish the accuracy of source data or forecasts.
This review does not establish a new TEL price target or certify every specialist
valuation model. Company quality alone is not evidence that a calculated value
must exceed its market price.

## Source reconciliation update — 23 October 2026

The interim filing's Note 8 (F-55) reports weighted-average common shares of
216,056 thousand for both half-years. Common-share earnings are PHP 16,417 million
in H1 2026 and PHP 17,443 million in H1 2025. Dividing these rounded amounts gives
approximately 75.9849 and 80.7337; the reported EPS figures are 75.99 and 80.73.
The small differences are consistent with rounding. Using total equity-holder
income without removing preferred dividends would use the wrong numerator.

This supports the interim share-basis comparison only; it does not complete the
annual-revision reconciliation. The replay now retains and checks these figures.

**Correction:** the earlier cash discussion assigned H1 2025 lease settlements
of PHP 6,944 million to H1 2026. The correct H1 2026 amount is PHP 7,835 million.
This was a period-transcription error in research notes; neither amount feeds the
published DDM calculation. It reinforces why the two periods must be retained
side by side before constructing a cash-flow valuation.

The dividend ledger now records declaration, record and scheduled payment dates
for each common dividend. The cited declarations substantiate the payment schedule;
they do not independently prove individual receipt. The PHP 92 scenario uses the
two scheduled payments falling within the case's trailing-year window. Preferred
and special dividends are excluded. Future maintenance remains an assumption.
