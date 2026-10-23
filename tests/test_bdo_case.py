import unittest
from scripts.replay_bdo_case import replay

class BdoCaseTests(unittest.TestCase):
    def test_common_book_and_equivalent_models(self):
        result=replay()
        self.assertAlmostEqual(result['book_from_rounded_totals'],119.03,places=2)
        self.assertEqual(result['common_equity_from_statements_million'],644146-3072-6180)
        self.assertAlmostEqual(result['scenario_value'],145.4811111111111)
        self.assertAlmostEqual(result['implied_payout'],11/14)
        self.assertAlmostEqual(result['implied_next_dividend'],13.0933)
        self.assertFalse(result['investment_target_verified'])

    def test_roe_hurdle_and_sensitivity(self):
        result=replay()
        grid=result['sensitivity']
        self.assertAlmostEqual(grid[1]['values'][1],119.03)
        for row in grid:
            self.assertEqual(row['values'],sorted(row['values'],reverse=True))
        for column in range(3):
            values=[row['values'][column] for row in grid]
            self.assertEqual(values,sorted(values))

    def test_dividend_policy_exposes_distribution_gap(self):
        result=replay()
        check=result['dividend_policy_check']
        self.assertAlmostEqual(check['annualized_regular_cash'],4.4)
        self.assertAlmostEqual(check['modeled_next_regular_cash'],4.532)
        self.assertAlmostEqual(check['regular_cash_only_ddm'],4.532/.09)
        self.assertAlmostEqual(check['distribution_multiplier'],13.0933/4.532)
        self.assertLess(check['regular_cash_only_ddm'],result['scenario_value'])
