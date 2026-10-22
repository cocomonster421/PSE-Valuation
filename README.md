# PSE Valuation

An offline Philippine stock valuation workspace that uses fundamental analysis to
estimate fair value, with editable assumptions and reproducible calculations.

![Synthetic offline example](docs/screenshots/portfolio-demo.png)

## Getting started

Requires **Python 3.11 or newer**. Download and extract the repository, keeping its
folders intact. On Windows, double-click **Launch Workbench.cmd**. Alternatively:

```sh
python run.py
```

Open http://127.0.0.1:8765 and select **Try demo**. The synthetic example produces
PHP 60 per share using P/E and PHP 48 using DCF. The 61 real-company templates contain
company metadata but start with blank financial figures. They are a saved selection,
not a current index-constituent list.

For PDF/HTML imports and optional PSE EDGE refresh, run **Setup Report Tools.cmd**
once while online. It installs the pinned parser dependencies in `.venv`; the
Windows launcher uses that environment automatically. A command-line alternative is:

```sh
python -m pip install -r requirements-lock.txt
python run.py
```

Calculation and local report parsing work offline after setup. Stop the server with
Ctrl+C. If port 8765 is occupied, use `python run.py --port 8766`. The server accepts
connections only from the local computer. No Node installation or API key is needed.

## Workflow

1. Choose a company and a valuation method.
2. Review the financial figures, source dates and assumptions. Fill missing inputs.
3. Confirm the inputs and calculate fair value.
4. Use **Sensitivity → Compare values** to vary an assumption.
5. Save an analysis with notes, or export its inputs and results as JSON.

Editing the valuation form changes only that analysis. **Edit company data** updates
the saved baseline; **Edit method policies** changes defaults and recommendations.
Changes made through these editors create local backups and check for conflicting edits.

## Methods and assumptions

The main selector offers DCF, dividends, P/E, P/B and asset valuation. Recommendations
depend on the company profile and input availability. **Advanced methods** exposes
specialist models. The 14 implementations include FCFF and FCFE DCF, DDM, relative
and justified multiples, residual income, NAV/SOTP/RNAV, dividend capitalization,
P/AFFO, property capitalization and insurance embedded value.

**Current P/E = price ÷ EPS** describes the current market price. **Comparison P/E**
is the independently chosen ratio used for fair value. Using current P/E as the
comparison ratio simply returns current price. Record the basis and dates of any
peer or historical comparison in the analysis notes.

Growth, discount rates and valuation discounts are assumptions, not reported facts.
Default values are illustrative. Missing financial figures remain blank. Monetary
totals use full pesos; file-based rates use decimals, while the interface displays
percentages. DCF uses five forecast years and a continuing value. Terminal growth
must be below the discount rate and cannot exceed 5%.

See [formulas and references](docs/FORMULAS.md) and the
[data and assumptions policy](docs/DATA_POLICY.md) for definitions and limits.

## Updating company data

Use **Edit company data**, edit `brain/TICKER.toml` directly, or import a report:

1. Put a PDF, saved HTML page or text file in `reports/TICKER/`.
2. Choose the stock and select **Update from reports**.
3. Select one report. For PDF/text, enter its annual period and unit scale.
4. Click **Scan selected report**, compare proposed figures with the source rows,
   and apply only the figures checked.

The importer supports recognized text layouts. Scanned PDFs, ambiguous columns and
unsupported rows require manual entry. Saved PSE EDGE financial-summary HTML can
supply EPS and book value; DCF usually needs cash-flow statements and debt notes.
The DCF helper calculates cash flow and net claims from reviewed inputs.

**Refresh online** explicitly requests the latest available PSE EDGE price, EPS and
book value. Proposed updates require review before saving. A failed request preserves
existing data. Prices are dated snapshots and may be delayed.

## Project files

| Path | Purpose |
| --- | --- |
| `backend/` | Valuation formulas, validation, imports and local HTTP server |
| `frontend/` | HTML, CSS and JavaScript interface |
| `brain/` | Editable company TOML files and synthetic DEMO |
| `policies/catalog.json` | Method descriptions, recommendations and assumptions |
| `reports/` | Local report folders; downloaded files are ignored by Git |
| `scenarios/` | Local saved analyses; ignored by Git |
| `tests/` | Calculation, API, parsing, source-review and release tests |

See the [company-file guide](brain/README.md) and [demo walkthrough](docs/WALKTHROUGH.md).

## Testing

```sh
python -m unittest discover -s tests -v
python scripts/replay_example.py
```

Optional browser checks use Playwright and Microsoft Edge on Windows:

```sh
python -m pip install --target runtime/qa_packages playwright
python scripts/browser_check.py
python scripts/package_project.py
python scripts/first_user_review.py
python scripts/verify_package.py
```

Browser checks use temporary synthetic data. Outputs are written under `runtime/`.
`node --check frontend/app.js` provides an optional JavaScript syntax check.
See [verification scope](docs/VERIFICATION.md).

## License and distribution

Original code is available under the [MIT license](LICENSE). Company reports and
other third-party material remain subject to their owners' terms.

Use `python scripts/package_project.py` to build a shareable source ZIP. The script
replaces financial figures with blank templates and excludes local reports, saved
analyses and revision backups. Do not publish personal company data by committing
edited TOML files directly. See [release guidance](docs/PUBLIC_RELEASE.md).

GitHub hosts the source. The application runs locally; its Python backend cannot
run on GitHub Pages.
