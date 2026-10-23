import unittest

from backend.cash_flow import reconcile_cash_flow
from backend.review import review_inputs
from backend.catalog import initial_policy


def basis():
    return dict(period_type='annual',period_end='2025-12-31',lease_treatment='none',
                source_note='Synthetic cash-flow statement',scope_note='Parent, common equity only',
                lease_note='No leases in fixture',adjustment_note='Adjustments reviewed as zero')


def inputs():
    return dict(operating_cash_flow=100,interest_paid=10,interest_outside_cfo=0,tax=.25,
                capital_spending=30,additional_capex=5,cfo_adjustment=0,investment_adjustment=0,
                debt=200,cash=40,other_claims=10,borrowings=20,repayments=12,common_adjustment=-3)


class CashFlowTests(unittest.TestCase):
    def test_interest_classification_does_not_change_economic_cash(self):
        inside=reconcile_cash_flow('dcf_fcff',inputs(),basis())
        outside=reconcile_cash_flow('dcf_fcff',dict(inputs(),operating_cash_flow=110,interest_outside_cfo=10),basis())
        self.assertAlmostEqual(inside['cash_flow'],72.5)
        self.assertEqual(inside['cash_flow'],outside['cash_flow'])
        self.assertEqual(inside['net_debt'],170)

    def test_fcfe_matches_direct_after_interest_cash_bridge(self):
        result=reconcile_cash_flow('dcf_fcfe',inputs(),basis())
        self.assertEqual(result['cash_flow'],100-30-5+20-12-3)
        self.assertNotIn('net_debt',result)

    def test_signed_adjustments_are_explicit_not_absolute_values(self):
        base=reconcile_cash_flow('dcf_fcff',inputs(),basis())['cash_flow']
        adjusted=reconcile_cash_flow('dcf_fcff',dict(inputs(),cfo_adjustment=-7,investment_adjustment=-4),basis())
        self.assertEqual(adjusted['cash_flow'],base-11)

    def test_missing_invalid_or_incompatible_inputs_rejected(self):
        for change in ({'tax':1.1},{'capital_spending':-1},{'interest_outside_cfo':11},
                       {'cfo_adjustment':None},{'debt':True},{'cash':float('inf')}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                reconcile_cash_flow('dcf_fcff',dict(inputs(),**change),basis())
        for change in ({'period_type':'ytd'},{'lease_treatment':''},{'scope_note':''},{'period_end':'invalid'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                reconcile_cash_flow('dcf_fcff',inputs(),dict(basis(),**change))

    def test_review_replays_and_detects_altered_reconciliation(self):
        record=reconcile_cash_flow('dcf_fcff',inputs(),basis())
        valuation=dict(cash_flow=72.5,net_debt=170,shares=10,growth=.02,terminal_growth=.01,discount_rate=.1)
        evidence=[dict(output_field='cash_flow',value=72.5,reconciliation=record,inputs=record['inputs'])]
        checked=review_inputs({'fields':{}},initial_policy(),'dcf_fcff',valuation,derivations=evidence)
        self.assertTrue(any('arithmetic reproduced' in issue for issue in checked['issues']))
        record['inputs']['operating_cash_flow']=999
        checked=review_inputs({'fields':{}},initial_policy(),'dcf_fcff',valuation,derivations=evidence)
        self.assertTrue(any('cannot be reproduced' in issue for issue in checked['issues']))
