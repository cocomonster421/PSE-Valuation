"""One-time migration; existing brain files are never overwritten."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.server import read, write
from backend.catalog import initial_policy


def main():
    old_cache = ROOT.parent / "data/cache"
    rows = {}
    pointer = old_cache / "current_generation.json"
    if pointer.exists():
        generation = read(pointer)["generation_id"]
        data = read(old_cache / "generations" / generation / "fundamentals.json")
        rows = {r["ticker"]: r for r in data["rows"]}
    policy = initial_policy()
    count = 0
    for source in sorted((ROOT / "stock_data").glob("*.json")):
        stock = read(source)
        destination = ROOT / "brain" / f"{stock['ticker']}.toml"
        if destination.exists():
            continue
        row = rows.get(stock["ticker"], {})
        urls = [field.get("source_url") for field in stock["fields"].values()]
        company_id = next((parse_qs(urlsplit(url).query).get("cmpy_id", [None])[0] for url in urls if url and "cmpy_id=" in url), None)
        stock["pse_edge_url"] = f"https://edge.pse.com.ph/companyInformation/form.do?cmpy_id={company_id}" if company_id else "https://edge.pse.com.ph/companyDirectory/form.do"
        metrics = row.get("analyst_metrics") or {}
        rate = row.get("cost_of_equity")
        if rate is not None and not 0 < rate < 1:
            rate = None
        note = "Imported modeling assumption from the saved watcher analysis; review before use. Not company guidance."
        stock["models"] = {
            "dcf_fcff": {"growth": .03, "terminal_growth": .02, "discount_rate": "", "note": "Growth is an illustrative starting assumption. Enter WACC after reviewing capital structure."},
            "dcf_fcfe": {"growth": .03, "terminal_growth": .02, "discount_rate": rate if rate else "", "note": note},
            "ddm": {"discount_rate": rate if rate else "", "terminal_growth": .02, "note": note + " 2% dividend growth is illustrative; confirm recurring payout."},
            "pe": {"multiple": metrics.get("current_reference_pe") or metrics.get("peer_pe") or "", "note": note + " Saved earnings multiple is a reference, not a verified target."},
            "pb": {"multiple": metrics.get("peer_pb") or "", "note": note + " Saved peer P/B is a reference; review peer suitability."},
            "justified_pb": {"discount_rate": rate if rate else "", "terminal_growth": .02, "note": note},
            "residual_income": {"discount_rate": rate if rate else "", "terminal_growth": .02, "note": note},
            "dividend_cap": {"required_yield": "", "note": "Enter your required sustainable dividend yield."},
            "sotp": {"discount": .15, "note": "Illustrative holding-company discount; review attributable component values."},
            "nav": {"discount": 0, "note": "Undiscounted net asset value; enter reviewed assets and liabilities."},
            "rnav": {"discount": .15, "note": "Illustrative NAV discount; review attributable property values."},
        }
        for model in stock["models"].values():
            model["as_of"] = row.get("calculated_at") or row.get("valuation_as_of") or ""
        essential = ["price", "shares", "eps", "bvps", "dividend", "roe", "payout", "fcff_cash_flow", "fcfe_cash_flow", "net_debt", "asset_value", "liabilities"]
        stock["fields"] = {key: stock["fields"].get(key, {"value": None, "status": "missing", "as_of": "", "source_url": "", "note": "Not yet available; enter a reviewed figure."}) for key in essential} | {k:v for k,v in stock["fields"].items() if k not in essential}
        destination.parent.mkdir(parents=True, exist_ok=True)
        history = stock.get("history", [])
        history_path = destination.parent / "research" / f"{stock['ticker']}.json"
        history_path.parent.mkdir(exist_ok=True)
        history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
        write(destination, stock)
        count += 1
    print(f"Prepared {count} company brain files. Existing brains were preserved.")


if __name__ == "__main__":
    main()
