"""Explain input provenance and readiness without pretending to verify financial facts."""
from datetime import date
import math
from backend.cash_flow import reconcile_cash_flow
from backend.components import reconcile_components

ASSUMPTIONS = {"growth", "discount_rate", "terminal_growth", "multiple", "discount",
               "required_yield", "cap_rate", "roe", "payout"}
ANNUAL_FIELDS = {"eps", "dividend", "cash_flow", "fcff_cash_flow", "fcfe_cash_flow",
                 "affo_per_share", "noi", "operating_profit", "depreciation",
                 "capital_spending", "operating_cash_flow", "working_capital_increase",
                 "other_noncash", "other_investment"}
PERIOD_TYPES = {"unknown", "annual", "ttm", "quarter", "ytd", "point_in_time"}


def same_period_conflict(key, previous, proposed):
    """Flag changed reported figures, without inferring which source is correct."""
    if key == 'price' or previous.get('value') is None or proposed.get('value') is None:
        return None
    old_end=previous.get('period_end')
    new_end=proposed.get('period_end')
    if not old_end or old_end != new_end:
        return None
    if math.isclose(previous['value'],proposed['value'],rel_tol=1e-10,abs_tol=1e-8):
        return None
    evidence_keys=('value','period_end','period_type','as_of','source_url','source_file','source_hash','source_page','note','unit','scale')
    return dict(field=key,period_end=old_end,
                previous={k:previous[k] for k in evidence_keys if k in previous},
                proposed={k:proposed[k] for k in evidence_keys if k in proposed},
                note='Different values for the same period end; reconcile duration, units, scope and revisions. Neither source is automatically preferred.')


def period_issues(key, source):
    if key not in ANNUAL_FIELDS:
        return []
    kind=source.get("period_type", "unknown")
    if kind not in {"annual", "ttm"}:
        return [f"{key}: annual or trailing-12-month input required; saved period type is {kind}. Do not automatically multiply a quarter or YTD figure."]
    return []



def eps_bridge_issues(source, today):
    if source.get("period_type") != "ttm":
        return []
    bridge = source.get("eps_bridge")
    if not isinstance(bridge, dict):
        return ["eps: trailing-year component evidence is missing; reconcile earnings and weighted-average share bases"]
    issues = []
    try:
        values = [bridge[k] for k in ("annual_eps", "current_ytd_eps", "prior_ytd_eps")]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError("components must be finite numbers")
        if not math.isclose(values[0]+values[1]-values[2], source["value"], rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError("component arithmetic differs from saved EPS")
        annual = date.fromisoformat(bridge["annual_end"])
        current = date.fromisoformat(bridge["current_ytd_end"])
        prior = date.fromisoformat(bridge["prior_ytd_end"])
        if not ((annual.month, annual.day)==(12,31) and current.year==annual.year+1
                and (current.month,current.day) in {(3,31),(6,30),(9,30)}
                and prior==current.replace(year=current.year-1)
                and source.get("period_end")==current.isoformat()):
            raise ValueError("component periods do not form the supported calendar-year bridge")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        issues.append(f"eps: trailing-year bridge cannot be reproduced: {error}")
    try:
        age = (today-date.fromisoformat(bridge.get("reviewed_on", ""))).days
        reconciled = (bridge.get("review_status")=="reconciled" and 0<=age<=365
                      and bool(bridge.get("review_note", "").strip()))
    except (TypeError, ValueError, AttributeError):
        reconciled = False
    if not reconciled:
        issues.append("eps: annual + current YTD − prior YTD is provisional until revised earnings, corporate actions and weighted-average share bases are reconciled with a dated explanation")
    return issues


def documented(evidence, today):
    try:
        dated = date.fromisoformat(evidence.get("as_of", "")[:10])
        return (0 <= (today - dated).days <= 365
                and evidence.get("evidence_status") == "documented"
                and bool(evidence.get("note", "").strip()))
    except (ValueError, TypeError):
        return False


def saved_cash_flow_issues(source, method):
    """A reviewed numeric total alone cannot establish a cash-flow bridge."""
    record = source.get('cash_flow_reconciliation')
    if not isinstance(record, dict):
        return ['cash_flow: saved total has no reproducible cash-statement reconciliation; use the reconciliation helper and save its evidence']
    try:
        if record['method'] != method:
            raise ValueError('saved bridge uses a different DCF method')
        basis = record['basis']
        if not isinstance(basis, dict):
            raise ValueError('bridge basis must be an object')
        if any(basis.get(k) != source.get(k) for k in ('period_type', 'period_end')):
            raise ValueError('saved total and bridge cover different periods')
        result = reconcile_cash_flow(method, record['inputs'], basis)
        if not math.isclose(result['cash_flow'], source['value'], rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError('saved total differs from the reproduced bridge')
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return [f'cash_flow: saved reconciliation cannot be reproduced: {error}']
    return ['cash_flow: saved reconciliation arithmetic reproduced; source classification, leases, ownership and sustainable reinvestment still require review']


def distribution_check(stock, method, inputs):
    """Compare modeled first-year distributions with a saved historical cash input."""
    if method not in {'justified_pb', 'residual_income'}:
        return None
    required=('bvps','roe','terminal_growth') if method=='justified_pb' else ('bvps','roe','payout')
    if any(isinstance(inputs.get(k),bool) or not isinstance(inputs.get(k),(int,float))
           or not math.isfinite(inputs[k]) for k in required):
        return None
    if inputs['bvps']<=0 or inputs['roe']<=0:
        return None
    payout=1-inputs['terminal_growth']/inputs['roe'] if method=='justified_pb' else inputs['payout']
    modeled=inputs['bvps']*inputs['roe']*payout
    if not math.isfinite(modeled):
        return None
    source=stock.get('fields',{}).get('dividend',{})
    dividend=source.get('value')
    comparable=(not isinstance(dividend,bool) and isinstance(dividend,(int,float))
                and math.isfinite(dividend) and dividend>=0
                and source.get('unit','PHP/share')=='PHP/share'
                and source.get('period_type') in {'annual','ttm'})
    return dict(modeled_payout=payout,modeled_next_distribution=modeled,
                saved_annual_dividend=dividend if comparable else None,
                dividend_evidence=dict(source),
                note=(f"Payout check: next-year modeled distribution is {modeled:,.4f} per share ({payout:.2%} payout). "
                      +(f"Saved annual cash dividend is {dividend:,.4f}; periods and distribution scope differ, so this is not a like-for-like payout test. " if comparable else "No annual/TTM cash dividend is available for comparison. ")
                      +"Reconcile regular/special dividends, other distributions and capital needs; model agreement does not establish feasible payouts."))


def review_inputs(stock, policy, method, inputs, today=None, derivations=None):
    today=today or date.today()
    missing=[]; issues=[]; audit=[]; periods=set(); unsupported=[]; data_issues=[]
    if method == 'pe':
        from backend.earnings import check_pe_basis
        try:
            _, basis_notes = check_pe_basis(inputs)
            issues.extend(basis_notes)
        except ValueError as error:
            data_issues.append(str(error))
        if isinstance(inputs.get('pe_basis'), dict) and inputs['pe_basis'].get('kind') in {'forecast', 'normalized'}:
            unsupported.append('EPS forecast / normalization judgment')
            issues.append('Forecast or normalized EPS is a scenario assumption, even when it equals a saved historical figure.')
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
    if report_status == 'unresolved':
        for conflict in reports.get('source_conflicts',{}).values():
            data_issues.append(f"Source conflict: {conflict['field']} at {conflict['period_end']}: saved {conflict['previous']['value']} versus imported {conflict['proposed']['value']}. {conflict['note']}")
    for key in policy["methods"][method]["fields"]+["price"]:
        value=inputs.get(key)
        if value is None:
            if key!="price": missing.append(policy["fields"][key]["label"])
            if key in ASSUMPTIONS: unsupported.append(key)
            continue
        baseline_key=("fcff_cash_flow" if method=="dcf_fcff" else "fcfe_cash_flow") if key=="cash_flow" else key
        source=stock.get("fields",{}).get(baseline_key,{})
        derived=next((d for d in reversed(derivations or []) if isinstance(d,dict) and d.get("output_field")==key and d.get("value")==value),None)
        if method == "pe" and key == "eps" and isinstance(inputs.get("pe_basis"), dict) and inputs["pe_basis"].get("kind") in {"forecast", "normalized"}:
            kind="Scenario earnings assumption"; evidence=dict(inputs["pe_basis"])
        elif derived:
            kind="Calculated from helper inputs"; evidence=derived
            issues.append(f"{key}: review the helper's inputs and source periods")
            if derived.get('component_reconciliation'):
                try:
                    if method!='sotp' or key!='asset_value':
                        raise ValueError('component bridge belongs to SOTP owned asset value')
                    replay=reconcile_components(derived['component_reconciliation']['components'])
                    if not math.isclose(replay['asset_value'],value,rel_tol=1e-10,abs_tol=1e-8):
                        raise ValueError('component sum differs from valuation input')
                    issues.extend(replay['warnings'])
                except (ValueError,TypeError,KeyError,OverflowError) as error:
                    data_issues.append(f'asset_value: component reconciliation cannot be reproduced: {error}')
            if derived.get('reconciliation'):
                try:
                    record=derived['reconciliation']
                    if record['method']!=method:
                        raise ValueError('cash-flow method differs from the valuation method')
                    replay=reconcile_cash_flow(record['method'],record['inputs'],record['basis'])
                    output='net_debt' if key=='net_debt' else 'cash_flow'
                    if not math.isclose(replay[output],value,rel_tol=1e-10,abs_tol=1e-8):
                        raise ValueError('reconciled output differs from the valuation input')
                    issues.append(f"{key}: reconciliation arithmetic reproduced; source classification, leases and ownership scope still require review")
                except (ValueError,TypeError,KeyError,OverflowError) as error:
                    data_issues.append(f"{key}: reconciliation cannot be reproduced: {error}")
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
            if key == "eps": data_issues.extend(eps_bridge_issues(source, today))
            if key == "cash_flow": data_issues.extend(saved_cash_flow_issues(source, method))
            if key=='asset_value' and method=='sotp':
                try:
                    components=source.get('sotp_components')
                    if not isinstance(components,dict) or not components:
                        raise ValueError('saved component evidence is missing; use Add up owned businesses and save the baseline')
                    replay=reconcile_components(list(components.values()))
                    if not math.isclose(replay['asset_value'],value,rel_tol=1e-10,abs_tol=1e-8):
                        raise ValueError('saved asset total differs from the component sum')
                    data_issues.extend(replay['warnings'])
                except (ValueError,TypeError,KeyError,OverflowError) as error:
                    data_issues.append(f'asset_value: saved SOTP reconciliation cannot be reproduced: {error}')
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
    payout_check=distribution_check(stock,method,inputs)
    if payout_check: issues.append(payout_check['note'])
    issues = list(dict.fromkeys(data_issues + issues))
    # Documentation is not a certification; warnings survive input confirmation.
    data_warnings = data_issues or [s for s in issues if any(term in s for term in
        ("days old", "future", "invalid source date", "unit differs", "mix financial", "financial period", "saved figure needs review"))]
    return {"status":"Missing data" if missing else "Needs review" if issues else "Ready for input confirmation",
            "data_status":"Missing data" if missing else "Needs review" if data_warnings else "Reviewed inputs",
            "assumption_status":"Illustrative scenario" if unsupported else "Documented assumptions (not independently verified)",
            "unsupported_assumptions":unsupported, "reporting_status":report_status,
            "distribution_check":payout_check,
            "missing":missing,"issues":issues,"fields":audit,"checked_on":today.isoformat(),
            "note":"Confirmation acknowledges inputs; it does not clear warnings. Offline checks cannot discover disclosures absent from local records. Documentation does not certify accuracy or forecast quality."}
