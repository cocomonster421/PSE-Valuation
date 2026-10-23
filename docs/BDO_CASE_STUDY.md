# BDO: what supports a premium to book?

Reviewed 23 October 2026. Retrospective FY2025 modeling example, using information
published afterward. This is neither a backtested trading decision nor a current
price target.

## Source and denominator checks

BDO's [share information](https://www.bdo.com.ph/about-bdo/investor-relations/share-information)
reports FY2025 common equity of PHP 634,894 million, 5,334 million common shares,
book value per share of PHP 119.03 and a year-end reference price of PHP 134.60.
The per-share series carries a property-dividend adjustment note. The separate
preferred-share count must not be added to the common denominator.

```text
Common book value per share = 634,894 million / 5,334 million = 119.02775
Historical price/book = 134.60 / 119.03 = 1.13081 times
```

The [FY2025 results release](https://www.bdo.com.ph/about-bdo/learn/news-and-features/bdo-net-income-full-year-2025)
reports 14.4% return on average common equity. This is historical profitability,
not the sustainable return on beginning book equity required by the model.
The distinction matters when equity grows, shares change or profits are unusual.

## Model judgment

For a bank, lending assets and deposit funding are central to operations. An
industrial FCFF model with a mechanical net-debt deduction is a poor starting
point. This example values common equity through book value and the return earned
above shareholders' required return. Clean-surplus consistency, credit quality,
other comprehensive income and regulatory capital still require investigation.
See [CFA Institute: residual income valuation](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/residual-income-valuation).

Use 14% sustainable ROE, a 12% required equity return and 3% perpetual growth as
explicit **scenario assumptions**. The historical 14.4% provides context for 14%,
but does not establish a forecast. The 12% hurdle is not a measured cost of equity.

```text
Justified P/B = (14% − 3%) / (12% − 3%) = 1.22222
Scenario value = 119.03 × 1.22222 = PHP 145.48
```

| Sustainable ROE | 10% required return | 12% required return | 14% required return |
| --- | ---: | ---: | ---: |
| 10% | 119.03 | 92.58 | 75.75 |
| 12% | 153.04 | 119.03 | 97.39 |
| 14% | 187.05 | 145.48 | 119.03 |
| 16% | 221.06 | 171.93 | 140.67 |

Growth is held at 3%. If ROE equals required return, value equals book; growth
creates a premium only when reinvestment earns more than the equity hurdle.
The historical price implies 13.18% sustainable ROE under the chosen 12% hurdle
and 3% growth. That is a reverse calculation, not evidence those assumptions hold.

## Payout consistency check

The assumptions imply retention of 3% / 14% = 21.43%, hence a **78.57% payout**.
Next-year modeled earnings are 119.03 × 14% = 16.6642 per share; modeled dividends
are 16.6642 × 78.57% = **13.0933**. This is not a declared BDO dividend.

The replay compares justified P/B with five-year residual income, 1,000 separately
discounted residual-income payments and DDM using this consistent payout. All give
145.48. DDM takes a base dividend, so its input is 13.0933 / 1.03, not 13.0933.
Agreement tests implementation and assumptions; it is not independent investment
corroboration. Without evidence that the implied distribution and capital policy
are feasible, this model cannot support a target.

### Compare the required payout with the cash policy

The [April 2025 dividend policy](https://www.bdo.com.ph/content/dam/bdounibank/en-ph/about-bdo/investor-relations/financials/pdf/dividend-information/dividend-policy/bdo-dividend-policy-statement-2025.pdf)
sets regular quarterly cash at PHP 1.10 starting Q2, or PHP 4.40 annualized.
A [May 2026 declaration](https://edge.pse.com.ph/downloadHtml.do?file_id=1918558)
also specifies PHP 1.10. This later observation is retrospective corroboration.

At the scenario's 3% growth, next-year regular cash would be 4.40 × 1.03 = 4.532.
The equivalent-model distribution of 13.0933 is about **2.89 times** that amount.
Discounting only the growing regular cash at 12% gives 4.532 / (12% − 3%) =
**PHP 50.36**. This is a contrasting scenario, not a replacement price target.

The gap exposes an assumption: book-based value requires a path to distributing
the modeled earnings or releasing capital. Regular cash dividends alone do not
demonstrate that path. Investigate other distributions, capital needs and future
payout changes. The annualized policy is neither actual FY2025 cash received nor
total shareholder distributions; special/property dividends and buybacks require
separate treatment. Do not interpret the difference as a proven mispricing.

## Reproduce and extend

```sh
python scripts/replay_bdo_case.py
```

In the app, click **Open BDO bank example**, inspect **Sources and assumptions**,
confirm the inputs and click **Calculate fair value**. This loads justified P/B
with the dated figures above; the result should be PHP 145.48. Change ROE or the
required return to inspect the sensitivity. Saved analyses retain the source links
and qualifications in their notes. Loading the example does not change your brain.

Edit [the case inputs](../examples/bdo_case.json) to change the bundled example.
For residual income use payout 78.57142857%. The company brain remains unchanged
unless you explicitly save company data.

Before forming an investment view, reconcile common equity to the audited balance
sheet, review capital needs and credit losses, forecast sustainable profitability,
calibrate the return requirement and test a transition to mature growth. The sourced
book-value check and formula agreement are complete; that investment work is not.
