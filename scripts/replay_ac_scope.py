"""Reproduce AC ownership/claims checks; this worksheet has no completed SOTP."""
import json
from decimal import Decimal
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.components import reconcile_components

def replay():
    case=json.loads((ROOT/'examples/ac_scope_check.json').read_text(encoding='utf-8'))
    r=case['reported']
    group_equity=r['total_assets_thousand']-r['total_liabilities_thousand']
    if group_equity!=r['total_equity_thousand']:
        raise ValueError('Consolidated balance-sheet totals do not reconcile')
    noncontrolling=group_equity-r['parent_attributable_equity_thousand']
    missing=[]
    if not case['components']: missing.append('Dated attributable component equity values and ownership stakes')
    elif case.get('component_coverage')!='complete':
        missing.append('Unlisted investments, other assets and overlapping ownership reconciliation')
    components=list(case['components'].values())
    subtotal=reconcile_components(components) if components else None
    # Independent decimal calculation checks the production helper's ownership math.
    exact=sum((Decimal(str(row['value']))*Decimal(str(row['ownership']))
               for row in components),Decimal(0))
    if subtotal and abs(Decimal(str(subtotal['asset_value']))-exact)>Decimal('0.01'):
        raise ValueError('Component ownership arithmetic does not reconcile')
    for key in ('remaining_parent_claims','period_matched_common_shares','holding_discount'):
        if case[key] is None: missing.append(key)
    return dict(status=case['status'],fair_value=None,
        scope_note='Source-scope checks only; not a valuation calculator or certified accounting conclusion.',
        consolidated_equity_php=group_equity*1000,
        noncontrolling_equity_php=noncontrolling*1000,
        listed_market_value_subtotal_php=int(exact) if components else None,
        listed_component_steps=subtotal['steps'] if subtotal else [],
        component_coverage=case.get('component_coverage','missing'),
        excess_of_consolidated_over_parent_net_debt_php=int(
            (Decimal(str(r['consolidated_net_debt_billion']))
             - Decimal(str(r['parent_net_debt_billion']))) * 1_000_000_000),
        missing_valuation_evidence=missing,limitations=case['limitations'])

if __name__=='__main__':
    print(json.dumps(replay(),indent=2))
