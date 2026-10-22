# Public release and data ownership

Original code is MIT licensed. The license does not cover third-party reports,
PSE EDGE pages or other source material.

`python scripts/package_project.py` creates
`runtime/release/fundamental-valuation-workbench.zip` containing:

- Application code, tests, documentation, synthetic examples and a dated TEL research case.
- Company metadata and blank financial templates.
- One populated synthetic DEMO company; the sourced TEL case remains separate from the blank working templates.
- Empty report and scenario folders.

Downloaded reports, research histories, personal scenarios, extraction caches and
revision backups are excluded. The builder clears real-company financial figures
inside the archive without changing the working files. It can also rebuild a release
from a clean public checkout.

Review the ZIP before sharing. Extract it with the folder structure intact. Company
TOML files are tracked in Git, so committing personal edits directly can publish those
figures; use the sanitized archive when distributing a populated workspace.

The TEL case includes a small set of cited public facts and original analysis. It
does not reproduce report pages or grant a license to third-party source material.
