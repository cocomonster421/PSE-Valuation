# TEL: does the dividend justify the price?

**Research date: 22 October 2026 · PLDT Inc. · PHP per common share**

| Reference price | DDM base case | Difference vs price | Tested range |
| --- | --- | --- | --- |
| 1,190.00 | 844.73 | −29.0% | 657.14–1,173.00 |

**Conclusion:** this dividend-based screen does not establish a margin of safety at
the reference price. A 7.73% trailing yield is not enough by itself: the base case
requires 12% annual equity return and assumes only 1% perpetual dividend growth.
The conclusion is conditional on those choices, not a claim that the market is wrong.

![TEL valuation in the application](screenshots/tel-overview.png)

## Evidence and accounting choices

| Item | Figure / period | Source and treatment |
| --- | --- | --- |
| Last traded price | 1,190; 22 Oct 2026, 14:50 Asia/Manila | [PSE EDGE stock data](https://edge.pse.com.ph/companyPage/stockData.do?cmpy_id=6&security_id=134). Dated intraday snapshot, not the day's close or a live quote. |
| FY2025 basic EPS | 138.63 | [PSE EDGE financial reports](https://edge.pse.com.ph/companyPage/financial_reports_view.do?cmpy_id=6), annual income statement. Per-share amounts are pesos, not millions. |
| H1 EPS | 75.99 in 2026; 80.73 in 2025 | Same source, year-to-date basic EPS columns. Use six-month figures rather than the adjacent three-month columns. |
| FY2025 earnings-year dividend | 94 | [PLDT FY2025 results, filed 26 Feb 2026](https://www.sec.gov/Archives/edgar/data/78150/000119312526073891/phi-ex99_1.htm). Includes a final 46 declared in 2026; this is not the trailing payment total at the case date. |
| Latest twelve-month payments | 46 in April 2026 + 46 in September 2026 = 92 | [PSE EDGE dividend records](https://edge.pse.com.ph/companyPage/dividends_and_rights_form.do?cmpy_id=6), checked against the [August 2026 dividend filing](https://www.sec.gov/Archives/edgar/data/78150/000119312526348006/08.13.2026_boardmeeting.htm). Both common-share cash dividends. |

Derived earnings check: **138.63 + 75.99 − 80.73 = 133.89 TTM EPS** for the twelve
months ended June 2026. This roll-forward uses the published per-share series; it
assumes comparable share bases and no unadjusted restatement. Reconcile those if a
subsequent filing changes the comparatives. Current P/E = 1,190 / 133.89 = **8.89×**.
This is descriptive, not a justified target multiple.

Trailing dividend / TTM reported EPS = 92 / 133.89 = **68.7%**. The periods differ:
dividends are payments through September; earnings end in June. This is a coverage
screen, not a matched-period payout ratio. PLDT's stated 60% FY2025 payout uses
Telco Core earnings, a different denominator; it should not be substituted for
reported earnings. [FY2025 results](https://www.sec.gov/Archives/edgar/data/78150/000119312526073891/phi-ex99_1.htm)

## Business interpretation

The latest half-year results show net service revenue up 1%, capex of PHP 20.7 billion
versus PHP 27.4 billion a year earlier, and net debt of PHP 287.3 billion at 2.6×
EBITDA. Lower investment spending can support distributions, but leverage and modest
revenue growth limit the case for aggressive dividend growth. Management reports
positive free cash flow; that label alone does not supply a normalized FCFF input.
[PLDT H1 2026 results](https://www.sec.gov/Archives/edgar/data/78150/000119312526348006/phi-ex99_1.htm)

DDM fits a question about cash returned to common shareholders. It is deliberately
narrow: retained cash, subsidiaries and growth investments may create value not
captured by a conservative dividend path. No enterprise DCF is presented because
this case does not reconcile operating cash, leases, maintenance/growth investment
and financing into a defensible annual FCFF base. Avoiding an unsupported model is
part of the analytical decision.

## Assumptions and calculation

| Input | Base case | Rationale / limitation |
| --- | --- | --- |
| Base annual dividend | 92 | Latest twelve-month regular payments. Maintaining this level is an assumption; it is not a declared FY2026 total. |
| Required yearly return | 12% | Chosen nominal PHP equity-return hurdle for a leveraged equity with payout risk. Not a measured CAPM estimate, industry average or WACC. A different required return materially changes the answer. |
| Long-run dividend growth | 1% | Conservative scenario consistent with limited recent revenue growth and payout uncertainty; not company guidance. Test 0–2%. |

```text
Next annual dividend = 92 × (1 + 0.01) = 92.92
Fair value = 92.92 ÷ (0.12 − 0.01) = 844.73
Difference vs reference price = 844.73 ÷ 1,190 − 1 = −29.0%
```

Use the cost of equity, not WACC, for dividends. Do not subtract net debt again:
dividends are already distributions to equity holders. Values are nominal, before
investor taxes and transaction costs. The model simplifies payment timing to annual
cash flows and does not separately value an imminent declared distribution.

## Two-variable sensitivity

Fair value per share; the PHP 92 base dividend is held fixed.

| Required return ↓ / Growth → | 0% | 1% | 2% |
| --- | ---: | ---: | ---: |
| 10% | 920.00 | 1,032.44 | 1,173.00 |
| 11% | 836.36 | 929.20 | 1,042.67 |
| **12%** | **766.67** | **844.73** | **938.40** |
| 13% | 707.69 | 774.33 | 853.09 |
| 14% | 657.14 | 714.77 | 782.00 |

The highest tested value is only 1.4% below the reference price: that small gap is
not robust to estimation error. The grid is a set of scenarios, not a confidence
interval or probability forecast. A 10% dividend cut reduces every cell by 10%.

At the reference price, the model requires either **3.96% perpetual dividend growth
at a 12% return hurdle**, or an **8.81% required return at 1% growth**. These reverse
calculations identify the assumptions behind a more favorable view. A lower hurdle,
a higher sustainable payout, or value outside the dividend stream could overturn
the screen; none is established by this case.

![Required-return sensitivity in the application](screenshots/tel-sensitivity.png)

## What would change the view?

- Sustainable cash generation after capex, leases and financing that supports a
  higher common dividend without increased borrowing.
- Lower leverage and a defensible lower cost of equity.
- A normalized FCFE/DCF or subsidiary valuation showing value beyond the dividend
  path, with consistent treatment of debt and minority interests.
- Adverse earnings, refinancing or capital-investment changes that weaken payout
  coverage. Earnings coverage alone is not cash coverage.

The case uses selected public sources available on the research date, not an
exhaustive review of every disclosure. It illustrates a conditional investment
judgment rather than a personal buy/sell recommendation. Dynamic source pages may
change; the cited dates and frozen inputs make the published calculation reproducible.

## Reproduce it without installing the report parsers

```sh
python scripts/replay_tel_case.py
```

[Machine-readable inputs and assumptions](../examples/tel_case.json) reproduce the
base case, EPS bridge, implied assumptions and all 15 sensitivity cells. In the app,
choose TEL → Dividend valuation (DDM), enter dividend **92**, required return **12%**,
growth **1%**, and price **1,190**. Add the cited dates/sources to Notes and confirm.
The general TEL brain remains a blank template; this dated research example is
separate from the editable baseline.

![Source notes beside editable financial inputs](screenshots/tel-sources.png)

Only discrete cited facts and original calculations are included. Source reports
and page images are not redistributed; third-party material is not covered by the
project's MIT license.
