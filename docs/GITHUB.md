# Sharing the project

The repository is available at https://github.com/cocomonster421/PSE-Valuation.
GitHub hosts its source; the Python application runs locally.

To prepare a clean source archive:

```sh
python scripts/package_project.py
python scripts/verify_package.py
```

Extract `runtime/release/fundamental-valuation-workbench.zip` into an empty folder.
Keep `backend/`, `frontend/`, `brain/`, `policies/` and the other folders intact.
Use Git or GitHub Desktop to commit that directory's contents. Do not flatten files
from different folders into the repository root.

The release includes the MIT license, blank real-company templates and synthetic
examples. Reports, personal scenarios and revision backups are excluded. See
[release rules](PUBLIC_RELEASE.md) before sharing a populated workspace.
