"""Reproduce the dated BDO equity-model consistency example offline."""
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.engine import calculate


def replay():
    case=json.loads((ROOT/'examples/bdo_case.json').read_text(encoding='utf-8'))
    facts=case['reported']; assumptions=case['assumptions']
    book=facts['bvps']; roe=assumptions['roe']; rate=assumptions['discount_rate']; growth=assumptions['terminal_growth']
    book_check=facts['common_equity_million']/facts['common_shares_million']
    assert abs(book_check-book)<.01
    payout=1-growth/roe
    inputs=dict(bvps=book,roe=roe,discount_rate=rate,terminal_growth=growth,price=facts['period_end_price'])
    justified=calculate('justified_pb',inputs)
    residual=calculate('residual_income',dict(inputs,payout=payout))
    next_dividend=book*roe*payout
    # DDM expects D0, while the book-based model derives D1.
    ddm=calculate('ddm',dict(dividend=next_dividend/(1+growth),discount_rate=rate,terminal_growth=growth))
    direct=book+sum(book*(1+growth)**(year-1)*(roe-rate)/(1+rate)**year for year in range(1,1001))
    for value in (residual['fair_value'],ddm['fair_value'],direct):
        assert math.isclose(justified['fair_value'],value,rel_tol=1e-10)
    observed_pb=facts['period_end_price']/book
    grid=[]
    for expected_roe in case['sensitivity']['roe']:
        grid.append(dict(roe=expected_roe,values=[calculate('justified_pb',dict(inputs,roe=expected_roe,discount_rate=r))['fair_value'] for r in case['sensitivity']['discount_rate']]))
    return dict(arithmetic_verified=True,investment_target_verified=False,scope=case['scope'],
                book_from_rounded_totals=book_check,observed_pb=observed_pb,
                scenario_value=justified['fair_value'],residual_income_value=residual['fair_value'],
                consistent_ddm_value=ddm['fair_value'],discounted_residual_income_value=direct,
                implied_payout=payout,implied_next_dividend=next_dividend,
                required_roe_at_reference_price=growth+observed_pb*(rate-growth),
                sensitivity=grid,assumptions=assumptions,limitations=case['limitations'])

if __name__=='__main__':
    print(json.dumps(replay(),indent=2))
