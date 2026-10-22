"""Capture the dated TEL research example using a temporary company-data copy."""
import json
import shutil
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime/qa_packages'))
from playwright.sync_api import sync_playwright, expect
from backend import server


def main():
    case = json.loads((ROOT / 'examples/tel_case.json').read_text(encoding='utf-8'))
    output = ROOT / 'docs/screenshots'
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for name in ('frontend', 'brain', 'policies'):
            shutil.copytree(ROOT / name, root / name)
        (root / 'scenarios').mkdir()
        stock = server.read(root / 'brain/TEL.toml')
        stock['fields']['price'] = {'value':1190, 'as_of':case['price']['as_of'],
            'status':'historical', 'source_url':case['price']['source_url'],
            'note':'Research snapshot: 22 October 2026, 14:50 Asia/Manila. Last traded price, not a closing price or live quote.'}
        stock['fields']['dividend'] = {'value':92, 'as_of':'2026-09-11', 'period_end':'2026-09-11',
            'status':'reviewed', 'source_url':case['reported']['dividend_source_url'],
            'note':'Common dividends paid over the last twelve months: PHP 46 in April 2026 + PHP 46 in September 2026 = PHP 92. Distinct from FY2025 earnings-year dividend of PHP 94. Maintenance is an assumption.'}
        stock['models'] = {'ddm': {'discount_rate':.12, 'terminal_growth':.01,
            'as_of':case['analysis_date'], 'note':'Dated TEL research case: 12% chosen equity-return hurdle, not a measured CAPM estimate; 1% perpetual dividend growth is a conservative scenario, not guidance.'}}
        server.write(root / 'brain/TEL.toml', stock)
        server.ROOT = root
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True)
                page = browser.new_page(viewport={'width':1440,'height':1250}, device_scale_factor=1)
                base = f'http://127.0.0.1:{http.server_port}'
                page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base)
                page.locator('#stock-search').fill('TEL')
                page.locator('#search-results button').filter(has_text='TEL ·').click()
                page.locator('#method').select_option('ddm')
                page.locator('#scenario-name').fill('TEL · 22 Oct 2026 · dividend case')
                page.locator('#scenario-notes').fill('LTM dividend: 46 + 46 = PHP 92. Equity-return hurdle 12%; growth 1%. See docs/TEL_CASE_STUDY.md for source links, sensitivity and risks. Price is a dated intraday snapshot.')
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('.fair-value')).to_contain_text('844.73')
                page.evaluate('window.scrollTo(0, 0)')
                page.screenshot(path=str(output / 'tel-overview.png'))
                page.locator('#sensitivity-field').select_option('discount_rate')
                page.locator('#sensitivity-low').fill('10')
                page.locator('#sensitivity-high').fill('14')
                page.locator('#sensitivity-run').click()
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                page.locator('.result-panel').screenshot(path=str(output / 'tel-sensitivity.png'))
                for details in page.locator('#fields .field-help').all():
                    details.locator('summary').click()
                page.locator('#fields').screenshot(path=str(output / 'tel-sources.png'))
                assert not errors, errors
                browser.close()
        finally:
            http.shutdown()
            http.server_close()
            worker.join()
    print('Captured TEL overview, sensitivity and source notes from temporary dated research inputs.')


if __name__ == '__main__':
    main()
