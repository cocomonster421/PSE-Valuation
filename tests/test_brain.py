import tempfile
import unittest
from pathlib import Path

from backend.brain import stock_path, stock_paths
from backend.server import read, write, Handler, revision


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "brain/TEL.toml"
        self.data = {"ticker":"TEL", "name":"PLDT", "industry":"Telecom", "archetype":"TELECOM", "currency":"PHP",
                     "fields":{"dividend":{"value":92,"as_of":"2026-06-30","note":"Reviewed example"}, "shares":{"value":None}},
                     "models":{"ddm":{"discount_rate":.1085,"terminal_growth":.02,"note":"Assumption"}}}
        write(self.path, self.data)

    def tearDown(self):
        self.temp.cleanup()

    def test_read_write_preserves_values_and_assumptions(self):
        original = read(self.path)
        Handler.validate_stock(original,"TEL")
        write(self.path,original)
        self.assertEqual(revision(read(self.path)),revision(original))
        self.assertEqual(original["models"]["ddm"]["discount_rate"],.1085)
        self.assertIsNone(original["fields"]["shares"]["value"])

    def test_manual_file_change_is_authoritative(self):
        self.path.write_text(self.path.read_text(encoding="utf-8").replace("dividend = 92", "dividend = 100"),encoding="utf-8")
        self.assertEqual(read(self.path)["fields"]["dividend"]["value"],100)
        self.assertEqual(stock_path(self.root,"TEL"),self.path)
        self.assertEqual(stock_paths(self.root),[self.path])

    def test_reporting_and_assumption_evidence_round_trip(self):
        data=read(self.path)
        data['reports']={'review_status':'unresolved','reviewed_on':'2026-10-22','review_note':'Pending reconciliation'}
        data['models']['ddm'].update(evidence_status='documented',as_of='2026-10-22')
        data['fields']['dividend']['period_type']='ttm'
        Handler.validate_stock(data,'TEL')
        write(self.path,data)
        restored=read(self.path)
        self.assertEqual(restored['reports'],data['reports'])
        self.assertEqual(restored['models'],data['models'])
        self.assertEqual(restored['fields']['dividend']['period_type'],'ttm')
        data['reports']['review_status']='automatically_verified'
        with self.assertRaises(ValueError):
            Handler.validate_stock(data,'TEL')

    def test_nonfinite_or_text_value_rejected(self):
        content=self.path.read_text(encoding="utf-8")
        for value in ['nan', '"invalid"']:
            self.path.write_text(content.replace("dividend = 92",f"dividend = {value}"),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"TEL.toml"):
                read(self.path)

    def test_invalid_method_assumption_rejected(self):
        data=read(self.path)
        data["models"]["ddm"]["discount_rate"]="12%"
        with self.assertRaises(ValueError):
            Handler.validate_stock(data,"TEL")
