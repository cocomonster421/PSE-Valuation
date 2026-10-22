"""Offline extraction and explicit online refresh. Candidates are reviewed before saving."""
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen


def number(text):
    text = text.strip().replace(",", "").replace("₱", "").replace("−", "-")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    return float(text) if re.fullmatch(r"-?\d+(?:\.\d+)?", text) else None


def soup_for(html):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ValueError("Install report tools once with: python -m pip install -r requirements.txt")
    return BeautifulSoup(html, "html.parser")


def edge_financials(html, source):
    soup = soup_for(html)
    section = "annual"
    sections = {"annual": {"date": None, "unit": "", "rows": {}}, "quarterly": {"date": None, "unit": "", "rows": {}}}
    for node in (soup.select_one("#contents") or soup).find_all(["h3", "p", "table"]):
        text = node.get_text(" ", strip=True)
        if node.name == "h3":
            section = "quarterly" if "quarterly" in text.lower() else "annual"
        elif node.name == "p":
            match = re.search(r"For the (?:fiscal year|period) ended\s*:\s*([A-Za-z]{3} \d{1,2}, \d{4})",text,re.I)
            if match:
                sections[section]["date"] = datetime.strptime(match[1],"%b %d, %Y").date().isoformat()
            if "currency" in text.lower():
                sections[section]["unit"] = text.split(":",1)[-1].strip()
        elif node.name == "table":
            for row in node.find_all("tr"):
                cells = row.find_all(["th","td"])
                if len(cells)>1:
                    sections[section]["rows"][cells[0].get_text(" ",strip=True)] = [number(c.get_text(" ",strip=True)) for c in cells[1:]]
    annual, quarterly = sections["annual"],sections["quarterly"]
    if not annual["date"] or "PHP" not in annual["unit"].upper():
        raise ValueError("No supported PHP annual financial summary found. Keep the existing data and use a reviewed import.")
    candidates=[]
    def add(key,value,period,note,period_type):
        if value is not None:
            candidates.append({"key":key,"value":value,"as_of":period,"period_end":period,"period_type":period_type,"source_url":source,"status":"needs_review","note":note})
    annual_eps=annual["rows"].get("Earnings/(Loss) Per Share (Basic)",[None])[0]
    q_eps=quarterly["rows"].get("Earnings/(Loss) Per Share (Basic)",[])
    eps=annual_eps
    eps_type="annual"
    period=annual["date"]
    note="Annual basic EPS from PSE EDGE; per-share values are not scaled with statement totals."
    if annual_eps is not None and quarterly["date"] and "PHP" in quarterly["unit"].upper() and len(q_eps)>=4 and q_eps[2] is not None and q_eps[3] is not None:
        a=datetime.fromisoformat(annual["date"]); q=datetime.fromisoformat(quarterly["date"])
        if a.month==12 and a.day==31 and q.year==a.year+1 and (q.month,q.day) in {(3,31),(6,30),(9,30)}:
            eps=annual_eps+q_eps[2]-q_eps[3];period=quarterly["date"]
            eps_type="ttm"
            note=f"Trailing-12-month EPS = annual EPS {annual_eps} + current YTD EPS {q_eps[2]} − prior YTD EPS {q_eps[3]}. Review accounting/share-basis comparability."
    add("eps",eps,period,note,eps_type)
    latest=quarterly if quarterly["date"] and quarterly["date"]>=annual["date"] and "PHP" in quarterly["unit"].upper() else annual
    add("bvps",latest["rows"].get("Book Value Per Share",[None])[0],latest["date"],"Reported book value per share from PSE EDGE; no monetary-unit scaling applied to per-share values.","point_in_time")
    return candidates


PDF_LABELS = {
    "operating_profit": [r"(?:income|profit) from operations",r"operating (?:income|profit)"],
    "depreciation": [r"depreciation and amortization"],
    "capital_spending": [r"(?:acquisitions|purchases|additions) (?:of|to) property,? plant and equipment"],
    "operating_cash_flow": [r"net cash (?:provided by|generated from) operating activities"],
    "cash": [r"cash and cash equivalents"],
    "debt": [r"total (?:interest-bearing )?(?:borrowings|debt)"],
    "eps": [r"(?:basic earnings per share|earnings per share[^\n]*?basic)"],
    "receivables": [r"trade receivables"],
    "inventory": [r"inventories"],
    "payables": [r"trade payables"],
    "working_capital_increase": [r"increase in operating working capital"],
}


def document_candidates(path, period="", scale=1, page_selection=""):
    if path.stat().st_size>30_000_000:
        raise ValueError("Report exceeds 30 MB; use a smaller extract or saved financial-summary page.")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    pages=None
    if path.suffix.lower() in {".html",".htm"}:
        html=path.read_text(encoding="utf-8",errors="replace")
        try:
            candidates=edge_financials(html,path.name)
            for candidate in candidates:
                candidate.update(source_file=path.name,source_hash=digest,unit="PHP/share",source_row=candidate["note"],source_page="HTML summary",scale=1)
            return candidates,digest,[]
        except ValueError:
            text=soup_for(html).get_text("\n",strip=True)
    elif path.suffix.lower()==".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("PDF tools are missing. Run python -m pip install -r requirements.txt once while online.")
        reader=PdfReader(path)
        if len(reader.pages)>500:
            raise ValueError("PDF exceeds 500 pages. Save only the relevant financial statements.")
        selected=set(range(1,len(reader.pages)+1))
        if page_selection:
            selected=set()
            for part in page_selection.split(","):
                if not re.fullmatch(r"\s*\d+(?:-\d+)?\s*",part): raise ValueError("Pages must look like 54,56,59-60")
                limits=[int(v) for v in part.strip().split("-")]
                if not 1<=limits[0]<=limits[-1]<=len(reader.pages): raise ValueError("Selected page is outside the PDF")
                selected.update(range(limits[0],limits[-1]+1))
        pages={n:reader.pages[n-1].extract_text(extraction_mode="layout") or "" for n in sorted(selected)}
        text="\n".join(pages.values())
        if len(text.strip())<100:
            raise ValueError("This appears to be a scanned/image PDF. Save a text-based report or enter reviewed figures; OCR is not enabled.")
    else:
        text=path.read_text(encoding="utf-8",errors="replace")
    if not period:
        raise ValueError("Select the financial period end for this report before scanning PDF/text files.")
    datetime.fromisoformat(period)
    declared_scales=set()
    if re.search(r"in\s+(?:thousand|thousands)(?:\s+of)?\s+pesos",text,re.I): declared_scales.add(1000)
    if re.search(r"in\s+(?:million|millions)(?:\s+of)?\s+pesos",text,re.I): declared_scales.add(1000000)
    if declared_scales and declared_scales!={scale}:
        raise ValueError("Selected unit scale conflicts with the report's stated pesos unit. Check the report header and scale.")
    interim=bool(re.search(r"(?:three|six|nine|3|6|9)\s+months?\s+ended|quarter\s+ended",text,re.I))
    page_lines=[(page_no,line_no,line) for page_no,page in (pages or {1:text}).items() for line_no,line in enumerate(page.splitlines(),1)]
    candidates=[]
    warnings=[]
    if interim: warnings.append("Interim report detected: income/cash-flow rows are not annual inputs and are omitted. Use an annual or reviewed trailing-year calculation.")
    for key, patterns in PDF_LABELS.items():
        if interim and key not in {"cash","debt","receivables","inventory","payables"}: continue
        hits=[]
        for page_no,line_no,line in page_lines:
            original_line=line.strip()
            if pages and key in {"cash","receivables","inventory","payables"} and not re.search(r"(?:statements? of financial position|balance sheets?)",pages[page_no],re.I):
                continue
            line=line.replace("−","-")
            line=re.sub(r"\(Notes?\s+[\d,\s]+(?:and\s+\d+)?\)","",line,flags=re.I).replace("P=","")
            label=next((m for pattern in patterns if (m:=re.match(r"^\s*(?:"+pattern+r")\s*:?\s*",line,re.I))),None)
            if label:
                tail=line[label.end():].strip()
                # Only a complete label followed by numeric columns is supported.
                # This rejects opening balances, note references and prose matches.
                if not re.fullmatch(r"[\d,().\-\s₱]+",tail):
                    continue
                match=re.search(r"\(?-?\d[\d,]*(?:\.\d+)?\)?",tail)
                if match:
                    value=number(match[0])
                    numbers=re.findall(r"\(?-?\d[\d,]*(?:\.\d+)?\)?",tail)
                    # PDF layout can concatenate adjacent columns. Never accept
                    # malformed thousands groups as one enormous company value.
                    if any("," in token and not re.fullmatch(r"\(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?",token) for token in numbers):
                        continue
                    # A small leading integer in a three-column row is often a note
                    # reference. Do not silently treat it as the reported amount.
                    if len(numbers)>1 and value is not None and value.is_integer() and (0<=value<100 or 1900<=value<=2100):
                        continue
                    if re.search(r"\bnotes?\b",line[:match.end()],re.I):
                        continue
                    if value is not None:
                        hits.append((value,original_line,numbers,page_no,line_no))
        # Repeated/ambiguous lines are deliberately not resolved by picking one.
        if len(hits)==1:
            value,line,numbers,page_no,line_no=hits[0]
            candidates.append({"key":key,"value":value*(1 if key=="eps" else scale),"as_of":period,"period_end":period,
                "source_url":"", "status":"needs_review","note":f"{path.name}: {line[:350]}. First numeric column; verify period duration, currency, scale and scope. Applied scale: {scale}.","source_file":path.name,"source_hash":digest,"source_page":page_no,"source_line":line_no,"source_row":line,"unit":"PHP/share" if key=="eps" else "PHP","scale":1 if key=="eps" else scale,"period_basis":"User-selected end date; duration requires review", "period_type":"point_in_time" if key in {"cash","debt","receivables","inventory","payables"} else "unknown"})
            if key in {"receivables","inventory","payables"} and len(numbers)==2 and not interim and not re.search(r"unaudited",(pages or {1:text})[page_no],re.I):
                previous=number(numbers[1])
                if previous is not None:
                    ending=datetime.fromisoformat(period)
                    try: previous_period=ending.replace(year=ending.year-1).date().isoformat()
                    except ValueError: previous_period=ending.replace(year=ending.year-1,day=28).date().isoformat()
                    candidates.append({**candidates[-1],"key":"previous_"+key,"value":previous*scale,
                        "period_end":previous_period,"as_of":previous_period,"report_period_end":period,
                        "note":f"{path.name}: {line[:350]}. Second column: confirm this is the previous annual closing balance. Scale: {scale}."})
        elif len(hits)>1:
            warnings.append(f"{key}: {len(hits)} matching rows; choose the correct value manually.")
    found={c['key'] for c in candidates}
    missing=[key for key in PDF_LABELS if key not in found]
    warnings.insert(0,"Review company, annual period, columns and units. Only recognized unambiguous rows are proposed; missing is not zero.")
    if missing: warnings.append("Not extracted: "+", ".join(missing)+". Enter these manually from the relevant statements if needed.")
    if not candidates: warnings.append("Unsupported or ambiguous layout: no figures were extracted. Use Edit company data; the saved brain is unchanged.")
    return candidates,digest,warnings


def fetch_edge(url):
    if urlsplit(url).hostname!="edge.pse.com.ph" or urlsplit(url).scheme!="https":
        raise ValueError("Refresh only supports official PSE EDGE HTTPS pages")
    request=Request(url,headers={"User-Agent":"Mozilla/5.0 (personal valuation workbench)"})
    with urlopen(request,timeout=20) as response:
        if urlsplit(response.geturl()).hostname!="edge.pse.com.ph":
            raise ValueError("Unexpected source redirect")
        content=response.read(5_000_001)
        if len(content)>5_000_000:
            raise ValueError("Source page too large")
        return content.decode("utf-8",errors="replace")


def refresh_candidates(stock):
    company_id=parse_qs(urlsplit(stock.get("pse_edge_url","")).query).get("cmpy_id",[None])[0]
    if not company_id or not company_id.isdigit():
        raise ValueError("Set a company-specific PSE EDGE link in the brain first")
    financial_url=f"https://edge.pse.com.ph/companyPage/financial_reports_view.do?cmpy_id={company_id}"
    candidates=[];errors=[]
    try:
        candidates.extend(edge_financials(fetch_edge(financial_url),financial_url))
    except Exception as error:
        errors.append(f"Financial summary unchanged: {error}")
    url=stock["fields"].get("price",{}).get("source_url") or f"https://edge.pse.com.ph/companyPage/stockData.do?cmpy_id={company_id}"
    try:
        soup=soup_for(fetch_edge(url));text=soup.get_text(" ",strip=True)
        date=re.search(r"As of ([A-Za-z]{3} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)",text)
        from datetime import timedelta
        if not date:
            raise ValueError("No quote timestamp found")
        timestamp=datetime.strptime(date[1],"%b %d, %Y %I:%M %p").replace(tzinfo=timezone(timedelta(hours=8))).isoformat()
        for row in soup.select("table.view tr"):
            cells=row.find_all(["th","td"])
            for i in range(len(cells)-1):
                if cells[i].get_text(" ",strip=True)=="Last Traded Price":
                    value=number(cells[i+1].get_text(" ",strip=True))
                    if value and value>0:
                        candidates.append({"key":"price","value":value,"as_of":timestamp,"source_url":url,"status":"historical","note":"Latest available PSE EDGE quote; may be delayed."})
        if not any(c["key"]=="price" for c in candidates):
            # EDGE can leave the live-trade cells empty while publishing a dated
            # previous close. Preserve that distinction instead of calling it live.
            close=re.search(r"Previous Close and Date\s+([\d,.]+)\s*\(([A-Za-z]{3} \d{1,2}, \d{4})\)",text)
            if not close or not number(close[1]) or number(close[1])<=0:
                raise ValueError("No valid quote or dated previous close found")
            close_date=datetime.strptime(close[2],"%b %d, %Y").date().isoformat()
            candidates.append({"key":"price","value":number(close[1]),"as_of":close_date,"source_url":url,"status":"historical","note":"PSE EDGE dated previous close; live last-traded price was unavailable. This is not a live quote."})
            errors.append("Live quote unavailable; proposing the dated previous close instead.")
    except Exception as error:
        errors.append(f"Price unchanged: {error}")
    return candidates,errors
