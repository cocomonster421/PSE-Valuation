"""Read-only review of saved inputs; no data refresh or fabricated financials."""
from backend.catalog import METHODS
from backend.engine import calculate
from backend.review import review_inputs


def review_company(stock, policy, today=None):
    recommended=policy.get('recommendations', {}).get(stock.get('archetype'), [])
    methods=recommended or list(METHODS)
    rows=[]
    for method in dict.fromkeys(methods):
        inputs={}
        model=stock.get('models', {}).get(method, {})
        for key in policy['methods'][method]['fields']+['price']:
            saved_key=('fcff_cash_flow' if method=='dcf_fcff' else 'fcfe_cash_flow') if key=='cash_flow' else key
            if key in model:
                value=model[key]
            else:
                value=stock.get('fields', {}).get(saved_key, {}).get('value')
                if value is None:
                    value=policy.get('defaults', {}).get(key)
            if value is not None and value != '':
                inputs[key]=value
        review=review_inputs(stock,policy,method,inputs,today=today)
        row={'method':method,'name':policy['methods'][method]['name'],
             'inputs':inputs,'review':review,'calculation_status':'Missing data'}
        if not review['missing']:
            try:
                result=calculate(method,inputs)
                row.update(calculation_status='Calculated',fair_value=result['fair_value'],
                           calculation_warnings=result['warnings'],formula=result['formula'])
            except (ValueError,TypeError,KeyError,OverflowError) as error:
                row.update(calculation_status='Invalid inputs',calculation_error=str(error))
        rows.append(row)
    return {'ticker':stock['ticker'],'name':stock['name'],
            'method_scope':'Recommended methods' if recommended else 'All methods; no saved recommendation',
            'methods':rows}
