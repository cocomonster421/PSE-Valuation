import unittest
from datetime import date
from backend.review import review_inputs
from backend.catalog import initial_policy


class ReviewTests(unittest.TestCase):
    def test_annual_valuation_rejects_partial_or_unknown_period_as_reviewed(self):
        stock={'fields':{'eps':{'value':5,'status':'reviewed','period_end':'2026-06-30','note':'Reported EPS'}},
               'reports':{'review_status':'reviewed','review_note':'Checked sources','reviewed_on':'2026-10-22'}}
        for period in ('quarter','ytd','point_in_time','unknown','annual','ttm'):
            with self.subTest(period=period):
                stock['fields']['eps']['period_type']=period
                checked=review_inputs(stock,initial_policy(),'pe',dict(eps=5,multiple=10),date(2026,10,22))
                self.assertEqual(checked['data_status'],'Reviewed inputs' if period == 'annual' else 'Needs review')

    def test_helper_cannot_hide_quarterly_source_or_override(self):
        source={'value':100,'period_type':'quarter','period_end':'2026-06-30'}
        derivation={'output_field':'cash_flow','value':70,'inputs':{'operating_profit':100},'sources':{'operating_profit':source}}
        inputs=dict(cash_flow=70,growth=.03,discount_rate=.12,terminal_growth=.02,shares=10,net_debt=0)
        checked=review_inputs({'fields':{}},initial_policy(),'dcf_fcff',inputs,derivations=[derivation])
        self.assertTrue(any('saved period type is quarter' in s for s in checked['issues']))
        derivation['inputs']['operating_profit']=120
        checked=review_inputs({'fields':{}},initial_policy(),'dcf_fcff',inputs,derivations=[derivation])
        self.assertTrue(any('helper input differs' in s for s in checked['issues']))

    def test_missing_assumptions_are_not_documented(self):
        checked=review_inputs({'fields':{}},initial_policy(),'ddm',{})
        self.assertEqual(checked['assumption_status'],'Illustrative scenario')
        self.assertIn('discount_rate',checked['unsupported_assumptions'])

    def test_documentation_requires_explicit_status_and_current_date(self):
        stock={"models":{"pe":{"multiple":10,"note":"Peer sample and exclusions documented in local research", "as_of":"2026-10-22"}}}
        inputs={"eps":5,"multiple":10}
        checked=review_inputs(stock,initial_policy(),"pe",inputs,date(2026,10,22))
        self.assertEqual(checked['assumption_status'],'Illustrative scenario')
        stock['models']['pe']['evidence_status']='documented'
        checked=review_inputs(stock,initial_policy(),"pe",inputs,date(2026,10,22))
        self.assertEqual(checked['unsupported_assumptions'],[])
        for change in ({'as_of':'2027-01-01'},{'as_of':'2020-01-01'},{'note':''}):
            changed={**stock,'models':{'pe':{**stock['models']['pe'],**change}}}
            self.assertEqual(review_inputs(changed,initial_policy(),"pe",inputs,date(2026,10,22))['assumption_status'],'Illustrative scenario')

    def test_manual_assumption_cannot_inherit_saved_documentation(self):
        stock={'models':{'pe':{'multiple':10,'note':'Documented comparison','as_of':'2026-10-22','evidence_status':'documented'}}}
        checked=review_inputs(stock,initial_policy(),'pe',dict(eps=5,multiple=11),date(2026,10,22))
        self.assertIn('multiple',checked['unsupported_assumptions'])

    def test_reporting_issue_survives_reviewed_figures(self):
        stock={'fields':{'bvps':{'value':10,'status':'reviewed','period_end':'2026-06-30','note':'Report'}},
               'reports':{'review_status':'unresolved','review_note':'Audit opinion withdrawn; reconciliation pending'}}
        checked=review_inputs(stock,initial_policy(),'pb',dict(bvps=10,multiple=1),date(2026,10,22))
        self.assertEqual(checked['data_status'],'Needs review')
        self.assertTrue(any('Audit opinion withdrawn' in issue for issue in checked['issues']))
        stock['reports']={'review_status':'reconciled','review_note':'Checked revised report against prior inputs','reviewed_on':'2026-10-22'}
        self.assertEqual(review_inputs(stock,initial_policy(),'pb',dict(bvps=10,multiple=1),date(2026,10,22))['data_status'],'Reviewed inputs')

    def test_missing_and_stale_are_visible(self):
        stock={"fields":{"eps":{"value":5,"period_end":"2020-12-31","status":"needs_review"}},"models":{"pe":{"multiple":10,"note":"Illustrative","as_of":"2025-01-01"}}}
        checked=review_inputs(stock,initial_policy(),"pe",{"eps":5,"multiple":10},date(2026,10,22))
        self.assertEqual(checked["status"],"Needs review")
        self.assertTrue(any("days old" in s for s in checked["issues"]))
        self.assertEqual(checked['fields'][1]['kind'],'Company assumption')
        self.assertEqual(review_inputs(stock,initial_policy(),"pe",{})['status'],'Missing data')

    def test_override_does_not_claim_old_source(self):
        stock={"fields":{"eps":{"value":5,"source_url":"https://example.com"}}}
        checked=review_inputs(stock,initial_policy(),"pe",{"eps":6,"multiple":10})
        self.assertEqual(checked['fields'][0]['kind'],'Manual or calculated input')
        self.assertNotIn('source_url',checked['fields'][0]['evidence'])

    def test_units_and_mixed_periods(self):
        stock={'fields':{'cash_flow':{},'fcff_cash_flow':{'value':100,'period_end':'2025-12-31','status':'reviewed','unit':'PHP thousands'},'shares':{'value':10,'period_end':'2024-12-31','status':'reviewed'},'net_debt':{'value':20,'period_end':'2025-12-31','status':'reviewed'}}}
        checked=review_inputs(stock,initial_policy(),'dcf_fcff',dict(cash_flow=100,shares=10,net_debt=20,growth=.03,terminal_growth=.02,discount_rate=.1),date(2026,10,22))
        self.assertTrue(any('unit differs' in s for s in checked['issues']))
        self.assertTrue(any('mix financial periods' in s for s in checked['issues']))

    def test_source_conflict_does_not_treat_new_periods_or_prices_as_revisions(self):
        from backend.review import same_period_conflict
        old=dict(value=10,period_end='2025-12-31')
        self.assertIsNone(same_period_conflict('eps',old,dict(value=10,period_end='2025-12-31')))
        self.assertIsNone(same_period_conflict('eps',old,dict(value=12,period_end='2026-06-30')))
        self.assertIsNone(same_period_conflict('price',old,dict(value=12,period_end='2025-12-31')))
        self.assertIsNone(same_period_conflict('eps',{},dict(value=12,period_end='2025-12-31')))
        self.assertIsNotNone(same_period_conflict('eps',old,dict(value=12,period_end='2025-12-31')))
