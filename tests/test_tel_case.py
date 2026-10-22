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
