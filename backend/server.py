"""Loopback-only, standard-library server. No internet or external runtime required."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import socket
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer as BaseThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from backend.catalog import METHODS, initial_policy
from backend.engine import calculate, compare, ENGINE_VERSION
from backend.brain import decode as read_brain, encode as encode_brain, stock_path, stock_paths
from backend.importer import document_candidates, refresh_candidates
from backend.review import review_inputs, same_period_conflict
from backend.batch_review import review_company
from backend.cash_flow import reconcile_cash_flow
from backend.components import reconcile_components

ROOT = Path(__file__).resolve().parents[1]
LOCK = threading.Lock()


class ThreadingHTTPServer(BaseThreadingHTTPServer):
    # Windows SO_REUSEADDR can allow a second process to take the same port.
    allow_reuse_address = os.name != "nt"
    allow_reuse_port = False

    def server_bind(self):
        if os.name=="nt":
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()


def read(path):
    if path.suffix == ".toml":
        return read_brain(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite number")))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data
    except (ValueError, UnicodeError) as error:
        raise ValueError(f"Repair {path.name}: {error}") from error


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(encode_brain(data) if path.suffix == ".toml" else json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def revision(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def safe_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise ValueError("Invalid record identifier")
    return value


class Handler(BaseHTTPRequestHandler):
    def send(self, status, value, content_type="application/json; charset=utf-8"):
        payload = json.dumps(value, allow_nan=False).encode() if content_type.startswith("application/json") else value
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            # Navigation can cancel a request after processing has completed.
            self.close_connection = True

    def valid_host(self):
        return self.headers.get("Host") in {f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}"}

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {"error": "Use the localhost address"})
        path = urlsplit(self.path).path
        try:
            if path == "/api/examples/tel":
                return self.send(200,read(ROOT / "examples/tel_case.json"))
            if path == "/api/examples/bdo":
                return self.send(200,read(ROOT / "examples/bdo_case.json"))
            if path == "/api/review-all":
                policy=read(ROOT / "policies/catalog.json")
                self.validate_policy(policy)
                checked_at=datetime.now(timezone.utc)
                rows=[]
                for file in stock_paths(ROOT):
                    try:
                        stock=read(file)
                        self.validate_stock(stock,file.stem)
                        row=review_company(stock,policy,today=checked_at.astimezone().date())
                        row["stock_revision"]=revision(stock)
                    except (ValueError,TypeError,KeyError,AttributeError,OSError) as error:
                        row={"ticker":file.stem,"name":"File needs repair","error":str(error),"methods":[]}
                    rows.append(row)
                return self.send(200,{"checked_at":checked_at.isoformat(),"engine_version":ENGINE_VERSION,
                    "policy_revision":revision(policy),"companies":rows,
                    "scope":"Local saved inputs and policy defaults; recommended methods, or all methods when no recommendation exists. No online requests. A calculated value is not a verified target."})
            if path.startswith("/api/reports/"):
                ticker=safe_id(path.rsplit("/",1)[1])
                read(stock_path(ROOT,ticker))
                folder=ROOT/"reports"/ticker
                folder.mkdir(parents=True,exist_ok=True)
                return self.send(200,{"folder":str(folder.resolve()),"files":[p.name for p in sorted(folder.iterdir()) if p.is_file() and not p.is_symlink() and p.suffix.lower() in {".pdf",".html",".htm",".txt"}]})
            if path.startswith("/api/brains/"):
                ticker = safe_id(path.rsplit("/", 1)[1])
                file = stock_path(ROOT, ticker)
                company = read(file)
                return self.send(200, file.read_bytes() if file.suffix == ".toml" else encode_brain(company).encode("utf-8"), "text/plain; charset=utf-8")
            if path == "/api/stocks":
                stocks = []
                for p in stock_paths(ROOT):
                    try:
                        data = read(p)
                        self.validate_stock(data, p.stem)
                        stocks.append(data)
                    except (ValueError, TypeError, KeyError):
                        stocks.append({"ticker": p.stem, "name": "File needs repair", "industry": "Unavailable", "archetype": "Unavailable"})
                return self.send(200, [{k: s.get(k) for k in ("ticker", "name", "industry", "archetype")} for s in stocks])
            if path.startswith("/api/stocks/"):
                data = read(stock_path(ROOT, safe_id(path.rsplit('/', 1)[1])))
                self.validate_stock(data, path.rsplit('/', 1)[1])
                return self.send(200, {"data": data, "revision": revision(data)})
            if path == "/api/policy":
                data = read(ROOT / "policies/catalog.json")
                self.validate_policy(data)
                return self.send(200, {"data": data, "revision": revision(data)})
            if path == "/api/scenarios":
                scenarios = []
                for p in sorted((ROOT / "scenarios").glob("*.json")):
                    try:
                        saved = read(p)
                        if not isinstance(saved.get("result"), dict) or not {"ticker", "id", "name", "saved_at", "notes"} <= saved.keys():
                            raise ValueError("Invalid saved analysis")
                        scenarios.append(saved)
                    except (ValueError, TypeError):
                        return self.send(422, {"error": f"Repair or move the invalid saved analysis {p.name}; other data is unchanged."})
                return self.send(200, scenarios)
            if path == "/api/health":
                return self.send(200, {"status": "ok", "mode": "offline", "engine": ENGINE_VERSION})
            static = {"/": ("index.html", "text/html; charset=utf-8"),
                      "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                      "/styles.css": ("styles.css", "text/css; charset=utf-8")}
            if path in static:
                file, mime = static[path]
                return self.send(200, (ROOT / "frontend" / file).read_bytes(), mime)
            self.send(404, {"error": "Not found"})
        except FileNotFoundError as error:
            self.send(404, {"error": str(error)})
        except (ValueError, TypeError, KeyError) as error:
            self.send(422, {"error": str(error)})
        except OSError:
            self.send(500, {"error": "Cannot read the local file. Check file permissions and try again."})

    def do_POST(self):
        origin = self.headers.get("Origin")
        allowed = {f"http://localhost:{self.server.server_port}", f"http://127.0.0.1:{self.server.server_port}"}
        if not self.valid_host() or origin not in allowed or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send(403, {"error": "Writes require a same-origin local JSON request"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                raise ValueError("Request must be between 1 byte and 2 MB")
            payload = json.loads(self.rfile.read(length), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
            if not isinstance(payload, dict):
                raise ValueError("Request must be a JSON object")
            path = urlsplit(self.path).path
            if path == '/api/reconcile-cash':
                return self.send(200,reconcile_cash_flow(payload['method'],payload['inputs'],payload['basis']))
            if path == '/api/reconcile-components':
                return self.send(200,reconcile_components(payload['components']))
            if path=="/api/review":
                stock=read(stock_path(ROOT,safe_id(payload["ticker"])))
                return self.send(200,review_inputs(stock,read(ROOT/"policies/catalog.json"),payload["method"],payload["inputs"],derivations=payload.get("derivations",[])))
            if path.startswith("/api/update/"):
                ticker=safe_id(path.rsplit("/",1)[1])
                company=read(stock_path(ROOT,ticker))
                mode=payload.get("mode")
                candidates=[];warnings=[];hashes={};findings=[]
                folder=ROOT/"reports"/ticker
                folder.mkdir(parents=True,exist_ok=True)
                ledger_path=ROOT/"runtime/import-ledgers"/f"{ticker}.json"
                ledger=read(ledger_path) if ledger_path.exists() else {}
                if mode=="online":
                    candidates,warnings=refresh_candidates(company)
                elif mode=="offline":
                    import hashlib
                    scale=payload.get("scale",1)
                    if scale not in {1,1000,1000000}:
                        raise ValueError("Choose pesos, thousands or millions")
                    files=[p for p in sorted(folder.iterdir()) if p.suffix.lower() in {".pdf",".html",".htm",".txt"} and p.is_file()]
                    selected_file=payload.get("file")
                    if selected_file:
                        files=[p for p in files if p.name==selected_file]
                        if not files:
                            raise ValueError("Selected report was not found. Reload the report list.")
                    elif len(files)>1:
                        raise ValueError("Select one report so its date and unit scale cannot be applied to other files.")
                    if len(files)>30:
                        raise ValueError("Keep at most 30 reports in this folder; archive older files elsewhere")
                    for file in files:
                        if file.is_symlink() or not file.resolve().is_relative_to(folder.resolve()):
                            raise ValueError("Linked report files are not supported")
                        if file.stat().st_size>30_000_000:
                            warnings.append(f"{file.name}: exceeds 30 MB; use a smaller extract")
                            continue
                        digest=hashlib.sha256(file.read_bytes()).hexdigest()
                        import_key=hashlib.sha256(json.dumps(["disclosure-screen-v1",digest,payload.get("pages",""),payload.get("period",""),scale]).encode()).hexdigest()
                        if import_key in ledger:
                            continue
                        try:
                            file_findings=[]
                            rows,digest,notes=document_candidates(file,payload.get("period",""),scale,payload.get("pages",""),findings=file_findings)
                            hashes[file.name]=digest
                            for row in rows:
                                row["source_file"]=file.name;row["source_hash"]=digest;row["import_key"]=import_key
                            candidates.extend(rows);warnings.extend(notes)
                        except Exception as error:
                            warnings.append(f"{file.name}: {error}")
                        # A units/date error in numeric extraction must not hide a
                        # passage already found in successfully extracted text.
                        if file_findings:
                            hashes[file.name]=digest
                            for finding in file_findings:
                                finding.update(source_file=file.name,source_hash=digest,import_key=import_key)
                                finding['id']=hashlib.sha256(json.dumps(finding,sort_keys=True).encode()).hexdigest()
                            findings.extend(file_findings)
                else:
                    raise ValueError("Choose offline scan or online refresh")
                token=uuid.uuid4().hex
                for index,candidate in enumerate(candidates):
                    candidate["id"]=str(index)
                    candidate["previous"]=company["fields"].get(candidate["key"],{}).get("value")
                    conflict=same_period_conflict(candidate['key'],company['fields'].get(candidate['key'],{}),candidate)
                    if conflict:
                        candidate['source_conflict']=conflict
                        warnings.append(f"{candidate['key']}: same-period source conflict; applying this value records an unresolved reporting issue.")
                preview={"token":token,"ticker":ticker,"revision":revision(company),"mode":mode,"folder":str(folder),"candidates":candidates,"findings":findings,"warnings":warnings,"hashes":hashes}
                write(ROOT/"runtime/import-previews"/f"{token}.json",preview)
                return self.send(200,preview)
            if path=="/api/update-apply":
                if payload.get("confirmed") is not True:
                    raise ValueError("Confirm company, period, units and source rows before updating")
                token=safe_id(payload["token"])
                preview_path=ROOT/"runtime/import-previews"/f"{token}.json"
                preview=read(preview_path);ticker=safe_id(preview["ticker"])
                selected=payload.get("selected",[])
                selected_findings=payload.get("selected_findings",[])
                if any(not isinstance(items,list) or any(not isinstance(i,str) for i in items) for items in (selected,selected_findings)):
                    raise ValueError("Select the figures to update")
                chosen=[c for c in preview["candidates"] if c["id"] in selected]
                flagged=[f for f in preview.get("findings",[]) if f["id"] in selected_findings]
                if set(selected)-{c['id'] for c in chosen} or set(selected_findings)-{f['id'] for f in flagged}:
                    raise ValueError("Selection does not match this preview. Scan again.")
                if len({c["key"] for c in chosen})!=len(chosen):
                    raise ValueError("Select only one proposed value per field; compare duplicate reports first")
                if not chosen and not flagged:
                    raise ValueError("Select figures or disclosure passages to save")
                with LOCK:
                    destination=stock_path(ROOT,ticker);company=read(destination)
                    if revision(company)!=preview["revision"]:
                        return self.send(409,{"error":"Company data changed. Scan again before applying."})
                    import hashlib
                    for filename,digest in preview["hashes"].items():
                        file=ROOT/"reports"/ticker/filename
                        if not file.exists() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
                            raise ValueError("A source report changed. Scan again.")
                    conflicts={}
                    for candidate in chosen:
                        old=company["fields"].get(candidate["key"],{})
                        old_date=(old.get("period_end") or (old.get("as_of") if candidate["key"]=="price" else "") or "")[:10]
                        if old_date and candidate["as_of"][:10]<old_date:
                            raise ValueError(f"{candidate['key']}: proposed data is older than saved data; preserve the newer baseline")
                        conflict=same_period_conflict(candidate['key'],old,candidate)
                        if conflict:
                            conflict['detected_on']=datetime.now(timezone.utc).isoformat()
                            conflicts[uuid.uuid4().hex]=conflict
                        company["fields"][candidate["key"]]={k:v for k,v in candidate.items() if k not in {"id","key","previous","source_conflict"}}
                    financial_keys=sorted({candidate["key"] for candidate in chosen if candidate["key"] != "price"})
                    if financial_keys:
                        reports=company.setdefault("reports", {})
                        # Imported numbers do not reconcile a disclosure or renew a review.
                        # Keep the prior note/date for auditability; status controls readiness.
                        reports["review_status"]="unresolved" if reports.get("review_status")=="unresolved" else "unreviewed"
                        reports["invalidated_on"]=datetime.now(timezone.utc).isoformat()
                        reports["invalidated_fields"]=financial_keys
                        reports["invalidation_reason"]="Financial inputs imported; review the new figures and any reporting issues before relying on the valuation."
                    if conflicts:
                        reports=company.setdefault('reports',{})
                        reports.setdefault('source_conflicts',{}).update(conflicts)
                        reports['review_status']='unresolved'
                    if flagged:
                        reports=company.setdefault("reports",{})
                        reports["review_status"]="unresolved"
                        evidence=reports.setdefault("disclosure_findings",{})
                        for finding in flagged:
                            evidence[finding['id']]={k:v for k,v in finding.items() if k not in {'id','import_key'}}
                        reports["invalidation_reason"]="Selected disclosure passages require review; keyword matches are not confirmed accounting findings."
                    self.validate_stock(company,ticker)
                    write(ROOT/"runtime/revisions"/f"{ticker}-{uuid.uuid4().hex}.json",read(destination))
                    write(destination,company)
                    ledger_path=ROOT/"runtime/import-ledgers"/f"{ticker}.json"
                    ledger=read(ledger_path) if ledger_path.exists() else {}
                    for candidate in chosen+flagged:
                        if candidate.get("source_hash"):
                            # Mark a file complete only when every proposed row from it was selected.
                            all_rows=[r for r in preview["candidates"] if r.get("source_hash")==candidate["source_hash"]]
                            all_findings=[f for f in preview.get('findings',[]) if f.get('source_hash')==candidate['source_hash']]
                            if all(r["id"] in selected for r in all_rows) and all(f['id'] in selected_findings for f in all_findings):
                                ledger[candidate.get("import_key",candidate["source_hash"])]=candidate.get("source_file")
                    write(ledger_path,ledger)
                    preview_path.unlink()
                return self.send(200,{"updated":len(chosen),"flagged":len(flagged),"reporting_review_required":bool(financial_keys or flagged)})
            if path in {"/api/calculate", "/api/scenarios", "/api/compare"}:
                if payload.get("confirmed") is not True:
                    raise ValueError("Confirm the selected inputs and assumptions first")
                if payload.get('method') == 'pe' and isinstance(payload.get('inputs'), dict) and not payload['inputs'].get('pe_basis'):
                    raise ValueError('Choose an EPS basis and matching comparison P/E basis before calculating or saving. Older saved results remain available; classify their inputs before recalculating.')
                result = calculate(payload["method"], payload["inputs"])
                if path == "/api/compare":
                    return self.send(200, compare(payload["method"], payload["inputs"], payload["field"], payload["low"], payload["high"]))
                if path == "/api/calculate":
                    return self.send(200, result)
                ticker = safe_id(payload["ticker"])
                stock = read(stock_path(ROOT, ticker))
                policy = read(ROOT / "policies/catalog.json")
                if payload.get("stock_revision") and payload["stock_revision"] != revision(stock):
                    return self.send(409, {"error": "Company data changed since this analysis was loaded. Reload before saving."})
                if payload.get("policy_revision") and payload["policy_revision"] != revision(policy):
                    return self.send(409, {"error": "Method policies changed. Reload before saving."})
                record = {"id": uuid.uuid4().hex, "name": str(payload.get("name", "Untitled scenario"))[:120],
                    "ticker": ticker, "saved_at": datetime.now(timezone.utc).isoformat(),
                    "notes": str(payload.get("notes", ""))[:10000], "result": result,
                    "stock_snapshot": stock, "policy_snapshot": policy}
                record["input_review"]=review_inputs(stock,policy,payload["method"],payload["inputs"],derivations=payload.get("derivations",[]))
                record["derivations"]=payload.get("derivations",[])
                if payload.get("sensitivity"):
                    sensitivity = payload["sensitivity"]
                    record["sensitivity"] = compare(payload["method"], payload["inputs"], sensitivity["field"], sensitivity["low"], sensitivity["high"])
                with LOCK:
                    write(ROOT / "scenarios" / f"{record['id']}.json", record)
                return self.send(201, record)
            if path == "/api/policy" or path.startswith("/api/stocks/"):
                data = payload["data"]
                if path == "/api/policy":
                    self.validate_policy(data)
                    destination = ROOT / "policies/catalog.json"
                else:
                    ticker = safe_id(path.rsplit("/", 1)[1])
                    self.validate_stock(data, ticker)
                    destination = stock_path(ROOT, ticker)
                changed=[]; assumption_resets=[]
                with LOCK:
                    previous = read(destination)
                    if payload.get("revision") != revision(previous):
                        return self.send(409, {"error": "This file changed. Reload it before saving to avoid overwriting another edit."})
                    if path.startswith('/api/stocks/'):
                        for method,model in data.get('models',{}).items():
                            old_model=previous.get('models',{}).get(method,{})
                            values_changed=any(old_model.get(k)!=model.get(k) for k in METHODS[method][1])
                            same_basis=old_model.get('note','').strip()==model.get('note','').strip()
                            if values_changed and same_basis and model.get('evidence_status')=='documented':
                                model['evidence_status']='illustrative'
                                assumption_resets.append(method)
                        evidence_keys=('value','period_end','period_type','unit','scale','as_of',
                                       'source_url','source_file','source_hash','source_page',
                                       'cash_flow_reconciliation','sotp_components')
                        old_fields=previous.get('fields',{})
                        new_fields=data.get('fields',{})
                        changed=[]
                        for key in sorted(set(old_fields)|set(new_fields)):
                            if key=='price':
                                continue
                            old=old_fields.get(key,{})
                            new=new_fields.get(key,{})
                            if any(old.get(k)!=new.get(k) for k in evidence_keys):
                                changed.append(key)
                                if key in new_fields:
                                    new_fields[key]['status']='needs_review'
                        if changed:
                            reports=data.setdefault('reports',{})
                            reports['review_status']=('unresolved' if previous.get('reports',{}).get('review_status')=='unresolved'
                                                      or reports.get('review_status')=='unresolved' else 'unreviewed')
                            reports['invalidated_fields']=changed
                            reports['invalidation_reason']='Financial figures, periods or source evidence changed; review the saved inputs again.'
                        old_eps=previous.get('fields',{}).get('eps',{})
                        new_eps=data.get('fields',{}).get('eps',{})
                        bridge=new_eps.get('eps_bridge')
                        if isinstance(bridge,dict):
                            keys=('annual_eps','current_ytd_eps','prior_ytd_eps','annual_end','current_ytd_end','prior_ytd_end')
                            old_bridge=old_eps.get('eps_bridge',{})
                            if (any(old_bridge.get(k)!=bridge.get(k) for k in keys)
                                or any(old_eps.get(k)!=new_eps.get(k) for k in ('value','period_end','period_type'))):
                                bridge['review_status']='unreviewed'
                                bridge['invalidation_reason']='EPS components, value or period changed; review the saved calculation again'
                    write(ROOT / "runtime/revisions" / f"{destination.stem}-{uuid.uuid4().hex}.json", previous)
                    write(destination, data)
                return self.send(200, {"data": data, "revision": revision(data), "financial_review_reset":bool(changed),
                                       "assumption_review_reset":assumption_resets})
            self.send(404, {"error": "Not found"})
        except (ValueError, KeyError, TypeError, OverflowError, FileNotFoundError) as error:
            self.send(400, {"error": str(error)})
        except OSError:
            self.send(500, {"error": "Cannot save the local file. Check disk space and file permissions; the previous baseline was not replaced."})

    @staticmethod
    def validate_stock(data, ticker):
        if not isinstance(data, dict):
            raise ValueError("Company data must be an object")
        if data.get("ticker") != ticker or any(not isinstance(data.get(key), str) or not data[key].strip() for key in ("name", "industry")):
            raise ValueError("Stock needs matching ticker, name and industry")
        if data.get("currency") != "PHP" or not isinstance(data.get("fields"), dict):
            raise ValueError("Stock fields must be an object; valuation currency must be PHP")
        models = data.get("models", {})
        if not isinstance(models, dict):
            raise ValueError("Company models must be an object")
        for method, assumptions in models.items():
            if method not in METHODS or not isinstance(assumptions, dict):
                raise ValueError("Use supported method IDs for company assumptions")
            for key, value in assumptions.items():
                if key in {"note", "as_of", "evidence_status"}:
                    if not isinstance(value, str):
                        raise ValueError("Assumption notes and dates must be text")
                    if key == "evidence_status" and value not in {"illustrative", "documented"}:
                        raise ValueError("Assumption evidence status must be illustrative or documented")
                elif key not in METHODS[method][1] or (value != "" and (isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value))):
                    raise ValueError(f"{method}.{key}: enter a finite number or leave blank")
        reports = data.get("reports", {})
        if not isinstance(reports, dict) or reports.get("review_status", "unreviewed") not in {"unreviewed", "unresolved", "reviewed", "reconciled"}:
            raise ValueError("Choose a supported reporting review status")
        for key in ("review_note", "reviewed_on"):
            if key in reports and not isinstance(reports[key], str):
                raise ValueError("Reporting review date and note must be text")
        conflicts=reports.get('source_conflicts',{})
        if not isinstance(conflicts,dict):
            raise ValueError('Source conflicts must be an object keyed by evidence ID')
        for conflict in conflicts.values():
            if not isinstance(conflict,dict) or any(not isinstance(conflict.get(k),str) for k in ('field','period_end','note')):
                raise ValueError('Source conflict needs field, period and explanation')
            for side in ('previous','proposed'):
                observation=conflict.get(side)
                if not isinstance(observation,dict) or isinstance(observation.get('value'),bool) or not isinstance(observation.get('value'),(int,float)) or not math.isfinite(observation['value']):
                    raise ValueError('Source conflict observations require finite numbers')
        findings=reports.get('disclosure_findings',{})
        if not isinstance(findings,dict):
            raise ValueError('Disclosure findings must be an object keyed by evidence ID')
        for finding in findings.values():
            if not isinstance(finding,dict) or any(not isinstance(finding.get(key),str) for key in ('category','source_file','source_hash','excerpt')) or not isinstance(finding.get('source_page'),(str,int)):
                raise ValueError('Disclosure evidence needs category, file, hash, page and excerpt')
        for key, field in data["fields"].items():
            if not isinstance(field, dict) or "value" not in field:
                raise ValueError(f"{key}: expected a field object with value")
            from backend.review import PERIOD_TYPES
            if field.get("period_type", "unknown") not in PERIOD_TYPES:
                raise ValueError(f"{key}: choose a supported period type")
            value = field["value"]
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
                raise ValueError(f"{key}: value must be numeric or null")
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{key}: value must be finite")
            if value is not None and (not field.get("as_of") or not (field.get("source_url") or field.get("note"))):
                raise ValueError(f"{key}: provide an effective date and source or explanatory note")

    @staticmethod
    def validate_policy(data):
        if not isinstance(data, dict):
            raise ValueError("Policy must be an object")
        if not isinstance(data.get("methods"), dict) or set(data["methods"]) != set(METHODS):
            raise ValueError("Keep the supported method IDs; formulas are implemented in Python")
        for key, method in data["methods"].items():
            if not isinstance(method, dict) or not isinstance(method.get("name"), str) or not isinstance(method.get("description"), str):
                raise ValueError(f"{key}: method needs a name and description")
            if method.get("fields") != METHODS[key][1]:
                raise ValueError(f"{key}: required formula inputs cannot be removed or changed")
        if not isinstance(data.get("defaults"), dict) or not isinstance(data.get("recommendations"), dict):
            raise ValueError("Defaults and recommendations must be objects")
        for choices in data["recommendations"].values():
            if not isinstance(choices, list) or any(m not in METHODS for m in choices):
                raise ValueError("Recommendations must list supported method IDs")
        if not isinstance(data.get("fields"), dict) or any(key not in data["fields"] for method in METHODS.values() for key in method[1]):
            raise ValueError("All required fields need descriptions")
        original = initial_policy()
        for key, definition in original["fields"].items():
            field = data.get("fields", {}).get(key)
            if not isinstance(field, dict) or field.get("unit") != definition["unit"]:
                raise ValueError(f"{key}: preserve the calculation unit {definition['unit']}")
            if not isinstance(field.get("label"), str) or not isinstance(field.get("help"), str):
                raise ValueError(f"{key}: needs label and help text")
        for key, value in data["defaults"].items():
            if key not in original["fields"] or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key}: default must be a finite numeric value for a supported field")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser",action="store_true")
    args = parser.parse_args()
    policy = ROOT / "policies/catalog.json"
    if not policy.exists():
        write(policy, initial_policy())
    (ROOT / "scenarios").mkdir(exist_ok=True)
    for company_file in (ROOT / "brain").glob("*.toml"):
        (ROOT / "reports" / company_file.stem).mkdir(parents=True, exist_ok=True)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as error:
        print(f"Cannot start on port {args.port}. Close the other launcher or run python run.py --port 8766. Details: {error}",flush=True)
        return
    print(f"Valuation Workbench: http://127.0.0.1:{args.port} (Ctrl+C to stop)", flush=True)
    if args.open_browser:
        import webbrowser
        threading.Timer(.5,lambda:webbrowser.open(f"http://127.0.0.1:{args.port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
