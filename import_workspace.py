"""One-time migration from the sibling watcher. Never needed to run the workbench."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Replace generated stock files; do not use after manual edits")
    args = parser.parse_args()
    profiles = read(SOURCE / "data/seeds/stock_profiles.json")
    cache = SOURCE / "data/cache"
    pointer = cache / "current_generation.json"
    if pointer.exists():
        cache = cache / "generations" / read(pointer)["generation_id"]
    fundamentals = {r["ticker"]: r for r in read(cache / "fundamentals.json")["rows"]}
    dashboard = {r["ticker"]: r for r in read(cache / "dashboard.json")["rows"]}
    output = ROOT / "stock_data"
    output.mkdir(exist_ok=True)
    for profile in profiles:
        ticker = profile["ticker"]
        destination = output / f"{ticker}.json"
        if destination.exists() and not args.refresh:
            continue  # Never replace manual edits.
        row = fundamentals.get(ticker, {})
        transparency = row.get("source_transparency") or dashboard.get(ticker, {}).get("source_transparency", {})
        fund_source = transparency.get("fundamentals", {})
        price_source = transparency.get("price", {})
        share = fund_source.get("share_count", {})
        fields = {}
        mapping = {"eps": "eps_ttm", "bvps": "bvps", "dividend": "dividend_per_share",
                   "roe": "roe", "payout": "payout_ratio"}
        for key, source_key in mapping.items():
            value = row.get(source_key)
            if value is not None:
                fields[key] = {"value": value / 100 if key in {"roe", "payout"} else value,
                    "source_url": fund_source.get("source_url"),
                    "as_of": fund_source.get("quarterly_report_date") or fund_source.get("annual_report_date"),
                    "fetched_at": fund_source.get("source_timestamp"), "period_end": None,
                    "status": "needs_review", "note": "Imported watcher metric. Date refers to latest report publication, not necessarily this metric's effective period. Confirm period, scope and recurring basis before use."}
        if share.get("value"):
            fields["shares"] = {"value": share["value"], "source_url": share.get("source_url"),
                "as_of": fund_source.get("source_timestamp"), "status": "needs_review",
                "note": "Outstanding common shares from saved stock-data snapshot; verify effective date."}
        fields["price"] = {"value": row.get("current_price"),
            "source_url": price_source.get("source_url"), "as_of": price_source.get("source_timestamp"),
            "status": "historical", "note": "Last saved delayed price. Offline; not a live quote."}
        facts_path = SOURCE / f"data/company_documents/{ticker}/financials/facts.json"
        history = []
        if facts_path.exists():
            for fact in read(facts_path).get("facts", []):
                if fact.get("metric") in {"revenue", "net_income_attributable_parent", "operating_cash_flow",
                    "cash_capex_ppe", "cash_and_cash_equivalents", "total_equity", "total_assets", "total_liabilities"}:
                    history.append({k: fact.get(k) for k in ("fact_id", "metric", "value", "currency", "unit",
                        "scope", "duration", "period_start", "period_end", "status", "source")})
        record = {"schema_version": 1, "ticker": ticker, "name": profile["company_name"],
            "industry": profile.get("subsector") or profile.get("sector") or "Unclassified — review company profile",
            "archetype": profile.get("valuation_archetype", "OPERATING_COMPANY"),
            "rationale": profile.get("rationale", "Review method suitability for this company."),
            "currency": "PHP", "fields": fields, "history": history,
            "benchmark": transparency.get("risk_free_rate", {}),
            "reports": {"annual_publication": row.get("latest_annual_report_date"),
                        "quarterly_publication": row.get("latest_quarterly_report_date")},
            "notes": "Imported local research. Candidate historical facts are not automatically used as valuation inputs."}
        destination.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Stock files available: {len(list(output.glob('*.json')))}")


if __name__ == "__main__":
    main()
