# Real report verification

Read-only check on 2026-10-22 using an already-downloaded URC 2025 annual report. No company brain was updated during verification.

- Official source: https://edge.pse.com.ph/downloadFile.do?file_id=1902846
- SHA-256: `9022a70ba19c30366362caea9bd96c413ff791ddbf3076ca7f4ff9c9597cb7be`
- PDF pages tested: 54, 56, 59 (printed pages 49, 51, 54).
- Selected annual period: 2025-12-31; units: full PHP.
- Cash, inventory/current and prior, depreciation and operating cash flow were extracted and checked against rendered pages 54 and 59.
- The concatenated operating-income columns on PDF page 56 were rejected, rather than parsed into an enormous number.
- Split acquisition labels and mixed receivable/payable totals remain manual: they cannot safely be treated as a clean FCFF input without reviewing the notes.
- Each proposal retains the file hash, PDF page, text line, source row, scale and period basis. Comparative balances carry the previous annual period and the current report period separately.

This establishes support for these specific rows/layouts, not universal PDF support. A full annual report contains repeated labels and different scopes; restrict PDF pages to the statements you want to review. A scan with no safe matches displays an unsupported-layout message. Downloaded PDFs and rendered source images are excluded from the public archive.

## Second real report: URC June 2026 quarterly filing

- Source: https://edge.pse.com.ph/downloadFile.do?file_id=1952924
- SHA-256: `de19f3123ab77ab3c308e8cd14c54cc0004c5bdb52568145ef3b0facacb19a0f`
- PDF pages 16, 18 and 21; units in thousands of pesos.
- Verified that the interim-period detector prevents six-month income/cash-flow data being offered as annual inputs.
- Verified that choosing full pesos instead of thousands raises a unit-conflict error.
- The PDF's split-digit columns are not safely readable by this parser. No values were proposed; the UI identifies the layout as unsupported and directs manual entry. This is a verified limitation, not a successful full-report import.
