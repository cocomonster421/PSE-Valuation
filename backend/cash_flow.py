"""Auditable cash-flow statement bridge; accounting classifications remain reviewed inputs."""
import math
from datetime import date

LABELS = {
    'operating_cash_flow':'Reported operating cash flow',
    'interest_paid':'Interest paid on financing debt',
    'interest_outside_cfo':'That interest paid outside operating cash flow',
    'tax':'Tax rate for the interest deduction',
    'capital_spending':'Equipment and property investment',
    'additional_capex':'Other capital investment',
    'cfo_adjustment':'Other operating-cash adjustments',
    'investment_adjustment':'Investment adjustments',
    'borrowings':'New debt financing', 'repayments':'Debt principal repaid',
    'common_adjustment':'Adjustment to cash attributable to common shareholders',
    'debt':'Financing debt balance', 'cash':'Available excess cash',
    'other_claims':'Other claims ahead of common shareholders',
}
COMMON = ['operating_cash_flow','interest_paid','interest_outside_cfo','tax',
          'capital_spending','additional_capex','cfo_adjustment','investment_adjustment']


def reconcile_cash_flow(method, inputs, basis):
    if method not in {'dcf_fcff','dcf_fcfe'}:
        raise ValueError('Choose FCFF or FCFE')
    if not isinstance(inputs,dict) or not isinstance(basis,dict):
        raise ValueError('Cash-flow inputs and basis must be objects')
    if basis.get('period_type') not in {'annual','ttm'}:
        raise ValueError('Use a full year or trailing 12 months; do not annualize a quarter automatically')
    try:
        date.fromisoformat(basis.get('period_end',''))
    except (TypeError,ValueError):
        raise ValueError('Enter the cash-flow period end')
    if basis.get('lease_treatment') not in {'operating','financing','none'}:
        raise ValueError('Record the lease treatment')
    for key in ('source_note','scope_note','lease_note','adjustment_note'):
        if not isinstance(basis.get(key),str) or not basis[key].strip():
            raise ValueError(f'{key}: explain the source, treatment or reviewed absence of adjustments')
    keys=COMMON+(['debt','cash','other_claims'] if method=='dcf_fcff' else ['borrowings','repayments','common_adjustment'])
    values={}
    signed={'operating_cash_flow','cfo_adjustment','investment_adjustment','common_adjustment'}
    for key in keys:
        value=inputs.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError(f'{LABELS[key]}: enter a finite number; missing is not zero')
        if key not in signed and value<0:
            raise ValueError(f'{LABELS[key]}: enter a positive amount or reviewed zero')
        values[key]=value
    if values['tax']>1:
        raise ValueError('Tax rate must be between 0% and 100%')
    if values['interest_outside_cfo']>values['interest_paid']:
        raise ValueError('Interest outside operating cash flow cannot exceed total financing interest paid')
    v=values
    normalized=v['operating_cash_flow']-v['interest_outside_cfo']+v['cfo_adjustment']
    after_tax_interest=v['interest_paid']*(1-v['tax'])
    fcff=normalized+after_tax_interest-v['capital_spending']-v['additional_capex']+v['investment_adjustment']
    steps=[
        {'label':'Normalized operating cash = Reported operating cash flow − That interest paid outside operating cash flow + Other operating-cash adjustments','value':normalized},
        {'label':'After-tax financing interest = Interest paid on financing debt × (1 − Tax rate for the interest deduction)','value':after_tax_interest},
        {'label':'FCFF = Normalized operating cash + After-tax financing interest − Equipment and property investment − Other capital investment + Investment adjustments','value':fcff}]
    result={'method':method,'reconciliation_version':'1.0','inputs':values,'basis':dict(basis),'steps':steps,'fcff':fcff}
    if method=='dcf_fcff':
        result['cash_flow']=fcff
        result['net_debt']=v['debt']-v['cash']+v['other_claims']
        steps.append({'label':'Net claims = Financing debt balance − Available excess cash + Other claims ahead of common shareholders','value':result['net_debt']})
    else:
        fcfe=fcff-after_tax_interest+v['borrowings']-v['repayments']+v['common_adjustment']
        result['cash_flow']=fcfe
        steps.append({'label':'FCFE = FCFF − After-tax financing interest + New debt financing − Debt principal repaid + Adjustment to cash attributable to common shareholders','value':fcfe})
    if any(not math.isfinite(step['value']) for step in steps):
        raise ValueError('Cash-flow reconciliation overflow; check units')
    result['warnings']=['Accounting classifications and adjustments are user-supplied, not independently verified.',
        'Keep leases, investment, financing, ownership scope and the chosen discount rate consistent. Do not subtract working-capital movements again: reported operating cash already includes them.']
    return result
