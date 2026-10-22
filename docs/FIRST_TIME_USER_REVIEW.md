# First-use regression cases

These cases cover defects found during release testing. The current implementation
passes the saved-analysis regressions; see [verification](VERIFICATION.md).

## Advanced-method reopening

Select DEMO, enable Advanced methods, calculate an AFFO example and save it. Reload
the page and load the saved inputs. The method must be selected automatically,
Advanced methods must be enabled, and calculation must require fresh confirmation.
Editing the comparison ratio must invalidate the previous result.

The AFFO example tests form persistence; it does not establish suitability for the
synthetic consumer company.

## DCF helper evidence

Calculate DEMO's cash flow and net claims with the helper, save the DCF, reload and
save it again. Both helper records must survive with their original sources and
saved-origin context. Manually changing cash flow must remove its old derivation
while retaining the unchanged net-claims evidence.

## Onboarding and missing data

Try demo must open the populated synthetic company. Real-company templates must
remain blank, and missing required inputs must block calculation. An empty report
folder must show its location and disable scanning until a file is available.

## Reproduction

Build the source archive and run `python scripts/first_user_review.py`. The script
uses a temporary extraction, checks the expected behavior and writes its observations
to `runtime/user-walkthrough/`. This is automated browser testing, not a human
usability study.
