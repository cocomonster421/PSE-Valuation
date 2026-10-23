import unittest

from scripts.replay_tel_case import replay


class TelCaseTests(unittest.TestCase):
    def test_published_case_and_sensitivity_reproduce(self):
        case = replay()
        self.assertAlmostEqual(case['result']['fair_value'], 844.7272727272727)
        self.assertAlmostEqual(case['ttm_eps'], 133.89)
        # At fixed growth a higher return hurdle reduces value.
        middle = [row['values'][1] for row in case['sensitivity']]
        self.assertEqual(middle, sorted(middle, reverse=True))
        for row in case['sensitivity']:
            self.assertEqual(row['values'], sorted(row['values']))
        all_values = [value for row in case['sensitivity'] for value in row['values']]
        self.assertEqual(max(all_values), 1173)
        self.assertLess(max(all_values), case['result']['inputs']['price'])

    def test_period_specific_source_cross_checks(self):
        case = replay()
        events = case['dividend_schedule']
        self.assertEqual([e['payment_date'] for e in events], ['2026-04-16','2026-09-11'])
        self.assertEqual(sum(e['amount_per_share'] for e in events),92)
        interim = case['interim_cross_check']
        self.assertEqual(interim['h1_2026']['lease_settlements_million'],7835)
        self.assertEqual(interim['h1_2025']['lease_settlements_million'],6944)
        self.assertEqual(interim['h1_2026']['cash_after_capex_before_remaining_adjustments'],22040)
        self.assertEqual(interim['h1_2025']['cash_after_capex_before_remaining_adjustments'],12627)
