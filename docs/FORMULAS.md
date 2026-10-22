# Formula references and assumptions

Reviewed against primary educational sources on 2026-10-22. This verifies equation structure, not any company's inputs or investment merit. Rates in files and saved results are decimals; the interface shows percentages.

| Model | Implemented equation and conditions |
| --- | --- |
| P/E and P/B | Annual EPS × comparison P/E; common book value/share × comparison P/B. Current price/metric is descriptive, not an independent valuation benchmark. |
| DDM | Annual recurring dividend × (1 + growth) / (required return − growth). Dividend input is the last/base annual dividend; use sustainable recurring payouts. |
| FCFF DCF | Discount five years of business cash at WACC; add discounted year-6 cash / (WACC − terminal growth), subtract net debt and other claims and divide by common shares. Add non-operating assets separately when appropriate. |
| FCFE DCF | Discount cash after financing at cost of equity; no second subtraction of debt. FCFE = FCFF − after-tax interest + net borrowing. |
| Cash helper | Operating profit × (1 − tax) + depreciation + other noncash adjustments − equipment investment − other investment − operating working-capital increase. Consistent annual scope required. |
| CAPM / WACC | Cost of equity = risk-free proxy + beta × equity premium. WACC = equity weight × cost of equity + debt weight × borrowing cost × (1 − tax). Market-value weights preferred; book debt can be a documented approximation. |
| Justified P/B | (Sustainable ROE − growth) / (cost of equity − growth), multiplied by book value/share. Growth and retention must be consistent. |
| Residual income | Book value/share + discounted excess earnings; excess earnings = beginning book × (ROE − cost of equity). Five explicit years followed by a continuing residual-income model. Terminal growth implies a new payout regime, shown in warnings. |
| NAV/RNAV | Gross reviewed assets less all corresponding liabilities/claims, optionally discounted, divided by shares. RNAV uses revalued assets. |
| SOTP | Ownership-weighted component equity values less remaining parent claims, optionally discounted, divided by shares. Subsidiary debt already in equity values must not be subtracted again. |
| Dividend capitalization | Sustainable annual dividend / chosen required yield. Equivalent to zero-growth DDM when the yield is the required return. |
| Property capitalization | (Stabilized NOI / capitalization rate − net claims) / shares. Gross property value is not common equity. |
| P/AFFO | Recurring AFFO/share × comparison multiple. AFFO is not standardized; compare like definitions. |
| Insurance embedded value | (Reviewed adjusted net worth + reviewed in-force business value) / shares. An aggregation tool, not an actuarial valuation engine; capital costs/options/risk adjustments belong in the reviewed inputs. |

## Primary references

- [CFA Institute: equity valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/equity-valuation-concepts-basic-tools)
- [CFA Institute: free cash flow valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/free-cash-flow-valuation)
- [CFA Institute: residual income valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/residual-income-valuation)
- [NYU / Damodaran: relative valuation and justified P/B](https://people.stern.nyu.edu/adamodar/pdfiles/ovhds/inv2E/relval.pdf)
- [NYU / Damodaran: risk-free rate and horizon](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/riskfreerates.htm)
- [OpenStax: costs of debt and equity](https://openstax.org/books/principles-finance-2e/pages/17-2-the-costs-of-debt-and-equity-capital)
- [California BOE: property capitalization](https://boe.ca.gov/info/iav/lesson12.htm)
- [Nareit: AFFO definition](https://www.reit.com/glossary/adjusted-funds-operations-affo)
- [CFO Forum: embedded-value framework](https://www.cfoforum.eu/publications/embedded-value)

## What the defaults do not establish

The original 91-day Philippine T-bill policy is a short-term proxy. A duration- and currency-consistent long-term benchmark may better suit DCF. Online stock refresh does not refresh the benchmark. Beta 1, premium 6%, debt cost 7%, tax 25%, debt weight 30%, forecast growth 3% and terminal growth 2% are illustrative starting assumptions, not measured company values. A 15% holding discount is not an industry fact. No formula certifies these defaults.
