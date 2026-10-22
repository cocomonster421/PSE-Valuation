# First-time user review — 22 October 2026

Historical review: the findings below describe the pre-fix version. See [completed fixes](FIX_CHECKLIST.md) and the [final audit](FINAL_USER_AUDIT.md) for the verified current state.

The basic valuation flow works, and the tested P/E and DCF arithmetic is correct. The app still has two reproducible saved-analysis defects and several first-use obstacles. I would fix the saved-analysis defects before presenting it as a finished portfolio project.

## Scope and evidence

This is an agent-led novice walkthrough, not a usability study with independent participants. I used installed Microsoft Edge with a fresh browser context and a temporary extraction of the public ZIP. I inspected the landing and DCF screenshots. Actual company files and existing analyses were untouched. No application fixes were made during this review.

The tested ZIP contains 61 blank real-company templates and one populated synthetic company, DEMO. Your private workspace has different, populated company data. Findings about blank inputs apply to the public package, not automatically to your private copy.

Reproduction: `python scripts/first_user_review.py` (development-only Playwright and installed Edge required). Raw observations are in `runtime/user-walkthrough/results.json`; screenshots are in that folder. The script records the defects rather than treating a successful process exit as an all-clear.

This pass tested browser use and local server operation. It did not repeat Python installation, double-click the Windows launcher, test online PSE access, or re-verify all 14 models. Existing clean-install/package checks and report extraction checks are documented separately in [VERIFICATION.md](VERIFICATION.md) and [REAL_REPORT_CHECK.md](REAL_REPORT_CHECK.md). Prior passing checks do not supersede the new defects below.

## Walkthrough

| Step | What I did as a new user | Actual result | Assessment |
| --- | --- | --- | --- |
| 1. Find how to start | Read README setup and launcher instructions. | Python is a prerequisite; optional report tools require setup. | Documented, but not a one-click install on a computer without Python. Installation was not rerun in this pass. |
| 2. Open the app | Open the extracted app in a fresh browser. | Clean Stock Analyzer header, search box, stock list, Saved analyses. | Clear first action. No prominent explanation that real-company data is blank in this public edition. |
| 3. Choose a stock | Open the arrow and search URC. | All 62 entries are available; URC opens correctly. | Pass. The list scrolls; only several entries fit on screen. DEMO is alphabetically buried, not offered as a first step. |
| 4. Choose P/E | Select P/E for URC. | Missing EPS and comparison ratio; no prefilled real price. | Correct missing-data handling, but a newcomer cannot immediately reproduce the intended real-stock workflow offline. |
| 5. Try calculating empty data | Check Inputs reviewed and calculate. | No fair value is produced; required fields block submission. | Pass: confirmation does not fabricate missing figures. |
| 6. Find reports | Open Update from reports for URC. | Dialog tells me to put PDF/HTML/text into `reports/URC/`, then choose a report, period, units and optional pages. | Folder guidance exists. The empty dropdown offers no obvious file-opening shortcut, and I still need accounting/report knowledge. |
| 7. Try a complete example | Search DEMO and choose P/E. | EPS 5, price 50, comparison P/E 12 produce fair value 60. Current P/E is shown separately as 10. | Pass. This should be the first suggested experience for a GitHub visitor. |
| 8. Experiment | Replace comparison P/E 12 with 10. | Fair value changes to 50. | Pass. UI explicitly explains that using current P/E simply returns current price. |
| 9. Try DCF | Select DEMO DCF, expand the cash-flow helper, apply calculated figures, confirm and calculate. | Business cash 5,000,000; net claims 2,000,000; fair value 48. | Pass for this controlled example. Field help exists, though the expanded form becomes long. |
| 10. Save and return | Save DCF, reload, open Saved analyses, Load inputs, confirm and recalculate. | Same inputs and fair value 48. | Numeric replay passes. Structured helper evidence is lost if the loaded analysis is saved again; see finding 2. |
| 11. Try an advanced method | Enable Advanced methods, calculate and save an AFFO example; reload and load it. | Method selection becomes blank and a JavaScript exception occurs. | Fail; see finding 1. The AFFO example was only a UI persistence probe, not a recommendation for DEMO. |

All browser requests during these flows stayed local. This confirms these particular flows can run offline; it does not prove online refresh works or that all possible features were exercised.

## Independent arithmetic checks

These checks use the synthetic inputs, not current financial claims about any listed company.

| Check | Independent calculation | App result |
| --- | --- | --- |
| Current P/E | Share price 50 ÷ EPS 5 = 10× | 10× |
| P/E fair value | EPS 5 × comparison P/E 12 = 60 | PHP 60.00 |
| Using current P/E as target | EPS 5 × current P/E 10 = 50 | PHP 50.00 |
| Annual business cash | Operating profit 10,000,000 × (1 − tax 25%) + depreciation 1,000,000 − capital spending 3,000,000 − working-capital increase 500,000; other adjustments zero | PHP 5,000,000 |
| Net claims | Debt 4,000,000 − cash 2,000,000 + other claims 0 | PHP 2,000,000 |
| DCF fair value | With both growth rates zero, constant annual cash 5,000,000 discounted at 10% has enterprise value 50,000,000. Subtract net claims 2,000,000 and divide by 1,000,000 shares. | PHP 48.00 |
| DCF price comparison | 48 ÷ 50 − 1 = −4% | −4.0% |

Correct arithmetic does not validate an assumed comparison ratio, growth rate, discount rate, or underlying company data. The tested app correctly distinguishes current P/E from a valuation assumption. An independent comparison P/E still needs a defensible basis; it cannot be inferred solely from current price and EPS without making the valuation circular.

## Reproduced defects

### 1. Saved advanced-method analyses fail to reopen — high priority

Reproduce: select DEMO → enable Advanced methods → choose AFFO → populate required inputs → calculate → save → reload → Saved analyses → Load inputs.

Expected: the saved method becomes available and its inputs load.

Actual: the method selector is blank; browser error: `Cannot read properties of undefined (reading 'fields')`. A subsequent input-review request returns 400. A normal newcomer receives a broken workspace rather than actionable recovery guidance.

Cause observed in `frontend/app.js`: loading chooses the stock with the default basic-method list, then sets the selector to an advanced method that is absent. `renderFields` then accesses the missing method definition.

Acceptance: loading any saved method restores the appropriate selector option, populates inputs, requires fresh confirmation and produces no browser error. Temporary workaround: enable Advanced methods before loading the saved analysis.

### 2. Re-saving loaded DCF inputs drops structured helper evidence — medium priority

Reproduce: DEMO DCF → Use calculated figures → calculate → save as Review DCF → reload → Load inputs → recalculate → save as Review DCF reopened.

Actual saved records: original `derivations` length 2; reopened/resaved length 0. Both fair values remain 48. The original saved record is retained; this is loss of structured provenance in the new record, not destruction of the original or a numerical valuation error. Text notes may still contain helper equations.

Cause observed: `renderFields` resets the derivations list and the saved-input loader does not restore it.

Acceptance: preserve the historical helper inputs and source context when reopening, distinguish them from current company data, and invalidate or update them when relevant inputs change. A resaved analysis should retain a traceable link or the applicable original derivations.

## First-use improvements

- [ ] Fix advanced-method reopening and add a saved-analysis regression check.
- [ ] Preserve helper evidence across load/recalculate/save, with explicit historical provenance.
- [ ] Add a short public-edition hint: “Try DEMO. Real-company templates need your data.” Keep the header clean; one compact action is enough.
- [ ] Make the empty report state explicit and offer a clear way to locate the company folder. “Scan selected report” would better match the current one-file selection than “Scan folder.”
- [ ] Give a beginner a practical path for choosing a comparison P/E: documented peer/history observations and dates, or an explicitly illustrative practice value. Do not invent a current industry average.
- [ ] Format calculation rows as readable numbers, avoiding expressions such as `5e+06` and `4.8e+07`. The formula paragraph uses field names, but scientific notation in the numeric steps makes manual calculator checking harder.

The report importer remains assisted extraction, not “drop any report and everything is ready.” Earlier real-report checks found partial extraction from URC's annual report and rejected ambiguous quarterly layouts. This walkthrough only inspected the empty import flow; it did not repeat those PDF tests. Retain review of period, units, ownership scope, source rows and missing adjustments.

## Verdict

A newcomer who follows the DEMO walkthrough can calculate and experiment successfully. A newcomer who immediately chooses a real stock in the public package will need clearer onboarding and their own figures. Core P/E and DCF arithmetic passed this walkthrough, but saved advanced analyses and helper provenance need repair before calling the workflow complete.
