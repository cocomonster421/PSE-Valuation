"""Reproduce ownership-weighted component values without inferring their fair values."""
import math
from datetime import date


def reconcile_components(components):
    if not isinstance(components,list) or not 1 <= len(components) <= 100:
        raise ValueError('Enter between 1 and 100 businesses or assets')
    steps=[]; dates=set(); names=set()
    for item in components:
        if not isinstance(item,dict):
            raise ValueError('Each component must be an object')
        for key in ('name','source_note','as_of'):
            if not isinstance(item.get(key),str) or not item[key].strip():
                raise ValueError(f'Each component needs {key}')
        name=item['name'].strip()
        if name.casefold() in names:
            raise ValueError('Duplicate component name; check for double counting')
        names.add(name.casefold())
        try:
            dates.add(date.fromisoformat(item['as_of']).isoformat())
        except ValueError:
            raise ValueError('Use a valid component valuation date')
        kind=item.get('basis')
        if kind not in {'enterprise','equity','attributable'}:
            raise ValueError('Choose enterprise, equity or already-owned equity value')
        for key in ('value','net_claims','ownership'):
            value=item.get(key)
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError(f'{name}: {key} must be a finite number')
        if item['value']<0 or not 0<=item['ownership']<=1:
            raise ValueError('Starting value must be nonnegative and ownership between 0% and 100%')
        if kind!='enterprise' and item['net_claims']!=0:
            raise ValueError('Equity value already reflects subsidiary financing; do not subtract its debt again')
        if kind=='attributable' and item['ownership']!=1:
            raise ValueError('Already-owned equity value must use 100%; do not apply ownership twice')
        equity=item['value']-item['net_claims']
        owned=equity*item['ownership']
        if not math.isfinite(owned):
            raise ValueError('Component calculation overflow')
        steps.append(dict(name=name,equity_value=equity,attributable_value=owned,
                          formula=f"({item['value']} − {item['net_claims']}) × {item['ownership']}"))
    total=math.fsum(s['attributable_value'] for s in steps)
    if not math.isfinite(total):
        raise ValueError('Component total overflow')
    warnings=['Review component valuations and ownership. Subtract only remaining parent claims in the main valuation; subsidiary equity already reflects subsidiary debt.']
    if len(dates)>1: warnings.append('Component valuation dates differ; reconcile timing before relying on the sum.')
    if any(s['attributable_value']<0 for s in steps):
        warnings.append('A component has negative equity. Review limited liability and parent guarantees; no automatic zero floor was applied.')
    return dict(asset_value=total,components=components,steps=steps,warnings=warnings)
