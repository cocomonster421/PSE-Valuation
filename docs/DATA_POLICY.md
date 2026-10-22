The public release contains 61 blank company templates plus a synthetic DEMO. The historical figures described below apply only to the private workspace, not the public package. Downloaded report text and research history are excluded from the release.

# Company data and assumptions

The bundled 61 records are a local research collection, not a claim about current
index membership. The active watcher cache selected during migration was generated
on October 12, 2026. Each quote retains its own source timestamp; individual report
publication dates and financial periods may be older. Nine records had no industry
label and are explicitly marked unclassified for manual review.

## What is prefilled

The importer retains available common shares, EPS, common book value per share,
dividends, ROE, payout and price references. Imported financial metrics remain
`needs_review`. The reported date may be a publication date rather than the
effective period of that particular metric; the UI preserves that qualification.

Compact historical extracted facts retain period, currency, unit, scope, candidate
status, source URL and document identifier. They are not automatically used to fill
DCF inputs. Original reports, extracted report text and the watcher's database are
not required or distributed with the standalone application.

## Updating a company

Use **Edit company data** to change a value, date, source URL, review status and
notes. Financial period end is a separate optional field. A source link or an
explanatory note is required for a populated figure. Changes are saved as actual
PHP values, decimal rates and per-share values according to each field definition.
Previous complete records are preserved under `runtime/revisions/`.

You may edit `brain/TEL.toml` in a text editor instead. Keep the schema and
numeric values valid. If a stock file is malformed, that stock is labeled as needing
repair while the others remain available. Fix the file or restore a backup; the app
does not silently replace invalid user data with defaults.

## Modeling assumptions

The default 3% explicit forecast growth, 2% terminal growth and 15% NAV discount are
illustrative starting values, not verified company forecasts. Missing discount
rates and unsupported financial inputs stay blank. Defaults are editable through
**Edit method policies** or `policies/catalog.json`.

The beta calculator starts from the company's saved Philippine government-rate
benchmark when one exists, showing its date. Beta, equity premium, debt cost, tax
and capital weights initially contain illustrative values. A computed rate is only
applied when you select the button; its components are appended to the thesis notes.

FCFF and FCFE have separate baseline fields. Do not treat operating cash flow minus
capital expenditure as either measure without reviewing financing, taxes, claims,
scope and adjustments. The interface keeps their definitions visible.

## Traceability

A calculation preserves the input values and engine version. Saving also preserves
the company's complete compact record and the method policy. Changed source revisions
are rejected at save time. Export includes the inputs and snapshots available when
the analysis was created. Loading a saved analysis places its inputs into a new
working form; it requires confirmation against the current baseline before reuse.

The five-year DCF assumes constant explicit-period growth. DDM uses a constant-growth
perpetuity. NAV/SOTP/RNAV accept reviewed component totals rather than independently
valuing each subsidiary or property. Embedded value accepts reviewed actuarial
inputs rather than building an actuarial projection. These limits are deliberate
and should be explained when presenting an analysis.
