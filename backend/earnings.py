"""Validate explicit P/E earnings bases without inventing earnings forecasts."""
import math


def check_pe_basis(inputs):
    basis = inputs.get('pe_basis')
    if basis is None:
        return [], ['Earnings basis is unspecified in this older input set. Match annual EPS and comparison P/E periods before relying on the value.']
    if not isinstance(basis, dict):
        raise ValueError('P/E earnings basis must be an object')
    kind = basis.get('kind')
    if kind not in {'historical', 'normalized', 'forecast'}:
        raise ValueError('Choose historical, normalized or forecast EPS')
    if basis.get('multiple_basis') != kind:
        raise ValueError('Comparison P/E must use the same earnings basis as EPS')
    for key in ('period', 'note'):
        if not isinstance(basis.get(key), str) or not basis[key].strip():
            raise ValueError('Enter the annual earnings period and the basis for your comparison P/E')
    steps = []
    if basis.get('calculation') not in {'manual', 'growth'}:
        raise ValueError('Choose direct EPS entry or the growth helper')
    if basis['calculation'] == 'growth':
        if kind != 'forecast':
            raise ValueError('The forecast growth helper requires forecast EPS')
        base, growth = basis.get('base_eps'), basis.get('growth')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (base, growth)):
            raise ValueError('Base annual EPS and expected EPS growth must be finite numbers')
        if base <= 0 or growth <= -1:
            raise ValueError('Growth helper requires positive base annual EPS and growth above -100%; enter a separately modeled recovery EPS directly')
        if not isinstance(basis.get('base_period'), str) or not basis['base_period'].strip():
            raise ValueError('Enter the base annual EPS period')
        forecast = base * (1 + growth)
        eps = inputs.get('eps')
        if not math.isfinite(forecast) or isinstance(eps, bool) or not isinstance(eps, (int, float)) or not math.isclose(forecast, eps, rel_tol=1e-10, abs_tol=1e-8):
            raise ValueError('Forecast EPS differs from Base annual EPS × (1 + Expected EPS growth); apply the helper again')
        steps.append({'label': f'Forecast annual EPS = Base annual EPS ({base:g}) × (1 + Expected EPS growth ({growth * 100:g}%))', 'value': forecast})
    warnings = [f'{kind.capitalize()} annual EPS period: {basis["period"]}. Comparison P/E must cover the same earnings basis; the saved explanation is not independently verified.']
    if kind == 'forecast':
        warnings.append('Forecast EPS is an estimate, not reported earnings. A current forward P/E calculated from price is not an independent target multiple. This is a value at the comparison multiple’s pricing date, not automatically a future price target.')
    return steps, warnings
