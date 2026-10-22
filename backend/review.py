"""Explain input provenance and readiness without pretending to verify financial facts."""
from datetime import date


def review_inputs(stock, policy, method, inputs, today=None, derivations=None):
    today=today or date.today()
    missing=[]; issues=[]; audit=[]; periods=set()
    model=stock.get("models",{}).get(method,{})
    for key in policy["methods"][method]["fields"]+["price"]:
        value=inputs.get(key)
        if value is None:
            if key!="price": missing.append(policy["fields"][key]["label"])
            continue
        baseline_key=("fcff_cash_flow" if method=="dcf_fcff" else "fcfe_cash_flow") if key=="cash_flow" else key
        source=stock.get("fields",{}).get(baseline_key,{})
        derived=next((d for d in reversed(derivations or []) if isinstance(d,dict) and d.get("output_field")==key and d.get("value")==value),None)
        if derived:
            kind="Calculated from helper inputs"; evidence=derived
            issues.append(f"{key}: review the helper's inputs and source periods")
        elif key in model and model[key]==value:
            kind="Company assumption"; evidence={"as_of":model.get("as_of"),"note":model.get("note")}
        elif source.get("value")==value:
            kind="Saved company figure"; evidence=dict(source)
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
    return {"status":"Missing data" if missing else "Needs review" if issues else "Ready for input confirmation", "missing":missing,"issues":list(dict.fromkeys(issues)),"fields":audit,"checked_on":today.isoformat(),"note":"Readiness checks do not certify source accuracy. Prices use a 7-day review threshold by default; financials use 450 days. New disclosures may make data stale sooner."}
