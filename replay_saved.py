"""Recalculate a saved/exported analysis offline: python scripts/replay_saved.py FILE.json."""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.engine import calculate, ENGINE_VERSION

if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("Usage: python scripts/replay_saved.py path/to/analysis.json")
    saved=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    original=saved["result"]
    recalculated=calculate(original["method"],original["inputs"])
    if not math.isclose(original["fair_value"],recalculated["fair_value"],rel_tol=1e-10,abs_tol=1e-8):
        raise SystemExit("Result differs from the saved analysis. Compare engine versions and input conventions.")
    print(json.dumps({"verified":True,"saved_engine":original.get("engine_version"),"current_engine":ENGINE_VERSION,"result":recalculated},indent=2,ensure_ascii=True))
