"""Recalculate the sourced TEL case and its two-variable sensitivity table offline."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engine import calculate


def replay():
    case = json.loads((ROOT / 'examples/tel_case.json').read_text(encoding='utf-8'))
    facts, assumptions = case['reported'], case['assumptions']
    eps = facts['fy2025_eps'] + facts['h1_2026_eps'] - facts['h1_2025_eps']
    dividend = facts['april_2026_dividend'] + facts['september_2026_dividend']
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
    return {'verified': True, 'ticker': 'TEL', 'price_as_of': case['price']['as_of'],
            'ttm_eps': round(eps, 2), 'current_pe': price / eps,
            'trailing_dividend_yield': dividend / price, 'payout_to_reported_ttm_eps': dividend / eps,
            'result': result, 'sensitivity_growth_rates': case['sensitivity']['growth_rates'],
            'sensitivity': rows,
            'growth_implied_by_price_at_base_return': (price * assumptions['discount_rate'] - dividend) / (price + dividend),
            'return_implied_by_price_at_base_growth': dividend * (1 + assumptions['terminal_growth']) / price + assumptions['terminal_growth']}


if __name__ == '__main__':
    print(json.dumps(replay(), indent=2))
