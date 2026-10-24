import unittest
from scripts.replay_ac_scope import replay

class AcScopeTests(unittest.TestCase):
    def test_listed_holdings_replay_without_claiming_complete_nav(self):
        result=replay()
        self.assertEqual(result['listed_market_value_subtotal_php'],587569900000)
        self.assertEqual(len(result['listed_component_steps']),6)
        self.assertEqual(result['component_coverage'],'partial_listed_only')
        self.assertIn('Unlisted investments',result['missing_valuation_evidence'][0])
        self.assertTrue(any('Mynt' in item and 'Globe' in item for item in result['limitations']))
        self.assertIsNone(result['fair_value'])

    def test_consolidated_and_parent_scopes_are_distinct(self):
        result=replay()
        self.assertEqual(result['consolidated_equity_php'],809848573000)
        self.assertEqual(result['noncontrolling_equity_php'],298186077000)
        self.assertEqual(result['excess_of_consolidated_over_parent_net_debt_php'],500900000000)

    def test_incomplete_sources_do_not_produce_a_target(self):
        result=replay()
        self.assertIsNone(result['fair_value'])
        self.assertEqual(len(result['missing_valuation_evidence']),4)
