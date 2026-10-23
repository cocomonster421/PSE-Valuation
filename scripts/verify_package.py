"""Verify the source archive runs independently after extraction."""
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    archive = ROOT / "runtime/release/fundamental-valuation-workbench.zip"
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary)
        with ZipFile(archive) as package:
            for name in package.namelist():
                path = Path(name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe archive path")
                if any(part in {"runtime", ".env", "node_modules", "__pycache__"} for part in path.parts):
                    raise ValueError(f"Private/runtime path included: {name}")
            package.extractall(destination)
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=destination, check=True)
        subprocess.run([sys.executable, "scripts/replay_example.py"], cwd=destination, check=True, stdout=subprocess.DEVNULL)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        process = subprocess.Popen([sys.executable, "run.py", "--port", str(port)], cwd=destination,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            base = f"http://127.0.0.1:{port}"
            for attempt in range(50):
                if process.poll() is not None:
                    raise RuntimeError(process.communicate()[1].decode())
                try:
                    with urllib.request.urlopen(base + "/api/health", timeout=1) as response:
                        assert json.load(response)["status"] == "ok"
                    break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError("Packaged app failed to start")
            with urllib.request.urlopen(base, timeout=5) as response:
                assert b"Valuation Workbench" in response.read()
            with urllib.request.urlopen(base + "/api/stocks", timeout=5) as response:
                assert len(json.load(response)) == 62
            with urllib.request.urlopen(base + "/api/stocks/TEL", timeout=5) as response:
                company=json.load(response)["data"]
                assert company["name"] == "PLDT Inc."
                assert all(f['value'] is None for f in company['fields'].values())
                assert not company['history']
            with urllib.request.urlopen(base + "/api/stocks/DEMO", timeout=5) as response:
                assert json.load(response)['data']['fields']['eps']['value']==5
            with urllib.request.urlopen(base + "/api/examples/bdo", timeout=5) as response:
                example=json.load(response)
                assert example['reported']['bvps']==119.03
                assert example['financial_period_end']=='2025-12-31'
            occupied=subprocess.run([sys.executable,"run.py","--port",str(port)],cwd=destination,capture_output=True,text=True,timeout=10)
            assert "Cannot start on port" in occupied.stdout
            print("PASS: public archive, extracted tests/example, standalone run.py, UI, health, 61 blank companies and synthetic DEMO; no research histories")
        finally:
            process.terminate()
            process.communicate(timeout=10)


if __name__ == "__main__":
    main()
