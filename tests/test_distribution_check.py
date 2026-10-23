import unittest

from backend.engine import calculate
from backend.catalog import initial_policy
from backend.batch_review import review_company
from backend.review import distribution_check


class DistributionCheckTests(unittest.TestCase):
    def test_justified_book_exposes_required_payout_without_changing_value(self):
        inputs=dict(bvps=100,roe=.14,terminal_growth=.03,discount_rate=.12)
        result=calculate('justified_pb',inputs)
        self.assertAlmostEqual(result['fair_value'],100*11/9)
        self.assertAlmostEqual(result['steps'][-1]['value'],11)
        self.assertTrue(any('not a declared dividend' in w for w in result['warnings']))
        check=distribution_check({'fields':{'dividend':{'value':4,'period_type':'annual'}}},'justified_pb',inputs)
        self.assertAlmostEqual(check['modeled_payout'],11/14)
        self.assertEqual(check['saved_annual_dividend'],4)
        self.assertIn('not a like-for-like',check['note'])

    def test_partial_missing_or_wrong_units_are_not_annualized(self):
        inputs=dict(bvps=100,roe=.14,terminal_growth=.03)
        for source in ({},{'value':1,'period_type':'quarter'},
                       {'value':4,'period_type':'annual','unit':'PHP million'}):
            check=distribution_check({'fields':{'dividend':source}},'justified_pb',inputs)
            self.assertIsNone(check['saved_annual_dividend'])
        self.assertIsNone(distribution_check({},'justified_pb',dict(inputs,roe=0)))

    def test_offline_bank_review_uses_entered_payout_for_residual_income(self):
        stock={'ticker':'FIXTURE','name':'Synthetic bank','archetype':'BANK',
               'fields':{'bvps':{'value':100},'dividend':{'value':4,'period_type':'annual'}},
               'models':{'residual_income':{'roe':.14,'payout':.3,'terminal_growth':.03,'discount_rate':.12}}}
        report=review_company(stock,initial_policy())
        row=next(r for r in report['methods'] if r['method']=='residual_income')
        self.assertAlmostEqual(row['review']['distribution_check']['modeled_next_distribution'],4.2)
        self.assertTrue(any('Payout check' in issue for issue in row['review']['issues']))
