import unittest

from backend.engine import calculate, compare


class ValuationTests(unittest.TestCase):
    def test_residual_growth_and_dcf_trace(self):
        result=calculate('residual_income',dict(bvps=100,roe=.02,discount_rate=.1,terminal_growth=.04,payout=.5))
        self.assertTrue(any('outside 0' in w for w in result['warnings']))
        result=calculate('dcf_fcff',dict(cash_flow=100,growth=0,discount_rate=.1,terminal_growth=0,net_debt=200,shares=10))
        self.assertEqual(result['steps'][-1]['value'],result['fair_value'])
        self.assertIn('discount_factor',result['steps'][0])
    def test_specialist_methods_against_hand_calculations(self):
        cases = [
            ("pe", {"eps": 12, "multiple": 10}, 120),
            ("pb", {"bvps": 100, "multiple": 1.2}, 120),
            ("affo", {"affo_per_share": 3, "multiple": 15}, 45),
            ("justified_pb", {"bvps": 100, "roe": .16, "discount_rate": .1, "terminal_growth": .02}, 175),
            ("dividend_cap", {"dividend": 3, "required_yield": .06}, 50),
            ("cap_rate", {"noi": 100, "cap_rate": .05, "net_debt": 500, "shares": 10}, 150),
            ("embedded_value", {"adjusted_net_worth": 1000, "in_force_value": 500, "shares": 10}, 150),
            ("nav", {"asset_value": 1500, "liabilities": 500, "discount": .1, "shares": 10}, 90),
            ("rnav", {"asset_value": 1500, "liabilities": 500, "discount": .1, "shares": 10}, 90),
        ]
        for method, inputs, expected in cases:
            with self.subTest(method=method):
                self.assertAlmostEqual(calculate(method, inputs)["fair_value"], expected)
    def test_discount_sensitivity_recomputes_values(self):
        result = compare("ddm", dict(dividend=10, discount_rate=.12, terminal_growth=.02), "discount_rate", .1, .14)
        values = [case["result"]["fair_value"] for case in result["cases"]]
        self.assertAlmostEqual(values[0], 127.5)
        self.assertAlmostEqual(values[1], 102)
        self.assertAlmostEqual(values[2], 85)

    def test_invalid_sensitivity_case_is_not_fabricated(self):
        with self.assertRaises(ValueError):
            compare("ddm", dict(dividend=10, discount_rate=.12, terminal_growth=.02), "discount_rate", .01, .14)
    def test_perpetual_cash_flow_enterprise_bridge(self):
        result = calculate("dcf_fcff", dict(cash_flow=100, growth=0, discount_rate=.1,
                           terminal_growth=0, net_debt=200, shares=10, price=50))
        self.assertAlmostEqual(result["fair_value"], 80)
        self.assertAlmostEqual(result["gap"], .6)

    def test_fcfe_does_not_subtract_debt(self):
        result = calculate("dcf_fcfe", dict(cash_flow=100, growth=0, discount_rate=.1,
                           terminal_growth=0, net_debt=200, shares=10))
        self.assertAlmostEqual(result["fair_value"], 100)

    def test_ddm(self):
        self.assertAlmostEqual(calculate("ddm", dict(dividend=10, terminal_growth=.02,
                                                   discount_rate=.12))["fair_value"], 102)

    def test_residual_income_at_cost_of_equity_equals_book(self):
        result = calculate("residual_income", dict(bvps=100, roe=.1, discount_rate=.1,
                                                    terminal_growth=.02, payout=.5))
        self.assertEqual(result["fair_value"], 100)

    def test_invalid_inputs(self):
        for rate in [.02, .01, float("nan"), True]:
            with self.assertRaises(ValueError):
                calculate("ddm", dict(dividend=10, terminal_growth=.02, discount_rate=rate))

    def test_nav_debt_and_discount(self):
        self.assertEqual(calculate("sotp", dict(asset_value=1000, liabilities=200,
                         discount=.25, shares=10))["fair_value"], 60)


if __name__ == "__main__":
    unittest.main()
