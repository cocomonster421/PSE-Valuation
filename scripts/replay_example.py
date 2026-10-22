"""Run a documented valuation without the web UI or any external data."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engine import calculate, compare

example = json.loads((ROOT / "examples/tel_ddm.json").read_text(encoding="utf-8"))
result = calculate(example["method"], example["inputs"])
assert math.isclose(result["fair_value"], example["expected_fair_value"])
print(json.dumps({"purpose": example["purpose"], "result": result,
                  "sensitivity": compare(example["method"], example["inputs"], **example["sensitivity"])}, indent=2))
