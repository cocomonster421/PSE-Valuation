import copy
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from pathlib import Path

from backend import server
from backend.catalog import initial_policy


class LocalAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.original_root = server.ROOT
        server.ROOT = Path(cls.directory.name)
        server.write(server.ROOT / "policies/catalog.json", initial_policy())
        server.write(server.ROOT / "stock_data/TEL.json", {
            "ticker": "TEL", "name": "PLDT", "industry": "Telecommunications",
            "currency": "PHP", "fields": {"dividend": {"value": 10, "as_of": "2025-12-31", "note": "Test fixture"}}})
        (server.ROOT / "scenarios").mkdir()
        cls.http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.http.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        server.ROOT = cls.original_root
        cls.directory.cleanup()

    def request(self, path, data=None, origin=True):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = self.base
        req = urllib.request.Request(self.base + path, None if data is None else json.dumps(data).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, json.load(error)

    def test_calculation_and_confirmation(self):
        body = {"method": "ddm", "inputs": {"dividend": 10, "discount_rate": .12, "terminal_growth": .02}}
        self.assertEqual(self.request("/api/calculate", body)[0], 400)
        body["confirmed"] = True
        code, result = self.request("/api/calculate", body)
        self.assertEqual(code, 200)
        self.assertAlmostEqual(result["fair_value"], 102)

    def test_import_invalidates_review_but_preserves_unresolved_issues(self):
        for index, status in enumerate(('reviewed','reconciled','unresolved','unreviewed')):
            with self.subTest(status=status):
                ticker=f'REVIEW{index}'
                reports={'review_status':status,'reviewed_on':'2026-10-22','review_note':'Prior review: revisions need reconciliation'}
                stock={'ticker':ticker,'name':'Review fixture','industry':'Test','currency':'PHP','fields':{},'reports':reports}
                server.write(server.ROOT / f'stock_data/{ticker}.json',stock)
                folder=server.ROOT / f'reports/{ticker}'
                folder.mkdir(parents=True)
                (folder/'annual.txt').write_text('Operating profit 100,000',encoding='utf-8')
                code,preview=self.request(f'/api/update/{ticker}',dict(mode='offline',file='annual.txt',period='2026-06-30',scale=1))
                self.assertEqual(code,200)
                # Preview alone must not invalidate a review.
                self.assertEqual(self.request(f'/api/stocks/{ticker}')[1]['data']['reports'],reports)
                code,outcome=self.request('/api/update-apply',dict(token=preview['token'],selected=['0'],confirmed=True))
                self.assertEqual(code,200)
                self.assertTrue(outcome['reporting_review_required'])
                current=self.request(f'/api/stocks/{ticker}')[1]['data']['reports']
                self.assertEqual(current['review_status'],'unresolved' if status=='unresolved' else 'unreviewed')
                self.assertEqual(current['review_note'],reports['review_note'])
                self.assertEqual(current['reviewed_on'],reports['reviewed_on'])
                self.assertEqual(current['invalidated_fields'],['operating_profit'])
                checked=self.request('/api/review',dict(ticker=ticker,method='pe',inputs={'eps':5,'multiple':10}))[1]
                self.assertTrue(any('Financial inputs imported' in issue for issue in checked['issues']))

    def test_price_only_refresh_preserves_financial_review(self):
        ticker='PRICEONLY'
        reports={'review_status':'reviewed','reviewed_on':'2026-10-22','review_note':'Reviewed filings'}
        server.write(server.ROOT / f'stock_data/{ticker}.json',dict(ticker=ticker,name='Price fixture',industry='Test',currency='PHP',fields={},reports=reports))
        rows=[dict(key='price',value=100,as_of='2026-10-23',note='Mock price source')]
        with patch.object(server,'refresh_candidates',return_value=(rows,[])):
            code,preview=self.request(f'/api/update/{ticker}',{'mode':'online'})
        self.assertEqual(code,200)
        code,outcome=self.request('/api/update-apply',dict(token=preview['token'],selected=['0'],confirmed=True))
        self.assertEqual(code,200)
        self.assertFalse(outcome['reporting_review_required'])
        self.assertEqual(self.request(f'/api/stocks/{ticker}')[1]['data']['reports'],reports)

    def test_cross_origin_write_rejected(self):
        self.assertEqual(self.request("/api/scenarios", {}, origin=False)[0], 403)

    def test_mixed_report_folder_requires_individual_selection(self):
        server.write(server.ROOT / "stock_data/TEST.json", {"ticker":"TEST","name":"Fixture","industry":"Test","currency":"PHP","fields":{}})
        folder=server.ROOT / "reports/TEST"
        folder.mkdir(parents=True)
        (folder/"older.txt").write_text("Operating profit 100,000",encoding="utf-8")
        (folder/"newer.txt").write_text("Operating profit 500,000",encoding="utf-8")
        body={"mode":"offline","period":"2025-12-31","scale":1000}
        self.assertEqual(self.request("/api/update/TEST",body)[0],400)
        body["file"]="newer.txt"
        code,preview=self.request("/api/update/TEST",body)
        self.assertEqual(code,200)
        self.assertEqual(len(preview["candidates"]),1)
        self.assertEqual(preview["candidates"][0]["value"],500000000)
        self.assertEqual(preview["candidates"][0]["source_file"],"newer.txt")

    def test_report_review_apply_and_deduplication(self):
        folder = server.ROOT / "reports/TEL"
        folder.mkdir(parents=True, exist_ok=True)
        report = folder / "sample.txt"
        report.write_text("Operating profit 100,000 90,000", encoding="utf-8")
        body = {"mode": "offline", "period": "2026-12-31", "scale": 1000}
        code, preview = self.request("/api/update/TEL", body)
        self.assertEqual(code, 200)
        self.assertEqual(preview["candidates"][0]["value"], 100000000)
        apply = {"token": preview["token"], "selected": ["0"]}
        self.assertEqual(self.request("/api/update-apply", apply)[0], 400)
        apply["confirmed"] = True
        report.write_text("Operating profit 200,000 90,000", encoding="utf-8")
        self.assertEqual(self.request("/api/update-apply", apply)[0], 400)
        _, preview = self.request("/api/update/TEL", body)
        apply["token"] = preview["token"]
        self.assertEqual(self.request("/api/update-apply", apply)[0], 200)
        _, current = self.request("/api/stocks/TEL")
        self.assertEqual(current["data"]["fields"]["operating_profit"]["value"], 200000000)
        _, preview = self.request("/api/update/TEL", body)
        self.assertEqual(preview["candidates"], [])
        report.write_text("Operating profit 300,000 90,000", encoding="utf-8")
        body["period"] = "2025-12-31"
        _, preview = self.request("/api/update/TEL", body)
        apply["token"] = preview["token"]
        self.assertEqual(self.request("/api/update-apply", apply)[0], 400)

    def test_save_snapshot_and_replay(self):
        body = {"ticker": "TEL", "method": "pe", "inputs": {"eps": 10, "multiple": 12}, "confirmed": True, "name": "Test thesis"}
        code, saved = self.request("/api/scenarios", body)
        self.assertEqual(code, 201)
        self.assertEqual(saved["stock_snapshot"]["name"], "PLDT")
        self.assertEqual(saved["result"]["fair_value"], 120)
        self.assertEqual(saved["policy_snapshot"], initial_policy())
        code, replay = self.request("/api/calculate", {"method": saved["result"]["method"], "inputs": saved["result"]["inputs"], "confirmed": True})
        self.assertEqual(replay, saved["result"])

    def test_baseline_conflict_and_backup(self):
        _, current = self.request("/api/stocks/TEL")
        changed = copy.deepcopy(current)
        changed["data"]["fields"]["dividend"]["value"] = 11
        self.assertEqual(self.request("/api/stocks/TEL", changed)[0], 200)
        self.assertEqual(self.request("/api/stocks/TEL", current)[0], 409)
        backups = list((server.ROOT / "runtime/revisions").glob("*.json"))
        self.assertTrue(backups)
        self.assertEqual(server.read(backups[0])["fields"]["dividend"]["value"], 10)

    def test_formula_contract_cannot_be_removed(self):
        _, current = self.request("/api/policy")
        current["data"]["methods"]["dcf_fcff"]["fields"].remove("net_debt")
        self.assertEqual(self.request("/api/policy", current)[0], 400)

    def test_policy_cannot_reinterpret_rate_units(self):
        _, current = self.request("/api/policy")
        current["data"]["fields"]["discount_rate"]["unit"] = "PHP"
        self.assertEqual(self.request("/api/policy", current)[0], 400)

    def test_save_rejects_changed_source_revision(self):
        body = {"ticker": "TEL", "method": "pe", "inputs": {"eps": 10, "multiple": 12},
                "confirmed": True, "stock_revision": "obsolete"}
        self.assertEqual(self.request("/api/scenarios", body)[0], 409)

    def test_malformed_payload_returns_error(self):
        for body in [[], {"method": "pe", "inputs": [], "confirmed": True}]:
            self.assertEqual(self.request("/api/calculate", body)[0], 400)

    def test_broken_stock_file_does_not_break_other_stocks(self):
        path = server.ROOT / "stock_data/BROKEN.json"
        path.write_text("{invalid", encoding="utf-8")
        try:
            code, stocks = self.request("/api/stocks")
            self.assertEqual(code, 200)
            self.assertTrue(any(s["ticker"] == "TEL" for s in stocks))
            self.assertEqual(self.request("/api/stocks/BROKEN")[0], 422)
            self.assertEqual(self.request("/api/stocks/TEL")[0], 200)
        finally:
            path.unlink()

    def test_nonfinite_local_file_has_actionable_error(self):
        path = server.ROOT / "stock_data/BAD.json"
        path.write_text('{"value": NaN}', encoding="utf-8")
        try:
            code, error = self.request("/api/stocks/BAD")
            self.assertEqual(code, 422)
            self.assertIn("BAD.json", error["error"])
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
