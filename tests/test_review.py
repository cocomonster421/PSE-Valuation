import unittest
from datetime import date
from backend.review import review_inputs
from backend.catalog import initial_policy


class ReviewTests(unittest.TestCase):
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
