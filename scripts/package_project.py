"""Create a small source archive using an explicit allowlist, never runtime data."""
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.brain import decode, encode
from backend.demo import demo_stock
from backend.catalog import initial_policy
DIRECTORIES = {"backend", "frontend", "brain", "policies", "tests", "scripts", "docs", "examples", ".github"}
ROOT_FILES = {"README.md", "requirements.txt", "requirements-lock.txt", "run.py", "Launch Workbench.cmd", "Setup Report Tools.cmd", ".gitignore", "IMPLEMENTATION_STATUS.md", "TODO.md", "LICENSE"}


def main():
    output = ROOT / "runtime/release"
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if relative.parts[0] not in DIRECTORIES and str(relative) not in ROOT_FILES:
            continue
        if "__pycache__" in relative.parts or path.is_dir():
            continue
        if relative.parts[:2]==("brain","research"):
            continue
        if relative.as_posix()=="brain/DEMO.toml":
            continue  # Always generate the canonical synthetic example once.
        if relative.parts[:2]==("docs","screenshots") and path.name not in {"portfolio-demo.png", "tel-overview.png", "tel-sensitivity.png", "tel-sources.png"}:
            continue
        if path.is_symlink() or path.suffix in {".pyc", ".db", ".pdf", ".log", ".env"}:
            raise ValueError(f"Unexpected file in release source: {relative}")
        if path.stat().st_size > 5_000_000:
            raise ValueError(f"Unexpected large file: {relative}")
        files.append(path)
    archive = output / "fundamental-valuation-workbench.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as package:
        for path in files:
            relative=path.relative_to(ROOT).as_posix()
            if relative.startswith("brain/") and path.suffix==".toml":
                original=decode(path)
                public={k:original[k] for k in ("ticker","name","industry","archetype","currency","pse_edge_url")}
                public.update(rationale="Saved company classification; review method suitability.",notes="Public blank template. Add your own reviewed data.",fields={k:{"value":None} for k in original["fields"]},models={},benchmark={},reports={})
                package.writestr(relative,encode(public))
            elif relative=="policies/catalog.json":
                package.writestr(relative,json.dumps(initial_policy(),indent=2,ensure_ascii=False))
            else:
                package.write(path, relative)
        package.writestr("brain/DEMO.toml",encode(demo_stock()))
        package.writestr("scenarios/.gitkeep", "")
        for brain in sorted((ROOT / "brain").glob("*.toml")):
            if brain.stem=="DEMO":
                continue
            package.writestr(f"reports/{brain.stem}/.gitkeep", "")
        package.writestr("reports/DEMO/.gitkeep","")
    manifest = {"archive": archive.name, "bytes": archive.stat().st_size,
                "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "files": sorted(ZipFile(archive).namelist())}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
