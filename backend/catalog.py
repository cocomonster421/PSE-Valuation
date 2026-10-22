"""Initial policy catalog; editable JSON is generated only when absent."""
FIELDS = {
    "fcff_cash_flow": ("Base-year FCFF", "PHP", "Annual free cash flow to the firm, before financing. Discount at WACC; do not substitute FCFE."),
    "fcfe_cash_flow": ("Base-year FCFE", "PHP", "Annual free cash flow to common equity, after financing and net borrowing. Discount at cost of equity; do not subtract debt again."),
    "price": ("Reference price", "PHP/share", "Last saved or manually entered price; not live."),
    "shares": ("Common shares outstanding", "shares", "Actual common share count, not millions. Consider dilution explicitly."),
    "cash_flow": ("Base-year cash flow", "PHP", "Annual total. FCFF: after-tax operating profit + depreciation − capex − change in working capital. FCFE also reflects net borrowing and interest; CFO less capex is not automatically either measure."),
    "growth": ("Annual forecast growth", "rate", "Growth used for each of the five explicit forecast years."),
    "discount_rate": ("Discount rate", "rate", "Use WACC for FCFF; cost of equity for FCFE, DDM and equity methods."),
    "terminal_growth": ("Terminal growth", "rate", "Long-run growth; must be below the discount rate. Maximum 5%."),
    "net_debt": ("Net debt and other claims", "PHP", "Debt less excess cash, plus other senior/non-common claims as appropriate. Negative means net cash."),
    "dividend": ("Annual recurring dividend", "PHP/share", "Exclude special dividends; assess payout sustainability."),
    "eps": ("Normalized annual EPS", "PHP/share", "Common earnings per share; use sustainable earnings and document normalization."),
    "bvps": ("Common book value per share", "PHP/share", "Equity attributable to common shareholders divided by common shares."),
    "multiple": ("Selected valuation multiple", "times", "Use a documented history or peer basis; not an automatic market average."),
    "roe": ("Sustainable return on equity", "rate", "Forward sustainable common ROE, not necessarily the latest reported ROE."),
    "payout": ("Earnings payout ratio", "rate", "Share of earnings distributed; retained earnings grow book value."),
    "asset_value": ("Attributable asset/component value", "PHP", "Reviewed sum of attributable component values; attach component calculations in notes."),
    "liabilities": ("Unaccounted liabilities/claims", "PHP", "Only claims not already deducted within component values."),
    "discount": ("NAV / holding company discount", "rate", "Explicit discount applied to net attributable equity value."),
    "affo_per_share": ("Annual AFFO per share", "PHP/share", "Reviewed recurring adjusted funds from operations per common share."),
    "required_yield": ("Required dividend yield", "rate", "Required sustainable yield, including relevant risk premium."),
    "noi": ("Annual net operating income", "PHP", "Stabilized attributable property NOI before financing."),
    "cap_rate": ("Property capitalization rate", "rate", "Market-supported property capitalization rate."),
    "adjusted_net_worth": ("Adjusted net worth", "PHP", "Reviewed insurance adjusted equity value."),
    "in_force_value": ("Value of in-force business", "PHP", "Present value from reviewed actuarial assumptions; not total premiums."),
}

METHODS = {
    "dcf_fcff": ("DCF · enterprise cash flow", ["cash_flow", "growth", "discount_rate", "terminal_growth", "net_debt", "shares"], "Five-year FCFF discounted at WACC, then bridge enterprise value to common equity."),
    "dcf_fcfe": ("DCF · equity cash flow", ["cash_flow", "growth", "discount_rate", "terminal_growth", "shares"], "Five-year FCFE discounted at cost of equity. No further debt subtraction."),
    "ddm": ("Dividend discount model", ["dividend", "discount_rate", "terminal_growth"], "Constant-growth model for sustainable recurring dividends."),
    "pe": ("Normalized P/E", ["eps", "multiple"], "Sustainable annual EPS multiplied by a justified earnings multiple."),
    "pb": ("Relative P/B", ["bvps", "multiple"], "Common book value per share multiplied by a supported P/B multiple."),
    "justified_pb": ("Justified P/B", ["bvps", "roe", "discount_rate", "terminal_growth"], "Connects sustainable ROE, growth and cost of equity."),
    "residual_income": ("Residual income", ["bvps", "roe", "payout", "discount_rate", "terminal_growth"], "Book value plus five years of excess returns and continuing residual income."),
    "sotp": ("Sum of the parts", ["asset_value", "liabilities", "discount", "shares"], "Attributable component equity values less remaining claims and holding discount."),
    "rnav": ("Revalued net asset value", ["asset_value", "liabilities", "discount", "shares"], "Reviewed property/development values less unaccounted claims."),
    "nav": ("Net asset value", ["asset_value", "liabilities", "discount", "shares"], "Reviewed net attributable asset value per common share."),
    "affo": ("P/AFFO", ["affo_per_share", "multiple"], "Recurring AFFO per share multiplied by a selected valuation multiple."),
    "dividend_cap": ("Dividend capitalization", ["dividend", "required_yield"], "Sustainable annual distribution capitalized at a required yield."),
    "cap_rate": ("Property capitalization", ["noi", "cap_rate", "net_debt", "shares"], "Stabilized property NOI capitalized into asset value, less net claims."),
    "embedded_value": ("Insurance embedded value", ["adjusted_net_worth", "in_force_value", "shares"], "Adjusted net worth plus reviewed value of in-force business."),
}


def initial_policy():
    from backend.explanations import FIELDS as EXPLAINED_FIELDS, METHODS as EXPLAINED_METHODS, RATE_HELP
    fields = {k: dict(label=v[0], unit=v[1], help=v[2]) for k, v in FIELDS.items()}
    for key, (label, help_text) in EXPLAINED_FIELDS.items():
        fields[key].update(label=label, help=help_text)
    extra = {
        "operating_profit":("Annual operating profit","Income statement: profit/income from operations, before financing and tax."),
        "depreciation":("Annual depreciation and amortization","Cash-flow statement: non-cash depreciation and amortization added back to profit."),
        "capital_spending":("Annual equipment and property spending","Cash-flow statement investing activities: purchases of property, plant and equipment. Enter spending as positive."),
        "working_capital_increase":("Annual increase in operating working capital","Increase in operating receivables and inventory minus increase in operating payables. Exclude cash and financing debt. A decrease is negative."),
        "operating_cash_flow":("Cash from operating activities","Cash-flow statement: net cash generated from operating activities. This alone is not business free cash flow."),
        "debt":("Interest-bearing debt","Borrowing notes: current plus long-term interest-bearing borrowings, including relevant leases. Do not use total liabilities."),
        "cash":("Cash available to offset debt","Balance sheet cash and cash equivalents, adjusted to exclude restricted cash or cash needed for operations when appropriate.")}
    for key,(label,help_text) in extra.items():
        fields[key]={"label":label,"unit":"PHP","help":help_text}
    for key,label,help_text in [
        ("additional_capex","Other capital investment","Include capitalized software, intangibles and other investment not already in equipment/property spending. Enter positive spending, or an explicitly reviewed zero."),
        ("other_claims","Other claims ahead of common shareholders","Include preferred equity, non-controlling interests when cash flows consolidate subsidiaries, and other claims not already in debt. Review values and avoid double counting. Enter zero only after checking."),
        ("other_working_capital_change","Other operating working-capital increase","Net change in other operating assets minus other operating liabilities, excluding cash and financing debt. Adjust acquisitions, FX and reclassifications. Zero means reviewed and not material."),
        ("other_noncash","Other non-cash operating adjustments","Non-cash operating charges to add back, net of non-cash gains to subtract, beyond depreciation. Exclude financing items. Enter zero only after review.")]:
        fields[key]={"label":label,"unit":"PHP","help":help_text}
    for key,label in {"receivables":"Operating trade receivables","inventory":"Inventory","payables":"Operating trade payables"}.items():
        for prefix,period in [("","Current year"),("previous_","Previous year")]:
            fields[prefix+key]={"label":f"{period}: {label}","unit":"PHP","help":"Use comparable annual balance-sheet closing balances. Exclude financing items. Include other operating working-capital movements separately when material."}
    methods={k:dict(name=v[0],fields=v[1],description=EXPLAINED_METHODS.get(k,v[2])) for k,v in METHODS.items()}
    return {"schema_version": 1,
        "fields": fields,
        "methods": methods,
        "rate_help": RATE_HELP,
        "recommendations": {
            "TELECOM": ["dcf_fcff", "ddm", "pe"],
            "UTILITY_INFRASTRUCTURE": ["dcf_fcff", "ddm", "pe"],
            "OPERATING_COMPANY": ["dcf_fcff", "dcf_fcfe", "pe"],
            "BANK": ["justified_pb", "residual_income", "pb", "pe", "ddm"],
            "CONGLOMERATE": ["sotp", "nav", "pe"],
            "PROPERTY_DEVELOPER": ["rnav", "dcf_fcff", "pe"],
            "REIT": ["nav", "affo", "dividend_cap", "cap_rate"],
            "CYCLICAL_COMMODITY": ["pe", "dcf_fcff"],
            "INSURANCE": ["embedded_value", "pb", "residual_income"],
            "OTHER_SPECIALIZED": ["pe", "nav"]},
        "defaults": {"growth": .03, "terminal_growth": .02, "discount": .15},
        "default_note": "Illustrative modeling assumptions, not company forecasts. Review and confirm before calculating."}
