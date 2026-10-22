# The company brains

Open a company's file in Notepad: **TEL.toml**, **BDO.toml**, **AREIT.toml**, etc.
These are the actual files the app reads. You can edit them directly or use
**Edit company data** in the website. You do not need to edit Python code.

Each file is organized in this order:

1. **company** — name, industry and PSE EDGE link.
2. **financials** — price, shares, EPS, dividends, book value and other figures.
3. **models** — editable assumptions for each valuation method.
4. **sources** — dates, links and notes behind the financial figures.

Synthetic example:

```toml
[financials]
dividend = 2.0
shares = 1000000
fcff_cash_flow = ""

[models.ddm]
discount_rate = 0.1085
terminal_growth = 0.02
```

`0.1085` means **10.85%**. Money totals are actual pesos, not millions.
`""` means **missing**, not zero. Enter numbers without commas.
Model assumptions are estimates, not facts reported by a company.

After changing a financial figure, update its corresponding `sources` date and note.
Save the file and reselect the company in the app to load the changes. Changes made
through the website save to the same file and create a backup automatically.

Each company has its own assumptions. These take priority over global policy defaults.
The five normal choices are DCF, dividends, earnings, book value, and assets.
**Advanced methods** exposes specialized variants when needed.

The public templates have blank financial data. DEMO contains invented values for
practice. Downloaded report text and private research histories are not distributed.

The PSE EDGE link beside the ticker opens the company information page when its ID
is known. That page links to financial reports, disclosures and dividends. Records
without a known ID link to the company directory. Opening the external source or
pressing **Refresh online** requires an internet connection; ordinary analysis does not.

To update from downloaded files, place them in `reports/TICKER/` beside this brain
folder. In the app, select the company and press **Update from reports**. Scan,
review the source rows and apply the selected figures. This updates this same TOML
file with dates and source evidence, and keeps a backup of the previous version.
PDF/text imports need the annual period and unit scale; saved PSE EDGE summary HTML
supplies its own dates. Unsupported or ambiguous figures stay blank for manual review.
