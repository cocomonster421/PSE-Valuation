"""Pure, offline valuation functions. Monetary totals use PHP, rates use decimals."""
from __future__ import annotations

import math


ENGINE_VERSION = "1.1.1"


def readable(value):
    return f"{value:,.8f}".rstrip("0").rstrip(".")


def compare(method, inputs, field, low, high):
    from backend.catalog import METHODS
    if method not in METHODS or field not in METHODS[method][1]:
        raise ValueError("Choose a supported assumption for this method")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (low, high)) or low >= high:
        raise ValueError("Sensitivity inputs must be finite and lower must be below higher")
    base = calculate(method, inputs)
    return {"field": field, "cases": [
        {"label": "Lower input", "input": low, "result": calculate(method, {**inputs, field: low})},
        {"label": "Base case", "input": inputs[field], "result": base},
        {"label": "Higher input", "input": high, "result": calculate(method, {**inputs, field: high})}]}


def calculate(method: str, inputs: dict) -> dict:
    if not isinstance(method, str) or not isinstance(inputs, dict):
        raise ValueError("Method must be a string and inputs must be an object")
    def number(key, *, positive=False):
        value = inputs.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key}: enter a finite number")
        if positive and value <= 0:
            raise ValueError(f"{key}: must be greater than zero")
        return float(value)

    steps = []
    warnings = []
    if method in {"dcf_fcff", "dcf_fcfe", "ddm", "residual_income", "justified_pb"}:
        rate = number("discount_rate", positive=True)
        terminal = number("terminal_growth")
        if not -1 < terminal <= 0.05:
            raise ValueError("Terminal growth must be greater than -100% and no more than 5%")
        if terminal >= rate:
            raise ValueError("Terminal growth must be below the discount rate")
    if method in {"dcf_fcff", "dcf_fcfe"}:
        cash_flow = number("cash_flow")
        growth = number("growth")
        if not -1 < growth <= 1:
            raise ValueError("Forecast growth must be greater than -100% and no more than 100%")
        shares = number("shares", positive=True)
        present = 0.0
        for year in range(1, 6):
            forecast = cash_flow * (1 + growth) ** year
            pv = forecast / (1 + rate) ** year
            present += pv
            cash_label = "Annual cash available to the business" if method == "dcf_fcff" else "Annual cash available to shareholders"
            steps.append({"label": f"Year {year}: {cash_label} ({readable(cash_flow)}) × (1 + Expected yearly cash growth ({readable(growth)}))^{year} ÷ (1 + Required yearly return ({readable(rate)}))^{year}", "forecast": forecast, "discount_factor":(1+rate)**year,"present_value": pv})
        terminal_value = forecast * (1 + terminal) / (rate - terminal)
        terminal_pv = terminal_value / (1 + rate) ** 5
        total = present + terminal_pv
        equity = total - number("net_debt") if method == "dcf_fcff" else total
        value = equity / shares
        steps += [{"label": f"Continuing value: {readable(forecast)} × (1 + Growth after year 5 ({readable(terminal)})) ÷ (Required yearly return ({readable(rate)}) − Growth after year 5 ({readable(terminal)}))", "value": terminal_value},
                  {"label": f"Discount continuing value: {readable(terminal_value)} ÷ (1 + Required yearly return ({readable(rate)}))^5", "value": terminal_pv},
                  {"label": "Sum of discounted forecast years and continuing value", "value": total},
                  {"label": f"Equity value: {readable(total)}"+(f" − Debt minus available cash ({readable(inputs['net_debt'])})" if method=="dcf_fcff" else " (no further debt subtraction)"), "value": equity},
                  {"label": f"Value per share: {readable(equity)} ÷ Number of common shares ({readable(shares)})", "value": value}]
        if cash_flow <= 0:
            warnings.append("A constant-growth forecast of nonpositive cash flow does not model a recovery; review the method.")
        if total > 0 and terminal_pv / total > 0.75:
            warnings.append("More than 75% of the discounted value comes from the terminal period.")
    elif method == "ddm":
        dividend = number("dividend", positive=True)
        value = dividend * (1 + terminal) / (rate - terminal)
        steps.append({"label": f"Annual dividend per share ({readable(dividend)}) × (1 + Long-run dividend growth ({readable(terminal)})) ÷ (Required yearly return ({readable(rate)}) − Long-run dividend growth ({readable(terminal)}))", "value": value})
        warnings.append("Use recurring, sustainable dividends; exclude special distributions.")
    elif method in {"pe", "pb", "affo"}:
        metric = {"pe": "eps", "pb": "bvps", "affo": "affo_per_share"}[method]
        value = number(metric, positive=True) * number("multiple", positive=True)
        metric_label={"eps":"Earnings per share (EPS)","bvps":"Book value per share","affo_per_share":"Annual AFFO per share"}[metric]
        ratio_label={"pe":"Comparison P/E","pb":"Comparison P/B","affo":"Comparison price / cash earnings"}[method]
        steps.append({"label": f"{metric_label} ({readable(inputs[metric])}) × {ratio_label} ({readable(inputs['multiple'])})", "value": value})
    elif method == "justified_pb":
        roe = number("roe")
        if roe>0 and not 0 <= terminal/roe <= 1:
            warnings.append("Long-run growth implies a retention ratio outside 0–100% at this ROE. Explain external financing or use another model.")
        multiple = (roe - terminal) / (rate - terminal)
        if multiple <= 0:
            raise ValueError("Sustainable ROE must exceed terminal growth for justified P/B")
        value = number("bvps", positive=True) * multiple
        steps.append({"label": "Justified P/B = (ROE − growth) / (cost of equity − growth)", "value": multiple})
    elif method == "residual_income":
        book = number("bvps", positive=True)
        roe = number("roe")
        payout = number("payout")
        if not 0 <= payout <= 1:
            raise ValueError("Payout must be between 0% and 100%")
        if roe>0:
            terminal_payout=1-terminal/roe
            warnings.append(f"Year 1–5 book growth = ROE × (1 − payout) = {roe*(1-payout):.2%}. Long-run growth implies a terminal payout of {terminal_payout:.2%}; review the change in payout after year 5.")
            if not 0 <= terminal_payout <= 1:
                warnings.append("Terminal payout is outside 0–100%; this requires external financing or a different terminal model.")
        else:
            warnings.append("Nonpositive sustainable ROE makes the perpetual residual-income assumptions weak; review the terminal model.")
        value = book
        for year in range(1, 6):
            residual = book * (roe - rate)
            pv = residual / (1 + rate) ** year
            value += pv
            steps.append({"label": f"Year {year} residual income per share", "forecast": residual, "present_value": pv})
            book += book * roe * (1 - payout)
        terminal_pv = book * (roe - rate) / (rate - terminal) / (1 + rate) ** 5
        value += terminal_pv
        steps.append({"label": "Present value of continuing residual income", "value": terminal_pv})
        warnings.append("Assumes clean-surplus accounting and a persistent ROE; terminal growth applies to continuing residual income.")
    elif method in {"nav", "sotp", "rnav"}:
        discount = number("discount")
        if not 0 <= discount < 1:
            raise ValueError("NAV discount must be between 0% and less than 100%")
        equity = number("asset_value") - number("liabilities")
        value = equity * (1 - discount) / number("shares", positive=True)
        asset_label="Value of owned assets and businesses" if method=="sotp" else "Reviewed gross asset value"
        claim_label="Remaining parent-company debt and claims" if method=="sotp" else "Liabilities and other claims against those assets"
        steps.append({"label": f"({asset_label} − {claim_label}) × (1 − Discount to asset-based value) ÷ Number of common shares", "value": value})
        warnings.append("Use attributable component equity values; subtract only remaining parent claims." if method=="sotp" else "Use gross assets and all corresponding liabilities/claims with the same ownership scope; do not enter already-net equity as gross assets.")
    elif method == "dividend_cap":
        value = number("dividend", positive=True) / number("required_yield", positive=True)
        steps.append({"label": "Annual recurring dividend / required yield", "value": value})
    elif method == "cap_rate":
        property_value = number("noi", positive=True) / number("cap_rate", positive=True)
        value = (property_value - number("net_debt")) / number("shares", positive=True)
        steps.append({"label": "Property value = NOI / capitalization rate", "value": property_value})
    elif method == "embedded_value":
        value = (number("adjusted_net_worth") + number("in_force_value")) / number("shares", positive=True)
        steps.append({"label": "(Adjusted net worth + present value of in-force business) / shares", "value": value})
    else:
        raise ValueError("Unknown valuation method")
    if not math.isfinite(value):
        raise ValueError("Calculation overflow: review the inputs")
    if value <= 0:
        warnings.append("The modeled equity value is nonpositive; this is not a price target.")
    price = inputs.get("price")
    gap = None
    if price is not None:
        price = number("price", positive=True)
        gap = value / price - 1
    from backend.explanations import FIELDS
    label=lambda key: FIELDS.get(key,(key,""))[0]
    formulas={
        "dcf_fcfe":"Discount each year's Annual cash available to shareholders at Required yearly return. Add continuing shareholder cash value discounted from year 5, then divide by Number of common shares. No further debt subtraction.",
        "affo":"Annual AFFO per share × Comparison price / cash earnings",
        "justified_pb":"Book value per share × (Sustainable return on equity − Long-run growth) ÷ (Required yearly return − Long-run growth)",
        "residual_income":"Book value per share + discounted yearly residual income. Each year's residual income = beginning book value × (Sustainable return on equity − Required yearly return). Grow book by ROE × (1 − Earnings payout ratio). Continuing residual income = year-5 closing book × (ROE − required return) ÷ (required return − Long-run growth), discounted five years.",
        "dividend_cap":"Annual dividend per share ÷ Required dividend yield",
        "cap_rate":"(Annual net operating income ÷ Property capitalization rate − Debt minus available cash) ÷ Number of common shares",
        "embedded_value":"(Adjusted net worth + Value of in-force business) ÷ Number of common shares",
        "pe":"Earnings per share (EPS) × Comparison P/E",
        "pb":"Book value per share × Comparison P/B",
        "ddm":"Annual dividend per share × (1 + Long-run dividend growth) ÷ (Required yearly return − Long-run dividend growth)",
        "dcf_fcff":"For each year n = 1 to 5: Annual cash available to the business × (1 + Expected yearly cash growth)^n ÷ (1 + Required yearly return)^n. Add all five years. Continuing value = Year-5 cash × (1 + Growth after year 5) ÷ (Required yearly return − Growth after year 5); divide it by (1 + Required yearly return)^5. Add it to the five years, subtract Debt minus available cash, then divide by Number of common shares.",
        "sotp":"(Value of owned assets and businesses − Remaining parent-company debt and claims) × (1 − Discount to asset-based value) ÷ Number of common shares",
    }
    formula=formulas.get(method)
    if method in {"nav","rnav"}: formula="(Reviewed gross asset value − Liabilities and other claims against those assets) × (1 − Discount to asset-based value) ÷ Number of common shares"
    ratios={}
    if price and inputs.get("eps",0)>0:
        ratios["current_pe"]=price/inputs["eps"]
    if price and inputs.get("bvps",0)>0:
        ratios["current_pb"]=price/inputs["bvps"]
    return {"engine_version": ENGINE_VERSION, "method": method, "fair_value": value, "formula":formula, "current_ratios":ratios,
            "gap": gap, "steps": steps, "warnings": warnings, "inputs": dict(inputs)}
