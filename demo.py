"""Original synthetic data for an offline public demonstration, never a recommendation."""

def demo_stock():
    values={"price":50,"eps":5,"bvps":40,"dividend":2,"shares":1000000,
        "operating_profit":10000000,"depreciation":1000000,"other_noncash":0,
        "capital_spending":3000000,"additional_capex":0,"working_capital_increase":500000,
        "debt":4000000,"cash":2000000,"other_claims":0,"fcff_cash_flow":5000000,
        "net_debt":2000000,"receivables":3000000,"inventory":2000000,"payables":1000000,
        "previous_receivables":2500000,"previous_inventory":1800000,"previous_payables":800000,
        "other_working_capital_change":0}
    return {"ticker":"DEMO","name":"Example Consumer Company (synthetic)","industry":"Example consumer business",
        "archetype":"OPERATING_COMPANY","currency":"PHP","pse_edge_url":"",
        "rationale":"Synthetic example for learning the workflow. All numbers are invented.",
        "notes":"Not a real listed company or investment recommendation.",
        "fields":{k:{"value":v,"status":"reviewed","as_of":"2026-10-22" if k=="price" else "2025-12-31",
                     "period_end":"" if k=="price" else "2024-12-31" if k.startswith("previous_") else "2025-12-31",
                     "note":"Synthetic example: invented figures for offline demonstration."} for k,v in values.items()},
        "models":{"pe":{"multiple":12,"as_of":"2026-10-22","note":"Illustrative comparison P/E, not a market average."},
                  "dcf_fcff":{"growth":0,"terminal_growth":0,"discount_rate":.1,"as_of":"2026-10-22","note":"Synthetic constant-cash case: 5 million / 10% − 2 million net debt, divided by 1 million shares = PHP 48."}},
        "benchmark":{},"reports":{},"history":[]}
