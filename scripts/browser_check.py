"""Optional end-to-end QA against temporary data using installed Microsoft Edge.

Install playwright into runtime/qa_packages before running this development check.
No browser testing dependency is required to run the application.
"""
import json
import math
import shutil
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runtime/qa_packages"))
from playwright.sync_api import sync_playwright, expect
from backend import server
from backend.demo import demo_stock


def main():
    screenshots = ROOT / "runtime/browser-check"
    screenshots.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        test_root = Path(temporary)
        for folder in ["frontend", "brain", "policies", "examples"]:
            shutil.copytree(ROOT / folder, test_root / folder)
        (test_root / "scenarios").mkdir()
        # Use invented figures so a clean public checkout needs no private research.
        tel = server.read(test_root / "brain/TEL.toml")
        tel["fields"] = demo_stock()["fields"]
        tel["models"] = {"ddm":{"discount_rate":.12,"terminal_growth":.02},
                         "dcf_fcff":{"growth":.03}}
        tel['reports']={'review_status':'unresolved','review_note':'Temporary test: pending report reconciliation'}
        server.write(test_root / "brain/TEL.toml", tel)
        stock_count = len(list((test_root / "brain").glob("*.toml")))
        server.ROOT = test_root
        http = server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        worker = threading.Thread(target=http.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{http.server_port}"
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 1000})
                external_requests = []
                def route(request):
                    if request.request.url.startswith(base):
                        request.continue_()
                    else:
                        external_requests.append(request.request.url)
                        request.abort()
                context.route("**/*", route)
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base)
                page.locator("#search-results button").first.wait_for()
                page.locator('#check-all-stocks').click()
                expect(page.locator('#batch-review-results > details')).to_have_count(stock_count)
                page.locator('#batch-review-results > details').filter(has_text='TEL · PLDT').locator('summary').click()
                expect(page.locator('#batch-review-results')).to_contain_text('Illustrative scenario')
                with page.expect_download() as download_info:
                    page.locator('#export-batch-review').click()
                exported=json.loads(Path(download_info.value.path()).read_text(encoding='utf-8'))
                assert len(exported['companies'])==stock_count
                assert exported['policy_revision']
                page.locator('#close-batch-review').click()
                page.screenshot(path=str(screenshots / "welcome.png"), full_page=True)
                page.locator("#stock-search").fill("TEL")
                page.locator("#search-results button").filter(has_text="TEL ·").click()
                page.locator("#workspace").wait_for(state="visible")
                assert "PLDT" in page.locator("#company").inner_text()
                expect(page.locator("#method option")).to_have_count(5)
                expect(page.locator("#method-readiness")).to_contain_text("Prefilled")
                assert "cmpy_id=6" in page.get_by_role("link",name="PSE EDGE ↗",exact=True).get_attribute("href")
                page.locator("#method").select_option("ddm")
                page.locator("#input-discount_rate").fill("12")
                page.locator("#input-terminal_growth").fill("2")
                dividend = float(page.locator("#input-dividend").input_value())
                page.locator("#confirmed").check()
                page.get_by_role("button", name="Calculate fair value").click()
                page.locator(".fair-value").wait_for()
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                expect(page.locator('#sensitivity-field')).to_have_value('discount_rate')
                expect(page.locator('#input-readiness')).to_contain_text('Needs review')
                expect(page.locator('#input-readiness')).not_to_contain_text('Ready')
                expect(page.locator('#review-summary')).to_contain_text('Illustrative scenario')
                expect(page.locator('#input-checks')).to_contain_text('pending report reconciliation')
                expected = dividend * 1.02 / .1
                assert f"{expected:,.2f}" in page.locator(".fair-value").inner_text()
                page.locator("#sensitivity-field").select_option("discount_rate")
                page.locator("#sensitivity-low").fill("10")
                page.locator("#sensitivity-high").fill("14")
                page.locator("#sensitivity-run").click()
                expect(page.locator("#sensitivity-results tbody tr")).to_have_count(3)
                page.locator("#scenario-name").fill("TEL · illustrative dividend case")
                page.locator("#scenario-notes").fill("Demonstration only: 12% cost of equity and 2% growth. Imported dividend requires review.")
                page.locator("#save-scenario").click()
                expect(page.locator("#status")).to_contain_text("Analysis saved")
                page.screenshot(path=str(screenshots / "tel-analysis.png"), full_page=True)
                saved = list((test_root / "scenarios").glob("*.json"))
                assert len(saved) == 1
                record = json.loads(saved[0].read_text(encoding="utf-8"))
                assert abs(record["result"]["fair_value"] - expected) < .0001
                assert len(record["sensitivity"]["cases"]) == 3
                with page.expect_download() as download_info:
                    page.locator("#export-scenario").click()
                download = download_info.value
                exported = json.loads(Path(download.path()).read_text(encoding="utf-8"))
                assert exported["stock_snapshot"]["ticker"] == "TEL"
                assert exported["result"]["inputs"]["discount_rate"] == .12
                page.locator("#open-library").click()
                page.get_by_role("button", name="Load inputs", exact=True).click()
                expect(page.locator("#input-discount_rate")).to_have_value("12")
                assert not page.locator("#confirmed").is_checked()
                page.locator("#close-library").click()
                page.locator("#input-dividend").fill("100")
                assert page.locator("#save-scenario").is_disabled()
                assert not page.locator("#confirmed").is_checked()
                page.locator("#edit-stock").click()
                page.locator('#eps-evidence summary').click()
                for key,value in dict(annual_eps='10',current_ytd_eps='6',prior_ytd_eps='4',annual_end='2025-12-31',current_ytd_end='2026-06-30',prior_ytd_end='2025-06-30').items():
                    page.locator('#eps-'+key).fill(value)
                page.locator('#eps-use-total').click()
                expect(page.locator('#baseline-eps')).to_have_value('12')
                page.locator('#eps-review-status').select_option('reconciled')
                page.locator('#eps-reviewed_on').fill('2026-10-23')
                page.locator('#eps-review-note').fill('Synthetic fixture: stable share count and no restatements')
                page.locator("#baseline-shares").fill("216000000")
                page.locator("#baseline-date-shares").fill("2026-10-21")
                page.locator("#baseline-note-shares").fill("Browser QA edit; temporary data only")
                page.locator('#baseline-duration-shares').select_option('point_in_time')
                page.locator("#model-ddm-discount_rate").fill("13")
                page.locator('[data-model="ddm"] [data-model-note]').fill('Temporary research basis: return and growth scenarios explained')
                page.locator('[data-model="ddm"] [data-model-date]').fill('2026-10-22')
                page.locator('[data-model="ddm"] [data-model-evidence]').select_option('documented')
                page.locator('#reporting-status').select_option('reconciled')
                page.locator('#reporting-date').fill('2026-10-22')
                page.locator('#reporting-note').fill('Temporary test: revised figures reconciled')
                page.get_by_role("button", name="Save company data", exact=True).click()
                page.locator("#stock-editor").wait_for(state="hidden")
                updated = server.read(test_root / "brain/TEL.toml")
                expect(page.locator('#status')).to_contain_text('Changed financial inputs need a new review')
                assert updated['fields']['eps']['eps_bridge']['review_status']=='unreviewed'
                assert updated['fields']['eps']['value']==12
                assert updated["fields"]["shares"]["value"] == 216000000
                assert updated["models"]["ddm"]["discount_rate"] == .13
                assert list((test_root / "runtime/revisions").glob("*.json"))
                page.reload()
                page.locator("#stock-search").fill("TEL")
                page.locator("#search-results button").filter(has_text="TEL ·").click()
                page.locator("#edit-stock").click()
                assert page.locator("#baseline-shares").input_value() == "216000000"
                expect(page.locator('#baseline-duration-shares')).to_have_value('point_in_time')
                expect(page.locator('[data-model="ddm"] [data-model-note]')).to_have_value('Temporary research basis: return and growth scenarios explained')
                expect(page.locator('[data-model="ddm"] [data-model-evidence]')).to_have_value('documented')
                expect(page.locator('#reporting-status')).to_have_value('unresolved')
                # Changed facts cannot simultaneously clear an earlier reporting issue.
                # Re-review the now-saved inputs in a separate save.
                page.locator('#reporting-status').select_option('reconciled')
                page.locator('#eps-evidence summary').click()
                expect(page.locator('#eps-annual_eps')).to_have_value('10')
                expect(page.locator('#eps-review-status')).to_have_value('unreviewed')
                page.locator('#eps-review-status').select_option('reconciled')
                page.get_by_role('button',name='Save company data',exact=True).click()
                page.locator('#stock-editor').wait_for(state='hidden')
                assert server.read(test_root/'brain/TEL.toml')['fields']['eps']['eps_bridge']['review_status']=='reconciled'
                assert server.read(test_root/'brain/TEL.toml')['reports']['review_status']=='reconciled'
                page.locator('#edit-stock').click()
                page.locator('#eps-evidence summary').click()
                page.locator('#eps-annual_eps').fill('11')
                page.get_by_role('button',name='Save company data',exact=True).click()
                page.locator('#stock-editor').wait_for(state='hidden')
                assert server.read(test_root/'brain/TEL.toml')['fields']['eps']['eps_bridge']['review_status']=='unreviewed'
                page.locator("#method").select_option("ddm")
                expect(page.locator("#input-discount_rate")).to_have_value("13")
                page.locator("#advanced-methods").check()
                expect(page.locator("#method option")).to_have_count(14)
                page.locator("#advanced-methods").uncheck()
                expect(page.locator("#method option")).to_have_count(5)
                page.locator("#edit-policy").click()
                page.locator("#policy-default-growth").fill("4")
                page.get_by_role("button", name="Save policies", exact=True).click()
                page.locator("#policy-editor").wait_for(state="hidden")
                assert json.loads((test_root / "policies/catalog.json").read_text())["defaults"]["growth"] == .04
                page.locator("#method").select_option("dcf_fcff")
                expect(page.locator("#input-growth")).to_have_value("3")  # Company assumption takes precedence.
                page.locator("#rate-calculator > summary").click()
                page.locator("#rate-risk_free").fill("5")
                page.locator("#rate-beta").fill("1")
                page.locator("#rate-premium").fill("6")
                page.locator("#apply-rate").click()
                expect(page.locator("#input-discount_rate")).to_have_value("9.2750")
                page.locator("#input-cash_flow").fill("10000000000")
                page.locator("#input-net_debt").fill("20000000000")
                page.locator("#cash-helper > details > summary").click()
                page.locator("#cash-helper details details > summary").click()
                for key,value in {"receivables":10000,"inventory":6000,"payables":4000,"previous_receivables":8000,"previous_inventory":5000,"previous_payables":3000,"other_working_capital_change":0}.items():
                    page.locator(f"#derive-{key}").fill(str(value))
                page.locator("#derive-working-capital").click()
                expect(page.locator("#derive-working_capital_increase")).to_have_value("2000")
                for key,value in {"operating_profit":10000,"depreciation":1000,"capital_spending":3000,"additional_capex":0,"other_noncash":0}.items():
                    page.locator(f"#derive-{key}").fill(str(value))
                page.locator("#rate-tax").fill("")
                page.locator("#apply-derived-cash").click()
                expect(page.locator("#input-cash_flow")).to_have_value("10000000000")
                expect(page.locator("#status")).to_contain_text("blank is not zero")
                page.locator("#rate-tax").fill("25")
                page.locator("#apply-derived-cash").click()
                expect(page.locator("#input-cash_flow")).to_have_value("3500")
                page.locator("#rate-beta").fill("2")
                page.locator("#rate-tax").fill("10")
                page.locator("#confirmed").check()
                page.get_by_role("button", name="Calculate fair value").click()
                page.locator(".fair-value").wait_for()
                page.locator("#stock-search").fill("BDO")
                page.locator("#search-results button").filter(has_text="BDO ·").click()
                expect(page.locator("#method")).to_have_value("pb")
                expect(page.locator("#rate-beta")).to_have_value("1")
                expect(page.locator("#rate-tax")).to_have_value("25")
                folder = test_root / "reports/BDO"
                folder.mkdir(parents=True)
                (folder / "annual.txt").write_text("Operating profit 100,000 90,000\nTotal borrowings 50,000 40,000", encoding="utf-8")
                page.locator("#scan-reports").click()
                expect(page.locator("#report-file option")).to_have_count(1)
                page.locator("#report-period").fill("2026-12-31")
                page.locator("#run-import").click()
                expect(page.locator("#import-proposals tbody tr")).to_have_count(2)
                page.locator('#import-proposals input[type="checkbox"]').evaluate_all("items => items.forEach(item => item.click())")
                page.locator("#import-confirmed").check()
                page.locator("#apply-import").click()
                page.locator("#import-dialog").wait_for(state="hidden")
                assert server.read(test_root / "brain/BDO.toml")["fields"]["debt"]["value"] == 50000
                (folder/'notice.txt').write_text('A material weakness was identified. Review of the affected statements is ongoing.',encoding='utf-8')
                page.locator('#scan-reports').click()
                expect(page.locator('#report-file option')).to_have_count(2)
                page.locator('#report-file').select_option('notice.txt')
                page.locator('#run-import').click()
                expect(page.locator('#import-findings input[type="checkbox"]')).to_have_count(1)
                page.locator('#import-findings input[type="checkbox"]').check()
                page.locator('#import-confirmed').check()
                page.locator('#apply-import').click()
                page.locator('#import-dialog').wait_for(state='hidden')
                reviewed=server.read(test_root/'brain/BDO.toml')
                assert reviewed['reports']['review_status']=='unresolved'
                assert len(reviewed['reports']['disclosure_findings'])==1
                assert reviewed['fields']['debt']['value']==50000
                page.locator("#all-stocks").click()
                expect(page.locator("#search-results button")).to_have_count(stock_count)
                page.locator("#stock-search").fill("AREIT")
                page.locator("#search-results button").filter(has_text="AREIT ·").click()
                expect(page.locator("#method")).to_have_value("nav")
                expect(page.locator('label[for="input-asset_value"]')).to_contain_text("Reviewed gross asset value")
                expect(page.locator('label[for="input-liabilities"]')).to_contain_text("Liabilities and other claims against those assets")
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                expect(page.locator("#status")).to_have_text("", timeout=10000)
                page.screenshot(path=str(screenshots / "mobile.png"), full_page=False)
                assert not errors, errors
                assert not external_requests, external_requests
                server.write(test_root / "brain/DEMO.toml",demo_stock())
                page.set_viewport_size({"width":1440,"height":1000})
                page.reload()
                page.locator("#stock-search").fill("DEMO")
                page.locator("#search-results button").filter(has_text="DEMO ·").click()
                page.locator("#method").select_option("pe")
                page.locator("#confirmed").check()
                page.get_by_role("button",name="Calculate fair value").click()
                expect(page.locator(".fair-value")).to_contain_text("60.00")
                expect(page.locator('#sensitivity-field')).to_have_value('multiple')
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                page.locator('#input-price').fill('60')
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('#sensitivity-results')).to_contain_text('conclusion changes within this range')
                page.locator('#sensitivity-low').fill('0')
                page.locator('#sensitivity-run').click()
                expect(page.locator('#sensitivity-results')).to_contain_text('Sensitivity unavailable')
                expect(page.locator('.fair-value')).to_contain_text('60.00')
                page.locator('#sensitivity-low').fill('10.8')
                page.locator('#sensitivity-run').click()
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                expect(page.locator("#input-readiness")).not_to_have_text("")
                page.screenshot(path=str(screenshots / "portfolio-demo.png"),full_page=True)
                page.locator("#method").select_option("dcf_fcff")
                page.locator("#cash-helper > details > summary").click()
                page.locator("#apply-derived-cash").click()
                expect(page.locator("#input-cash_flow")).to_have_value("5000000")
                expect(page.locator("#input-net_debt")).to_have_value("2000000")
                page.locator("#confirmed").check()
                page.get_by_role("button",name="Calculate fair value").click()
                expect(page.locator(".fair-value")).to_contain_text("48.00")
                page.locator("#save-scenario").click()
                expect(page.locator("#status")).to_contain_text("Analysis saved")
                demo_saved=[json.loads(p.read_text(encoding='utf-8')) for p in (test_root/'scenarios').glob('*.json')]
                demo_saved=next(s for s in demo_saved if s['ticker']=='DEMO')
                assert len(demo_saved['derivations'])==2
                assert demo_saved['input_review']['fields']
                assert math.isclose(demo_saved['result']['steps'][-1]['value'],48)
                original_tel=(test_root/'brain/TEL.toml').read_bytes()
                page.locator('#try-tel-case').click()
                expect(page.locator('#input-dividend')).to_have_value('92')
                expect(page.locator('#input-price')).to_have_value('1190')
                expect(page.locator('#research-case')).to_contain_text('138.63')
                expect(page.locator('#research-case')).to_contain_text('132.38')
                assert not page.locator('#confirmed').is_checked()
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('.fair-value')).to_contain_text('844.73')
                expect(page.locator('#sensitivity-results tbody tr')).to_have_count(3)
                with page.expect_response(lambda r:r.url.endswith('/api/scenarios') and r.request.method=='POST') as research_save:
                    page.locator('#save-scenario').click()
                assert research_save.value.status==201
                research_saved=next(json.loads(p.read_text(encoding='utf-8')) for p in (test_root/'scenarios').glob('*.json') if json.loads(p.read_text(encoding='utf-8'))['name']=='TEL research case · 2026-10-22')
                assert 'annual_source_comparison' in research_saved['notes']
                assert (test_root/'brain/TEL.toml').read_bytes()==original_tel
                original_bdo=(test_root/'brain/BDO.toml').read_bytes()
                page.locator('#try-bdo-case').click()
                expect(page.locator('#method')).to_have_value('justified_pb')
                expect(page.locator('#input-bvps')).to_have_value('119.03')
                expect(page.locator('#research-case')).to_contain_text('not a contemporaneous trade or current target')
                expect(page.locator('#research-case')).to_contain_text('Additional distributions or capital release need support')
                expect(page.locator('#confirmed')).not_to_be_checked()
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('.fair-value')).to_contain_text('145.48')
                expect(page.locator('#result')).to_contain_text('not a declared dividend')
                expect(page.locator('#result')).to_contain_text('Next-year modeled distribution')
                assert 'property dividend' in page.locator('#scenario-notes').input_value()
                with page.expect_response(lambda response: response.url.endswith('/api/scenarios') and response.request.method=='POST') as bdo_save:
                    page.locator('#save-scenario').click()
                assert bdo_save.value.status==201
                bdo_saved=next(json.loads(p.read_text(encoding='utf-8')) for p in (test_root/'scenarios').glob('*.json') if json.loads(p.read_text(encoding='utf-8'))['name']=='BDO bank example · 2025-12-31')
                assert 'share_information' in bdo_saved['notes']
                assert abs(bdo_saved['result']['inputs']['roe']-.14)<1e-12
                assert (test_root/'brain/BDO.toml').read_bytes()==original_bdo
                page.locator('#try-demo').click()
                expect(page.locator('#research-case')).to_be_hidden()
                # Reconcile the same annual cash statement under both cash-flow models.
                page.locator('#advanced-methods').check()
                for model in ('dcf_fcff','dcf_fcfe'):
                    page.locator('#method').select_option(model)
                    page.locator('#cash-statement-helper summary').click()
                    entries=dict(operating_cash_flow=100,interest_paid=10,interest_outside_cfo=0,tax=25,
                                 capital_spending=30,additional_capex=5,cfo_adjustment=0,investment_adjustment=0)
                    entries.update(dict(debt=200,cash=40,other_claims=10) if model=='dcf_fcff' else dict(borrowings=20,repayments=12,common_adjustment=-3))
                    for key,value in entries.items(): page.locator('#bridge-'+key).fill(str(value))
                    page.locator('#bridge-period-type').select_option('annual')
                    page.locator('#bridge-period-end').fill('2025-12-31')
                    page.locator('#bridge-lease').select_option('none')
                    for key in ('source','scope','lease','adjustment'):
                        page.locator('#bridge-'+key+'-note').fill('Synthetic annual fixture; no leases; parent common equity; explicit adjustments.')
                    page.locator('#bridge-apply').click()
                    expect(page.locator('#input-cash_flow')).to_have_value('72.5' if model=='dcf_fcff' else '70')
                    if model=='dcf_fcff': expect(page.locator('#input-net_debt')).to_have_value('170')
                    expect(page.locator('#bridge-result')).to_contain_text('not independently verified')
                    with page.expect_response(lambda response: '/api/stocks/DEMO' in response.url and response.request.method=='POST') as baseline_save:
                        page.locator('#bridge-save').click()
                    assert baseline_save.value.status==200,baseline_save.value.text()
                    expect(page.locator('#bridge-result')).to_contain_text('Reporting review required')
                    baseline=baseline_save.value.json()['data']
                    saved_key='fcff_cash_flow' if model=='dcf_fcff' else 'fcfe_cash_flow'
                    assert baseline['fields'][saved_key]['cash_flow_reconciliation']['method']==model
                    assert baseline['reports']['review_status']=='unreviewed'
                for key,value in dict(shares=10,discount_rate=10,growth=0,terminal_growth=0).items():
                    page.locator('#input-'+key).fill(str(value))
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('.fair-value')).to_contain_text('70.00')
                page.locator('#scenario-name').fill('Cash statement reconciliation')
                with page.expect_response(lambda response: response.url.endswith('/api/scenarios') and response.request.method=='POST') as saved_response:
                    page.locator('#save-scenario').click()
                assert saved_response.value.status==201
                expect(page.locator('#status')).to_contain_text('Analysis saved')
                saved_records=[json.loads(p.read_text(encoding='utf-8')) for p in (test_root/'scenarios').glob('*.json')]
                bridge_saved=next(s for s in saved_records if s['name']=='Cash statement reconciliation')
                assert bridge_saved['derivations'][0]['reconciliation']['basis']['lease_treatment']=='none'
                assert bridge_saved['derivations'][0]['reconciliation']['cash_flow']==70
                page.locator('#method').select_option('pe')
                page.locator('#method').select_option('dcf_fcfe')
                page.locator('#cash-statement-helper summary').click()
                expect(page.locator('#bridge-operating_cash_flow')).to_have_value('100')
                expect(page.locator('#bridge-period-end')).to_have_value('2025-12-31')
                expect(page.locator('#bridge-save')).to_be_disabled()
                page.locator('#bridge-apply').click()
                expect(page.locator('#bridge-save')).to_be_enabled()
                page.locator('#bridge-capital_spending').fill('31')
                expect(page.locator('#bridge-save')).to_be_disabled()
                page.locator('#stock-search').fill('AC')
                page.locator('#search-results button').filter(has_text='AC ·').click()
                page.locator('#method').select_option('sotp')
                page.locator('#component-helper summary').click()
                row=page.locator('#component-rows fieldset').first
                row.locator('[data-component="basis"]').select_option('enterprise')
                for key,value in dict(name='Synthetic business',value=1000,net_claims=200,ownership=60,
                                      as_of='2025-12-31',source_note='Synthetic component fixture').items():
                    row.locator(f'[data-component="{key}"]').fill(str(value))
                page.locator('#component-apply').click()
                expect(page.locator('#input-asset_value')).to_have_value('480')
                for key,value in dict(liabilities=80,shares=10,discount=10).items():
                    page.locator('#input-'+key).fill(str(value))
                page.locator('#confirmed').check()
                page.get_by_role('button',name='Calculate fair value').click()
                expect(page.locator('.fair-value')).to_contain_text('36.00')
                page.locator('#scenario-name').fill('SOTP component evidence')
                with page.expect_response(lambda response: response.url.endswith('/api/scenarios') and response.request.method=='POST') as component_save:
                    page.locator('#save-scenario').click()
                assert component_save.value.status==201
                component_saved=next(json.loads(p.read_text(encoding='utf-8')) for p in (test_root/'scenarios').glob('*.json') if json.loads(p.read_text(encoding='utf-8'))['name']=='SOTP component evidence')
                assert component_saved['derivations'][0]['component_reconciliation']['components'][0]['ownership']==.6
                page.locator('#open-library').click()
                page.locator('.saved-item').filter(has_text='SOTP component evidence').get_by_role('button',name='Load inputs').click()
                page.locator('#component-helper summary').click()
                expect(page.locator('#component-rows [data-component="name"]')).to_have_value('Synthetic business')
                expect(page.locator('#component-rows [data-component="ownership"]')).to_have_value('60')
                page.locator('#component-apply').click()
                expect(page.locator('#component-save')).to_be_enabled()
                with page.expect_response(lambda response: response.url.endswith('/api/stocks/AC') and response.request.method=='POST') as component_baseline:
                    page.locator('#component-save').click()
                assert component_baseline.value.status==200,component_baseline.value.text()
                expect(page.locator('#component-result')).to_contain_text('baseline and evidence saved')
                persisted=server.read(test_root/'brain/AC.toml')
                assert persisted['fields']['asset_value']['sotp_components']['component_1']['ownership']==.6
                assert persisted['reports']['review_status']=='unreviewed'
                page.locator('#method').select_option('pe')
                page.locator('#method').select_option('sotp')
                page.locator('#component-helper summary').click()
                expect(page.locator('#component-rows [data-component="name"]')).to_have_value('Synthetic business')
                expect(page.locator('#component-save')).to_be_disabled()
                assert not errors,errors
                browser.close()
                print("PASS: TEL DDM/DCF, beta/WACC, saved sensitivity, export/load, input invalidation, baseline edit/reload, policy edit, BDO/REIT recommendations, mobile width, zero external requests and zero page errors")
        finally:
            http.shutdown()
            http.server_close()
            worker.join()


if __name__ == "__main__":
    main()
