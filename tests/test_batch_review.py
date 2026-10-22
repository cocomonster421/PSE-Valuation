import unittest
from datetime import date

from backend.batch_review import review_company
from backend.catalog import initial_policy


class BatchReviewTests(unittest.TestCase):
    def setUp(self):
        self.policy=initial_policy()
        self.policy['recommendations']['FIXTURE']=['pe','dcf_fcff']
        self.stock={'ticker':'TEST','name':'Test company','archetype':'FIXTURE','fields':{}}

    def test_blank_company_remains_missing_without_fabricated_value(self):
        rows=review_company(self.stock,self.policy)['methods']
        self.assertEqual([row['method'] for row in rows],['pe','dcf_fcff'])
        for row in rows:
            self.assertEqual(row['calculation_status'],'Missing data')
            self.assertNotIn('fair_value',row)

    def test_company_override_and_illustrative_status_match_workspace(self):
        self.stock['fields']={'eps':{'value':5,'period_type':'annual'},'price':{'value':50}}
        self.stock['models']={'pe':{'multiple':12}}
        row=review_company(self.stock,self.policy,date(2026,10,23))['methods'][0]
        self.assertEqual(row['fair_value'],60)
        self.assertEqual(row['review']['assumption_status'],'Illustrative scenario')
        self.stock['models']['pe']['multiple']=''
        row=review_company(self.stock,self.policy)['methods'][0]
        self.assertEqual(row['calculation_status'],'Missing data')

    def test_invalid_method_inputs_do_not_hide_other_results(self):
        self.stock['fields']={'eps':{'value':-5}}
        self.stock['models']={'pe':{'multiple':12}}
        rows=review_company(self.stock,self.policy)['methods']
        self.assertEqual(rows[0]['calculation_status'],'Invalid inputs')
        self.assertEqual(rows[1]['calculation_status'],'Missing data')
