import unittest
from backend.components import reconcile_components
from backend.review import review_inputs
from backend.catalog import initial_policy
from backend.batch_review import review_company


def component(**changes):
    return dict(dict(name='Example',basis='enterprise',value=1000,net_claims=200,
                     ownership=.6,as_of='2025-12-31',source_note='Synthetic fixture'),**changes)


class ComponentTests(unittest.TestCase):
    def test_enterprise_equity_and_owned_values_agree(self):
        for row in (component(),component(basis='equity',value=800,net_claims=0),
                    component(basis='attributable',value=480,net_claims=0,ownership=1)):
            self.assertEqual(reconcile_components([row])['asset_value'],480)

    def test_double_counting_and_incomplete_rows_rejected(self):
        for rows in ([],[component(),component()], [component(basis='equity')],
                     [component(basis='attributable',net_claims=0)],
                     [component(value=None)],[component(ownership=1.1)],
                     [component(as_of='bad')],[component(source_note='')]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                reconcile_components(rows)

    def test_negative_equity_and_mixed_dates_remain_visible(self):
        result=reconcile_components([component(net_claims=1100),component(name='Second',as_of='2024-12-31')])
        self.assertEqual(result['asset_value'],420)
        self.assertTrue(any('negative equity' in w for w in result['warnings']))
        self.assertTrue(any('dates differ' in w for w in result['warnings']))

    def test_review_detects_altered_component_evidence(self):
        record=reconcile_components([component()])
        evidence=[dict(output_field='asset_value',value=480,component_reconciliation=record)]
        inputs=dict(asset_value=480,liabilities=80,shares=10,discount=.1)
        checked=review_inputs({},initial_policy(),'sotp',inputs,derivations=evidence)
        self.assertFalse(any('cannot be reproduced' in x for x in checked['issues']))
        record['components'][0]['value']=2000
        checked=review_inputs({},initial_policy(),'sotp',inputs,derivations=evidence)
        self.assertTrue(any('cannot be reproduced' in x for x in checked['issues']))

    def test_all_stock_review_replays_saved_component_total(self):
        stock={'ticker':'SYNTH','name':'Synthetic holding company','archetype':'CONGLOMERATE',
               'fields':{'asset_value':{'value':480,'sotp_components':{'one':component()}},
                         'liabilities':{'value':80},'shares':{'value':10}},
               'models':{'sotp':{'discount':.1}}}
        row=next(r for r in review_company(stock,initial_policy())['methods'] if r['method']=='sotp')
        self.assertEqual(row['fair_value'],36)
        self.assertFalse(any('cannot be reproduced' in x for x in row['review']['issues']))
        stock['fields']['asset_value']['sotp_components']['one']['ownership']=.5
        row=next(r for r in review_company(stock,initial_policy())['methods'] if r['method']=='sotp')
        self.assertTrue(any('saved asset total differs' in x for x in row['review']['issues']))
