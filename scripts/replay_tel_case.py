"""Recalculate the sourced TEL case and its two-variable sensitivity table offline."""
import json
import math
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engine import calculate


def replay():
    case = json.loads((ROOT / 'examples/tel_case.json').read_text(encoding='utf-8'))
    facts, assumptions = case['reported'], case['assumptions']
    eps = facts['fy2025_eps'] + facts['h1_2026_eps'] - facts['h1_2025_eps']
    end = date.fromisoformat(case['analysis_date'])
    start = end.replace(year=end.year-1)
    events = case['dividend_events']
    assert len({event['id'] for event in events}) == len(events), 'Duplicate dividend events'
    included = [e for e in events if start < date.fromisoformat(e['payment_date']) <= end
                and e['kind']=='regular' and e['share_class']=='common']
    dividend = sum(e['amount_per_share'] for e in included)
    assert dividend == facts['april_2026_dividend'] + facts['september_2026_dividend']
    interim = {}
    for period in ('h1_2026','h1_2025'):
        data = case['interim_reconciliation'][period]
        reconstructed = data['common_earnings_million']*1000/data['weighted_shares_thousand']
        # Published totals are rounded to millions/thousands; EPS uses unrounded amounts.
        assert abs(reconstructed-data['reported_basic_eps']) < .01
        interim[period] = dict(eps_from_rounded_totals=reconstructed,
            cash_after_capex_before_remaining_adjustments=data['operating_cash_million']-data['cash_capex_million'],
            lease_settlements_million=data['lease_settlements_million'])
    price = case['price']['value']
    inputs = dict(dividend=dividend, discount_rate=assumptions['discount_rate'],
                  terminal_growth=assumptions['terminal_growth'], price=price)
    result = calculate('ddm', inputs)
    expected = case['expected']
    assert math.isclose(eps, expected['ttm_eps'], abs_tol=1e-8)
    assert dividend == expected['base_dividend']
    assert math.isclose(result['fair_value'], expected['fair_value'], abs_tol=1e-8)
    rows = []
    for rate in case['sensitivity']['discount_rates']:
        values = []
        for growth in case['sensitivity']['growth_rates']:
            value = calculate('ddm', dict(inputs, discount_rate=rate, terminal_growth=growth))['fair_value']
            assert math.isclose(value, dividend * (1 + growth) / (rate - growth), abs_tol=1e-8)
            values.append(round(value, 2))
        rows.append({'required_return': rate, 'values': values})
    annual = case['annual_source_comparison']
    annual_eps_check = annual['form_20f_common_earnings_million']*1000/annual['form_20f_weighted_shares_thousand']
    assert abs(annual_eps_check-annual['form_20f_basic_eps']) < .01
    return {'arithmetic_verified': True, 'source_reconciled': False,
            'annual_source_comparison': annual, 'verification_scope': 'Arithmetic only; not source accuracy or a calibrated price target',
            'dividend_schedule': included, 'interim_cross_check': interim,
            'source_review': case['source_review'], 'ticker': 'TEL', 'price_as_of': case['price']['as_of'],
            'provisional_ttm_eps': round(eps, 2), 'provisional_price_to_eps': price / eps,
            'trailing_dividend_yield': dividend / price, 'provisional_dividend_to_eps_screen': dividend / eps,
            'result': result, 'sensitivity_growth_rates': case['sensitivity']['growth_rates'],
            'sensitivity': rows,
            'growth_implied_by_price_at_base_return': (price * assumptions['discount_rate'] - dividend) / (price + dividend),
            'return_implied_by_price_at_base_growth': dividend * (1 + assumptions['terminal_growth']) / price + assumptions['terminal_growth']}


if __name__ == '__main__':
    print(json.dumps(replay(), indent=2))
