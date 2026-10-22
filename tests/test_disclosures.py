import tempfile
import unittest
from pathlib import Path

from backend.disclosures import screen_passages
from backend.importer import document_candidates
from backend.brain import encode, decode


class DisclosureTests(unittest.TestCase):
    def test_flags_include_context_not_a_confirmed_conclusion(self):
        findings=screen_passages({7:'No material weakness was found. The audit opinions have been withdrawn. Prior financial statements were restated.'})
        self.assertEqual(len(findings),3)
        self.assertTrue(all(f['source_page']==7 for f in findings))
        self.assertTrue(any('No material weakness' in f['excerpt'] for f in findings))
        self.assertTrue(all('negated' in f['screening_note'] for f in findings))
        self.assertEqual(screen_passages({1:'Normal operating revenue and expense disclosure.'}),[])

    def test_findings_only_scan_does_not_invent_financial_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'disclosure.txt'
            file.write_text('The audit opinion was withdrawn. An independent review is ongoing.',encoding='utf-8')
            findings=[]
            rows,digest,warnings=document_candidates(file,findings=findings)
            self.assertEqual(rows,[])
            self.assertEqual(len(findings),1)
            self.assertEqual(len(digest),64)
            self.assertTrue(any('not extracted' in w for w in warnings))

    def test_nested_evidence_survives_brain_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/'TEST.toml'
            reports={'review_status':'unresolved','disclosure_findings':{'abc':{'category':'Possible restatement','source_page':7,'source_file':'report.pdf','source_hash':'123','excerpt':'Revised statements announced.'}}}
            file.write_text(encode({'ticker':'TEST','fields':{},'reports':reports}),encoding='utf-8')
            self.assertEqual(decode(file)['reports'],reports)

    def test_screening_is_bounded(self):
        findings=screen_passages({n:'Material weakness. Restated accounts. Audit opinion was withdrawn.' for n in range(100)})
        self.assertEqual(len(findings),20)
