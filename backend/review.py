"""Explain input provenance and readiness without pretending to verify financial facts."""
from datetime import date

ASSUMPTIONS = {"growth", "discount_rate", "terminal_growth", "multiple", "discount",
               "required_yield", "cap_rate", "roe", "payout"}
ANNUAL_FIELDS = {"eps", "dividend", "cash_flow", "fcff_cash_flow", "fcfe_cash_flow",
                 "affo_per_share", "noi", "operating_profit", "depreciation",
                 "capital_spending", "operating_cash_flow", "working_capital_increase",
                 "other_noncash", "other_investment"}
PERIOD_TYPES = {"unknown", "annual", "ttm", "quarter", "ytd", "point_in_time"}


def period_issues(key, source):
    if key not in ANNUAL_FIELDS:
        return []
    kind=source.get("period_type", "unknown")
    if kind not in {"annual", "ttm"}:
        return [f"{key}: annual or trailing-12-month input required; saved period type is {kind}. Do not automatically multiply a quarter or YTD figure."]
    return []


def documented(evidence, today):
    try:
        dated = date.fromisoformat(evidence.get("as_of", "")[:10])
        return (0 <= (today - dated).days <= 365
                and evidence.get("evidence_status") == "documented"
                and bool(evidence.get("note", "").strip()))
    except (ValueError, TypeError):
        return False


def review_inputs(stock, policy, method, inputs, today=None, derivations=None):
    today=today or date.today()
    missing=[]; issues=[]; audit=[]; periods=set(); unsupported=[]; data_issues=[]
    model=stock.get("models",{}).get(method,{})
    reports=stock.get("reports", {})
    report_status=reports.get("review_status", "unreviewed")
    if report_status not in {"reviewed", "reconciled"}:
        data_issues.append("Reporting: " + ("unresolved disclosure or revision; reconcile affected figures before relying on this valuation" if report_status == "unresolved" else "disclosure review not recorded"))
    elif not reports.get("review_note", "").strip() or not reports.get("reviewed_on"):
        data_issues.append("Reporting: review needs a date and explanation")
    else:
        try:
            age=(today-date.fromisoformat(reports["reviewed_on"][:10])).days
            if age < 0 or age > 90:
                data_issues.append("Reporting: review date is future-dated or more than 90 days old")
        except (ValueError, TypeError):
            data_issues.append("Reporting: invalid review date")
    if report_status == "unresolved" and reports.get("review_note"):
        data_issues.append("Reporting note: " + reports["review_note"])
    if report_status in {"unreviewed", "unresolved"} and reports.get("invalidation_reason"):
        data_issues.append("Reporting: " + reports["invalidation_reason"])
    if report_status == 'unresolved':
        for finding in reports.get('disclosure_findings',{}).values():
            data_issues.append(f"{finding['category']} — {finding['source_file']}, page {finding['source_page']}: {finding['excerpt']} (keyword match; review context)")
    for key in policy["methods"][method]["fields"]+["price"]:
        value=inputs.get(key)
        if value is None:
            if key!="price": missing.append(policy["fields"][key]["label"])
            if key in ASSUMPTIONS: unsupported.append(key)
            continue
        baseline_key=("fcff_cash_flow" if method=="dcf_fcff" else "fcfe_cash_flow") if key=="cash_flow" else key
        source=stock.get("fields",{}).get(baseline_key,{})
        derived=next((d for d in reversed(derivations or []) if isinstance(d,dict) and d.get("output_field")==key and d.get("value")==value),None)
        if derived:
            kind="Calculated from helper inputs"; evidence=derived
            issues.append(f"{key}: review the helper's inputs and source periods")
            helper_periods=set()
            for helper_key, helper_value in derived.get("inputs", {}).items():
                if helper_key not in ANNUAL_FIELDS or helper_value is None:
                    continue
                helper_source=derived.get("sources", {}).get(helper_key, {})
                if helper_source.get("value") != helper_value:
                    data_issues.append(f"{helper_key}: helper input differs from its saved source; confirm annual period and basis")
                else:
                    data_issues.extend(period_issues(helper_key, helper_source))
                    if helper_source.get("period_end"):
                        helper_periods.add(helper_source['period_end'][:10])
            if len(helper_periods)>1:
                data_issues.append("Cash-flow helper mixes annual reporting periods: "+", ".join(sorted(helper_periods)))
        elif key in model and model[key]==value:
            kind="Company assumption"; evidence={k:model.get(k) for k in ("as_of","note","evidence_status")}
        elif source.get("value")==value:
            kind="Saved company figure"; evidence=dict(source)
            data_issues.extend(period_issues(key, source))
            if source.get("status")!="reviewed": issues.append(f"{key}: saved figure needs review")
            period=source.get("period_end")
            if period and key!="price": periods.add(period[:10])
            if key!="price" and not period: issues.append(f"{key}: financial period is not recorded")
            expected=policy["fields"][key]["unit"]
            if source.get("unit") and source["unit"]!=expected: issues.append(f"{key}: source unit differs from input unit {expected}")
        elif policy.get("defaults",{}).get(key)==value:
            kind="Illustrative policy assumption"; evidence={"note":policy.get("default_note","Review this assumption")}
        else:
            kind="Manual or calculated input"; evidence={"note":"Changed from saved baseline; explain the basis in notes or the calculation trail."}
        if kind in {"Company assumption","Illustrative policy assumption"}: issues.append(f"{key}: assumption, not a reported fact")
        if key in ASSUMPTIONS:
            if not documented(evidence, today):
                unsupported.append(key)
                issues.append(f"{policy['fields'][key]['label']}: illustrative until saved with an explicit basis, review date and documented status (within 365 days)")
        else:
            if kind != "Saved company figure":
                data_issues.append(f"{key}: manual or derived figure needs source reconciliation")
            elif source.get("status") != "reviewed" or not (source.get("source_url") or source.get("note")) or not (source.get("as_of") or source.get("period_end")):
                data_issues.append(f"{key}: source evidence or review is incomplete")
        dated=evidence.get("period_end") or evidence.get("as_of")
        if dated:
            try:
                age=(today-date.fromisoformat(dated[:10])).days
                limit=policy.get("freshness_days",{}).get("price" if key=="price" else "financials",7 if key=="price" else 450)
                if age>limit: issues.append(f"{key}: saved date is {age} days old (review threshold {limit})")
                if age<0: issues.append(f"{key}: saved date is in the future")
            except (ValueError,TypeError): issues.append(f"{key}: invalid source date")
        audit.append({"field":key,"label":policy["fields"][key]["label"],"value":value,"unit":policy["fields"][key]["unit"],"kind":kind,"evidence":evidence})
    if len(periods)>1: issues.append("Inputs mix financial periods: "+", ".join(sorted(periods))+". Confirm they are comparable.")
    issues = list(dict.fromkeys(data_issues + issues))
    # Documentation is not a certification; warnings survive input confirmation.
    data_warnings = data_issues or [s for s in issues if any(term in s for term in
        ("days old", "future", "invalid source date", "unit differs", "mix financial", "financial period", "saved figure needs review"))]
    return {"status":"Missing data" if missing else "Needs review" if issues else "Ready for input confirmation",
            "data_status":"Missing data" if missing else "Needs review" if data_warnings else "Reviewed inputs",
            "assumption_status":"Illustrative scenario" if unsupported else "Documented assumptions (not independently verified)",
            "unsupported_assumptions":unsupported, "reporting_status":report_status,
            "missing":missing,"issues":issues,"fields":audit,"checked_on":today.isoformat(),
            "note":"Confirmation acknowledges inputs; it does not clear warnings. Offline checks cannot discover disclosures absent from local records. Documentation does not certify accuracy or forecast quality."}
