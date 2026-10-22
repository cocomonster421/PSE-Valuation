"""Public packages remain self-contained when rebuilt from a public checkout."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from backend.brain import encode, decode
from backend.demo import demo_stock
from scripts import package_project


class ReleaseTests(unittest.TestCase):
    def test_public_rebuild_has_unique_demo_and_blank_company(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'brain').mkdir()
            (root / 'brain/DEMO.toml').write_text(encode(demo_stock()), encoding='utf-8')
            company = demo_stock()
            company['ticker'] = 'TEST'
            (root / 'brain/TEST.toml').write_text(encode(company), encoding='utf-8')
            with patch.object(package_project, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                package_project.main()
            with ZipFile(root / 'runtime/release/fundamental-valuation-workbench.zip') as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertIn('reports/DEMO/.gitkeep', names)
                archive.extractall(root / 'extracted')
            self.assertEqual(decode(root / 'extracted/brain/DEMO.toml')['fields']['eps']['value'], 5)
            blank = decode(root / 'extracted/brain/TEST.toml')
            self.assertTrue(all(field['value'] is None for field in blank['fields'].values()))
            self.assertEqual(blank['models'], {})
