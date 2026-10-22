import unittest
from datetime import date
from backend.review import review_inputs
from backend.catalog import initial_policy


class ReviewTests(unittest.TestCase):
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
