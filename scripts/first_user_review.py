"""Reproduce a fresh public-package walkthrough without changing company data."""
import json
import sys
import tempfile
import threading
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runtime/qa_packages'))
from playwright.sync_api import sync_playwright, expect


def main():
    evidence = ROOT / 'runtime/user-walkthrough'
    evidence.mkdir(parents=True, exist_ok=True)
    observations = {}
    with tempfile.TemporaryDirectory() as temporary:
        destination = Path(temporary)
        with ZipFile(ROOT / 'runtime/release/fundamental-valuation-workbench.zip') as package:
            package.extractall(destination)
        sys.path.insert(0, str(destination))
        from backend import server
        server.ROOT = destination
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True)
                page = browser.new_page(viewport={'width': 1440, 'height': 1000})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                base = f'http://127.0.0.1:{http.server_port}'
                external = []
                def route(request):
                    if request.request.url.startswith(base):
                        request.continue_()
                    else:
                        external.append(request.request.url)
                        request.abort()
                page.route('**/*', route)
                def select(ticker):
                    page.locator('#stock-search').fill(ticker)
                    page.locator('#search-results button').filter(has_text=ticker + ' ·').click()
                    expect(page.locator('#company')).to_contain_text(ticker)
                def calculate():
                    page.locator('#confirmed').check()
                    page.get_by_role('button', name='Calculate fair value').click()
                    page.locator('.fair-value').wait_for()
                    return page.locator('.fair-value').inner_text()
                def save(name):
                    page.locator('#scenario-name').fill(name)
                    with page.expect_response(lambda response: response.url.endswith('/api/scenarios') and response.request.method=='POST') as saved:
                        page.locator('#save-scenario').click()
                    assert saved.value.status==201
                    expect(page.locator('#status')).to_contain_text('Analysis saved')
                page.goto(base)
                page.locator('#search-results button').first.wait_for()
                expect(page.locator('#try-demo')).to_be_visible()
                page.locator('#try-demo').click()
                expect(page.locator('#company')).to_contain_text('DEMO')
                page.reload()
                page.locator('#search-results button').first.wait_for()
                observations['landing_text'] = page.locator('body').inner_text()
                page.screenshot(path=str(evidence / '01-start.png'), full_page=True)
                page.locator('#all-stocks').click()
                observations['stock_count'] = page.locator('#search-results button').count()
                select('URC')
                page.locator('#method').select_option('pe')
                observations['urc_missing'] = page.locator('#method-readiness').inner_text()
                page.locator('#confirmed').check()
                page.get_by_role('button', name='Calculate fair value').click()
                observations['empty_calculation_blocked'] = page.locator('.fair-value').count() == 0
                page.screenshot(path=str(evidence / '02-urc-empty.png'), full_page=True)
                page.locator('#scan-reports').click()
                expect(page.locator('#import-status')).to_contain_text('No reports found')
                expect(page.locator('#run-import')).to_be_disabled()
                expect(page.locator('#run-import')).to_have_text('Scan selected report')
                expect(page.locator('#import-folder')).to_contain_text(str(destination))
                observations['empty_report_dialog'] = page.locator('#import-dialog').inner_text()
                page.locator('#close-import').click()
                select('DEMO')
                page.locator('#method').select_option('pe')
                observations['pe_value'] = calculate()
                observations['pe_ratios'] = page.locator('#current-ratios').inner_text()
                expect(page.locator('.fair-value')).to_contain_text('60.00')
                page.locator('#input-multiple').fill('10')
                observations['pe_market_multiple_value'] = calculate()
                expect(page.locator('.fair-value')).to_contain_text('50.00')
                page.locator('#method').select_option('dcf_fcff')
                page.locator('#cash-helper > details > summary').click()
                page.locator('#apply-derived-cash').click()
                observations['derived_cash'] = page.locator('#input-cash_flow').input_value()
                observations['derived_claims'] = page.locator('#input-net_debt').input_value()
                observations['dcf_value'] = calculate()
                assert '5e+' not in page.locator('#result').inner_text()
                expect(page.locator('.fair-value')).to_contain_text('48.00')
                save('Review DCF')
                page.screenshot(path=str(evidence / '03-dcf.png'), full_page=True)
                page.reload()
                page.locator('#open-library').click()
                page.get_by_role('button', name='Load inputs', exact=True).click()
                expect(page.locator('#input-cash_flow')).to_have_value('5000000')
                page.locator('#close-library').click()
                observations['reopened_dcf_value'] = calculate()
                save('Review DCF reopened')
                records = [json.loads(p.read_text(encoding='utf-8')) for p in (destination / 'scenarios').glob('*.json')]
                observations['saved_derivation_counts'] = {r['name']: len(r.get('derivations', [])) for r in records}
                assert observations['saved_derivation_counts'] == {'Review DCF':2, 'Review DCF reopened':2}
                reopened = next(r for r in records if r['name']=='Review DCF reopened')
                assert all(d.get('origin') for d in reopened['derivations'])
                page.locator('#input-cash_flow').fill('6000000')
                observations['edited_dcf_value'] = calculate()
                expect(page.locator('.fair-value')).to_contain_text('58.00')
                save('Review DCF edited')
                edited = next(json.loads(p.read_text(encoding='utf-8')) for p in (destination/'scenarios').glob('*.json') if json.loads(p.read_text(encoding='utf-8'))['name']=='Review DCF edited')
                assert [d['output_field'] for d in edited['derivations']]==['net_debt']
                page.locator('#advanced-methods').check()
                page.locator('#method').select_option('affo')
                for field in page.locator('#fields input').all():
                    field.fill('5' if field.get_attribute('data-key') != 'multiple' else '12')
                observations['advanced_value'] = calculate()
                save('Review advanced')
                page.reload()
                page.locator('#open-library').click()
                page.locator('.saved-item').filter(has_text='Review advanced').get_by_role('button', name='Load inputs').click()
                expect(page.locator('#method')).to_have_value('affo')
                expect(page.locator('#advanced-methods')).to_be_checked()
                assert not page.locator('#confirmed').is_checked()
                page.locator('#close-library').click()
                observations['advanced_recalculated'] = calculate()
                page.locator('#input-multiple').fill('10')
                expect(page.locator('#save-scenario')).to_be_disabled()
                observations['advanced_edited'] = calculate()
                expect(page.locator('.fair-value')).to_contain_text('50.00')
                save('Review advanced edited')
                with page.expect_download() as download_info:
                    page.locator('#export-scenario').click()
                exported=json.loads(Path(download_info.value.path()).read_text(encoding='utf-8'))
                assert exported['result']['fair_value']==50
                observations['advanced_reopened_method'] = page.locator('#method').input_value()
                observations['page_errors'] = errors
                observations['external_requests'] = external
                assert not errors, errors
                assert not external, external
                page.screenshot(path=str(evidence / '04-reopen-advanced.png'), full_page=True)
                original_tel=(destination/'brain/TEL.toml').read_bytes()
                page.locator('#try-tel-case').click()
                expect(page.locator('#input-dividend')).to_have_value('92')
                expect(page.locator('#research-case')).to_contain_text('not a verified price target')
                expect(page.locator('#research-case')).to_contain_text('132.38')
                observations['tel_case_value']=calculate()
                expect(page.locator('.fair-value')).to_contain_text('844.73')
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                observations['tel_brain_unchanged']=(destination/'brain/TEL.toml').read_bytes()==original_tel
                assert observations['tel_brain_unchanged']
                assert observations['empty_calculation_blocked']
                assert not errors,errors
                assert not external,external
                page.screenshot(path=str(evidence/'05-tel-research.png'),full_page=True)
                original_bdo=(destination/'brain/BDO.toml').read_bytes()
                page.locator('#try-bdo-case').click()
                expect(page.locator('#method')).to_have_value('justified_pb')
                expect(page.locator('#research-case')).to_contain_text('not a contemporaneous trade or current target')
                expect(page.locator('#research-case')).to_contain_text('Additional distributions or capital release need support')
                observations['bdo_case_value']=calculate()
                expect(page.locator('.fair-value')).to_contain_text('145.48')
                save('Review BDO case')
                saved_bdo=next(json.loads(p.read_text(encoding='utf-8')) for p in (destination/'scenarios').glob('*.json') if json.loads(p.read_text(encoding='utf-8'))['name']=='Review BDO case')
                assert 'common_equity_reconciliation' in saved_bdo['notes']
                assert 'dividend_policy_check' in saved_bdo['notes']
                observations['bdo_brain_unchanged']=(destination/'brain/BDO.toml').read_bytes()==original_bdo
                assert observations['bdo_brain_unchanged']
                page.screenshot(path=str(evidence/'06-bdo-research.png'),full_page=True)
                assert not errors,errors
                assert not external,external
                browser.close()
        finally:
            http.shutdown()
            http.server_close()
            worker.join()
    (evidence / 'results.json').write_text(json.dumps(observations, indent=2), encoding='utf-8')
    print(json.dumps(observations, indent=2))


if __name__ == '__main__':
    main()
