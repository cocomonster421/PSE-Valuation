# Demo walkthrough

The application uses Python, HTML, CSS and JavaScript. BeautifulSoup and pypdf
support report extraction. A local server reads company TOML files and a method
catalog; saved analyses are stored separately.

1. Run the launcher and select **Try demo**.
2. Choose **P/E**. EPS 5 × comparison P/E 12 gives PHP 60. Current P/E is
   50 ÷ 5 = 10; substituting it as the comparison ratio returns current price.
3. Choose **DCF**. Annual cash of PHP 5 million at 10%, with zero growth,
   PHP 2 million net claims and 1 million shares gives PHP 48 per share.
4. Open the cash-flow helper. Check its invented figures and explicit zero
   adjustments. The 25% tax rate is illustrative.
5. Change an assumption and recalculate, or use **Sensitivity → Compare values**.
6. Save an analysis, reload the page and load its inputs. Confirm them again before
   calculating. Export JSON to inspect the inputs, sources and helper calculations.
7. Select a real company. Its financial template starts blank. Use **Edit company
   data** or **Update from reports** to add reviewed figures.

DEMO illustrates the calculation mechanics; it is not research on a listed company.

## Design choices

- FCFF and FCFE have separate cash-flow fields. FCFF uses WACC and subtracts net
  claims; FCFE uses the cost of equity without another debt subtraction.
- Money totals use full pesos. Rates are decimals in files and percentages in forms.
- Missing inputs stay missing. Imported proposals require review before applying.
- Formula inputs and units are fixed; labels, defaults and recommendations are editable.
- File replacement, backups and revision checks protect saved data.
- Offline browser tests block external requests.
