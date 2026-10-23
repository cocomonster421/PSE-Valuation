import tempfile
import unittest
from pathlib import Path
from backend.importer import edge_financials, document_candidates, number


HTML = '''<div id="contents"><h3>Annual</h3><p>For the fiscal year ended : Dec 31, 2025</p><p>Currency: PHP</p><table class="view"><tr><th>Earnings/(Loss) Per Share (Basic)</th><td>4.77</td><td>5.39</td></tr><tr><th>Book Value Per Share</th><td>57.96</td><td>55.79</td></tr></table><h3>Quarterly</h3><p>For the period ended : Jun 30, 2026</p><p>Currency: PHP'000</p><table class="view"><tr><th>Earnings/(Loss) Per Share (Basic)</th><td>1.38</td><td>1.04</td><td>3.23</td><td>2.93</td></tr><tr><th>Book Value Per Share</th><td>59.47</td><td>57.96</td></tr></table></div>'''


class ImporterTests(unittest.TestCase):
    def test_ttm_uses_ytd_not_quarter_and_does_not_scale_eps(self):
        rows={r["key"]:r for r in edge_financials(HTML,"official")}
        self.assertAlmostEqual(rows["eps"]["value"],5.07)
        self.assertAlmostEqual(rows["bvps"]["value"],59.47)
        self.assertEqual(rows["eps"]["period_end"],"2026-06-30")
        self.assertEqual(rows['eps']['period_type'],'ttm')
        self.assertEqual(rows['bvps']['period_type'],'point_in_time')

    def test_ttm_component_evidence_survives_brain_roundtrip(self):
        from backend.brain import encode, decode
        row=next(r for r in edge_financials(HTML,"official") if r['key']=='eps')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'TEST.toml'
            path.write_text(encode({'ticker':'TEST','fields':{'eps':row}}),encoding='utf-8')
            self.assertEqual(decode(path)['fields']['eps']['eps_bridge'],row['eps_bridge'])

    def test_ttm_review_requires_comparability_and_replays_components(self):
        from datetime import date
        from backend.review import eps_bridge_issues
        row=next(r for r in edge_financials(HTML,"official") if r['key']=='eps')
        today=date(2026,7,1)
        self.assertTrue(any('provisional' in i for i in eps_bridge_issues(row,today)))
        row['eps_bridge'].update(review_status='reconciled',reviewed_on='2026-07-01',
                                review_note='Synthetic fixture: common share basis unchanged; no revisions.')
        self.assertEqual(eps_bridge_issues(row,today),[])
        row['eps_bridge']['annual_eps']=99
        self.assertTrue(any('arithmetic' in i for i in eps_bridge_issues(row,today)))
        row['eps_bridge']['annual_eps']=4.77
        row['eps_bridge']['prior_ytd_end']='2024-06-30'
        self.assertTrue(any('periods' in i for i in eps_bridge_issues(row,today)))

    def test_ttm_legacy_and_expired_evidence_stay_flagged(self):
        from datetime import date
        from backend.review import eps_bridge_issues
        self.assertTrue(eps_bridge_issues({'period_type':'ttm'},date(2026,7,1)))
        row=next(r for r in edge_financials(HTML,"official") if r['key']=='eps')
        row['eps_bridge'].update(review_status='reconciled',reviewed_on='2025-01-01',review_note='Old review')
        self.assertTrue(eps_bridge_issues(row,date(2026,7,1)))

    def test_nonmatching_periods_do_not_create_ttm(self):
        html=HTML.replace("Jun 30, 2026","Jun 30, 2027")
        rows={r["key"]:r for r in edge_financials(html,"official")}
        self.assertAlmostEqual(rows["eps"]["value"],4.77)
        self.assertEqual(rows['eps']['period_type'],'annual')

    def test_non_quarter_end_does_not_create_ttm(self):
        rows={r['key']:r for r in edge_financials(HTML.replace('Jun 30, 2026','Jun 15, 2026'),'official')}
        self.assertEqual(rows['eps']['period_type'],'annual')
        self.assertAlmostEqual(rows['eps']['value'],4.77)

    def test_foreign_currency_summary_is_rejected(self):
        with self.assertRaises(ValueError):edge_financials(HTML.replace("PHP","USD"),"official")

    def test_local_text_requires_period_and_preserves_units_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"annual.txt"
            file.write_text("Operating profit 100,000\nDepreciation and amortization 20,000\n",encoding="utf-8")
            with self.assertRaises(ValueError):document_candidates(file)
            rows,digest,warnings=document_candidates(file,"2025-12-31",1000)
            self.assertEqual(rows[0]["value"],100000000)
            self.assertEqual(len(digest),64)
            self.assertTrue(warnings)
            self.assertEqual(rows[0]['period_type'],'unknown')
            self.assertNotIn('User-confirmed annual',rows[0]['period_basis'])

    def test_repeated_pdf_style_rows_are_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"annual.txt"
            file.write_text("Cash and cash equivalents 1,000\nCash and cash equivalents 2,000",encoding="utf-8")
            rows,_,_=document_candidates(file,"2025-12-31",1)
            self.assertFalse(rows)

    def test_accounting_negative_number(self):
        self.assertEqual(number("(1,234.5)"),-1234.5)

    def test_note_tags_and_concatenated_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"annual.txt"
            file.write_text("Depreciation and amortization (Note 24) 5,958,173 4,987,520\nOperating income 16,129,744,06116,652,038,589 17,388,611,632",encoding="utf-8")
            rows,_,_=document_candidates(file,"2025-12-31",1)
            self.assertEqual([r['key'] for r in rows],['depreciation'])
            self.assertEqual(rows[0]['source_page'],1)
            self.assertIn('Note 24',rows[0]['source_row'])

    def test_interim_and_scale_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"quarter.txt"
            file.write_text("In Thousand Pesos\nSix Months Ended June 30\nOperating profit 100,000 90,000",encoding="utf-8")
            with self.assertRaises(ValueError): document_candidates(file,"2026-06-30",1)
            rows,_,warnings=document_candidates(file,"2026-06-30",1000)
            self.assertFalse(rows)
            self.assertTrue(any('Interim' in w for w in warnings))

    def test_unicode_negative_and_ambiguous_report_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"annual.txt"
            file.write_text("Operating profit −100,000",encoding="utf-8")
            rows,_,_=document_candidates(file,"2025-12-31",1000)
            self.assertEqual(rows[0]["value"],-100000000)
            for text in ["Operating profit 12 100,000", "Operating profit 2025 100,000 90,000", "Cash and cash equivalents at beginning of year 100,000", "Operating profit Note 12 100,000"]:
                file.write_text(text,encoding="utf-8")
                self.assertEqual(document_candidates(file,"2025-12-31",1)[0],[],text)

    def test_working_capital_balances_include_previous_column(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"annual.txt"
            file.write_text("Trade receivables 10,000 8,000\nInventories 6,000 5,000\nTrade payables 4,000 3,000",encoding="utf-8")
            rows,_,_=document_candidates(file,"2025-12-31",1000)
            values={row['key']:row['value'] for row in rows}
            self.assertEqual(len(values),6)
            self.assertEqual(values['receivables'],10000000)
            self.assertEqual(values['previous_receivables'],8000000)
