"""Independent closed-form and economic consistency checks for the DCF model."""
import unittest

from backend.engine import calculate


class DcfProperties(unittest.TestCase):
    def test_nonzero_growth_against_growing_annuity(self):
        # Closed-form growing annuity is independent of the engine's annual loop.
        cash, growth, rate, terminal = 100, .05, .10, .02
        annuity = cash * (1 + growth) / (rate - growth) * (1 - ((1 + growth) / (1 + rate)) ** 5)
        continuing = cash * (1 + growth) ** 5 * (1 + terminal) / (rate - terminal) / (1 + rate) ** 5
        expected = (annuity + continuing - 200) / 10
        actual = calculate('dcf_fcff', dict(cash_flow=cash, growth=growth,
            discount_rate=rate, terminal_growth=terminal, net_debt=200, shares=10))
        self.assertAlmostEqual(actual['fair_value'], expected, places=10)

    def test_share_and_debt_bridges(self):
        inputs = dict(cash_flow=100, growth=.03, discount_rate=.12,
                      terminal_growth=.02, net_debt=200, shares=10)
        value = calculate('dcf_fcff', inputs)['fair_value']
        self.assertAlmostEqual(calculate('dcf_fcff', dict(inputs, shares=20))['fair_value'], value / 2)
        self.assertAlmostEqual(calculate('dcf_fcff', dict(inputs, net_debt=300))['fair_value'], value - 10)
        self.assertAlmostEqual(calculate('dcf_fcff', dict(inputs, cash_flow=1000, net_debt=2000, shares=100))['fair_value'], value)

    def test_invalid_and_nonpositive_equity_cases(self):
        inputs = dict(cash_flow=100, growth=0, discount_rate=.10,
                      terminal_growth=.02, net_debt=200, shares=10)
        for change in ({'shares':0}, {'shares':-1}, {'cash_flow':float('inf')},
                       {'discount_rate':.02}, {'terminal_growth':.06}, {'growth':-1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                calculate('dcf_fcff', dict(inputs, **change))
        negative = calculate('dcf_fcff', dict(inputs, net_debt=100000))
        self.assertLess(negative['fair_value'], 0)
        self.assertTrue(any('not a price target' in warning for warning in negative['warnings']))
