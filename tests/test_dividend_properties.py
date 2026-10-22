"""Check dividend valuation against cash payments and equivalent equity models."""
import math
import unittest

from backend.engine import calculate


class DividendProperties(unittest.TestCase):
    def test_tel_against_individually_discounted_payments(self):
        # Sum 1,000 annual payments, without using the Gordon formula.
        dividend, discount, payments = 92.0, 1.0, []
        for _ in range(1000):
            dividend *= 1.01
            discount *= 1.12
            payments.append(dividend / discount)
        result = calculate('ddm', dict(dividend=92, discount_rate=.12, terminal_growth=.01))
        self.assertAlmostEqual(result['fair_value'], math.fsum(payments), places=9)

    def test_full_distribution_fcfe_matches_ddm(self):
        # When all shareholder cash is paid, identical growth/risk must give
        # the same value under a five-year FCFE model and perpetual DDM.
        for growth in (-.02, 0, .01, .04):
            with self.subTest(growth=growth):
                ddm = calculate('ddm', dict(dividend=92, discount_rate=.12, terminal_growth=growth))
                fcfe = calculate('dcf_fcfe', dict(cash_flow=920, shares=10,
                    growth=growth, terminal_growth=growth, discount_rate=.12))
                self.assertAlmostEqual(ddm['fair_value'], fcfe['fair_value'], places=9)

    def test_price_does_not_determine_intrinsic_value(self):
        inputs = dict(dividend=92, discount_rate=.12, terminal_growth=.01)
        low = calculate('ddm', dict(inputs, price=600))
        high = calculate('ddm', dict(inputs, price=1500))
        self.assertEqual(low['fair_value'], high['fair_value'])
        self.assertGreater(low['gap'], 0)
        self.assertLess(high['gap'], 0)
