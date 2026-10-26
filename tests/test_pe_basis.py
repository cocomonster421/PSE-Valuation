import unittest
from backend.engine import calculate, compare


class PeBasisTests(unittest.TestCase):
    def inputs(self):
        return dict(eps=11, multiple=12, price=100, pe_basis=dict(
            kind='forecast', multiple_basis='forecast', period='FY2027',
            note='Illustrative peer forward multiple at valuation date; not an industry estimate',
            calculation='growth', base_eps=10, growth=.1, base_period='FY2026'))

    def test_forward_value_and_market_ratio_are_separate(self):
        result=calculate('pe', self.inputs())
        self.assertEqual(result['fair_value'],132)
        self.assertAlmostEqual(result['current_ratios']['current_pe'],100/11)
        self.assertEqual(result['steps'][0]['value'],11)

    def test_mismatched_basis_and_stale_helper_rejected(self):
        for patch in ({'multiple_basis':'historical'}, {'growth':.2},
                      {'base_eps':None}, {'base_eps':True}, {'growth':-1},
                      {'period':''}, {'note':''}, {'base_period':''}):
            with self.subTest(patch=patch):
                inputs=self.inputs();inputs['pe_basis'].update(patch)
                with self.assertRaises(ValueError): calculate('pe',inputs)

    def test_manual_forecast_and_historical_basis(self):
        for kind in ('forecast','normalized','historical'):
            inputs=self.inputs()
            inputs['pe_basis'].update(kind=kind,multiple_basis=kind,calculation='manual')
            self.assertEqual(calculate('pe',inputs)['fair_value'],132)

    def test_legacy_inputs_warn_without_changing_value(self):
        result=calculate('pe',dict(eps=10,multiple=12))
        self.assertEqual(result['fair_value'],120)
        self.assertIn('unspecified',result['warnings'][0])

    def test_eps_stress_is_direct_override_and_keeps_original_bridge(self):
        inputs=self.inputs()
        result=compare('pe',inputs,'eps',9,13)
        self.assertEqual([c['result']['fair_value'] for c in result['cases']],[108,132,156])
        self.assertEqual(result['cases'][0]['result']['inputs']['pe_basis']['calculation'],'manual')
        self.assertEqual(inputs['pe_basis']['calculation'],'growth')

    def test_forecast_equal_to_historical_value_remains_assumption(self):
        from backend.review import review_inputs
        from backend.catalog import initial_policy
        inputs=self.inputs()
        stock={'fields':{'eps':{'value':11,'period_type':'annual'}}}
        review=review_inputs(stock,initial_policy(),'pe',inputs)
        eps=next(row for row in review['fields'] if row['field']=='eps')
        self.assertEqual(eps['kind'],'Scenario earnings assumption')
        self.assertEqual(review['assumption_status'],'Illustrative scenario')
