# Release audit — 22 October 2026

The release audit covers the public repository, including its documentation,
synthetic examples, release builder and local application.

## Acceptance checks

- Correct repository structure, with backend, frontend, company data and policies.
- No private reports or research snapshots in the published tree.
- Setup and UI terminology agree with the README.
- Public-checkout browser tests use explicit synthetic fixtures.
- Rebuilding a public release produces one DEMO file and one DEMO report placeholder.
- Basic and advanced saved analyses reopen with fresh confirmation.
- DCF helper evidence survives re-saving; manual output changes invalidate its evidence.
- Calculations agree with independent examples and formula regression tests.
- Internal documentation links resolve.

See [verification commands and limits](VERIFICATION.md). The completed change list
is in [FIX_CHECKLIST.md](FIX_CHECKLIST.md). Runtime test outputs are generated locally
and excluded from the repository.

Live PSE availability, arbitrary PDF layouts and installation on a separate physical
machine are not covered by this audit. Imported financial figures and valuation
assumptions still require review.

## Results

- 45 automated tests passed, including release rebuild and cancelled-response regressions.
- Public-checkout and extracted-package browser workflows passed.
- Independent package startup, health checks, example replay and occupied-port handling passed.
- Internal Markdown links resolve; current source contains no embedded credentials found by the release scan.
- Documentation was updated to match the public templates and current UI labels.

Browser reloads can cancel pending requests. The server now closes those connections
without attempting a second error response. The release builder avoids duplicate DEMO
entries, and browser checks use synthetic fixtures rather than private financial data.
