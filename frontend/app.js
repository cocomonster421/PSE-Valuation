"use strict";
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const peso = value => new Intl.NumberFormat("en-PH", {style:"currency",currency:"PHP",maximumFractionDigits:2}).format(value);
const numeric = value => new Intl.NumberFormat("en-PH", {maximumFractionDigits:2}).format(value);
const readableFormula = text => text.replace(/\b\d+(?:\.\d+)?e[+-]?\d+\b/gi, n => new Intl.NumberFormat("en-PH", {maximumFractionDigits:10}).format(Number(n)));
let stocks = [], stockRecord, policyRecord, result, lastInputs, editTarget, savedScenarios = [], sensitivity = null;
let statusTimer;
let inputVersion = 0;
let stockRequest = 0;
let reviewTimer, inputReview=null, derivations=[];
let batchReview=null;
$("close-batch-review").onclick=()=>$("batch-review").close();
$("check-all-stocks").onclick=async()=>{
  $("batch-review").showModal();
  $("batch-review-status").textContent="Checking local company files…";
  $("batch-review-results").replaceChildren();
  $("export-batch-review").disabled=true;$("check-all-stocks").disabled=true;
  batchReview=null;
  try {
    batchReview=await api('/api/review-all');
    $("batch-review-status").textContent=`${batchReview.companies.length} companies · ${batchReview.checked_at}. ${batchReview.scope}`;
    for(const company of batchReview.companies){
      const detail=document.createElement('details');detail.className='field-help';
      const problems=company.methods.filter(row=>row.calculation_status!=='Calculated' || row.review.status!=='Ready for input confirmation').length;
      detail.innerHTML=`<summary>${escapeHtml(company.ticker)} · ${escapeHtml(company.name)} · ${company.error ? 'File needs repair' : `${problems}/${company.methods.length} methods need review`}</summary>`;
      if(company.error){const message=document.createElement('p');message.textContent=company.error;detail.append(message);}
      else {
        const scope=document.createElement('p');scope.className='help';scope.textContent=company.method_scope;detail.append(scope);
        for(const row of company.methods){
          const section=document.createElement('div');
          const issues=[...row.review.missing.map(label=>'Missing: '+label),...row.review.issues,...(row.calculation_warnings || [])];
          if(row.calculation_error)issues.unshift(row.calculation_error);
          section.innerHTML=`<h3>${escapeHtml(row.name)}</h3><p>${escapeHtml(row.calculation_status)} · Data: ${escapeHtml(row.review.data_status)} · ${escapeHtml(row.review.assumption_status)}</p><ul>${issues.map(issue=>`<li>${escapeHtml(issue)}</li>`).join('')}</ul>`;
          const open=document.createElement('button');open.className='quiet';open.type='button';open.textContent='Open inputs';
          open.onclick=async()=>{try{await chooseStock(company.ticker);if(!basicMethods().includes(row.method))$("advanced-methods").checked=true;renderMethods(row.method);$("batch-review").close();}catch(error){status(error.message);}};
          section.append(open);detail.append(section);
        }
      }
      $("batch-review-results").append(detail);
    }
    $("export-batch-review").disabled=false;
  } catch(error){$("batch-review-status").textContent="Checks unavailable: "+error.message;}
  finally{$("check-all-stocks").disabled=false;}
};
$("export-batch-review").onclick=()=>{
  if(!batchReview)return;
  const blob=new Blob([JSON.stringify(batchReview,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob), link=document.createElement('a');
  link.href=url;link.download='stock-data-checks.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
function renderReadiness(){
  if(!inputReview)return;
  const checked=inputReview;
  $("input-readiness").textContent=(checked.missing.length ? "Missing data: "+checked.missing.join(", ") : checked.status) + ($("confirmed").checked ? " · Inputs acknowledged" : "");
  $("review-summary").textContent=`Data: ${checked.data_status || checked.status} · ${checked.assumption_status || "Assumptions need review"}`;
  $("input-checks").innerHTML=[...checked.issues,checked.note].map(t=>`<p class="help">${escapeHtml(t)}</p>`).join("");
}
function scheduleReview(){
  clearTimeout(reviewTimer);
  if(!stockRecord || !$("method").value)return;
  const version=inputVersion;
  reviewTimer=setTimeout(async()=>{try{
    const checked=await api("/api/review",{ticker:stockRecord.data.ticker,method:$("method").value,inputs:collectInputs(),derivations});
    if(version!==inputVersion)return;
    inputReview=checked;
    renderReadiness();
  }catch(error){$("input-readiness").textContent="Readiness check unavailable: "+error.message;}},180);
}
function baselineKey(method, key) { return key === "cash_flow" ? (method === "dcf_fcff" ? "fcff_cash_flow" : "fcfe_cash_flow") : key; }
const simpleNames = {dcf_fcff:"DCF",ddm:"Dividend valuation (DDM)",dividend_cap:"Dividend valuation",pe:"Earnings valuation (P/E)",pb:"Book-value valuation (P/B)",nav:"Asset valuation (NAV)",sotp:"Asset valuation (SOTP)",rnav:"Asset valuation (RNAV)"};
function basicMethods() {
  const profile = stockRecord.data.archetype;
  return ["dcf_fcff", profile === "REIT" ? "dividend_cap" : "ddm", "pe", "pb", profile === "CONGLOMERATE" ? "sotp" : profile === "PROPERTY_DEVELOPER" ? "rnav" : "nav"];
}
function preparedInput(method, key) {
  const model = stockRecord.data.models?.[method];
  if (model && Object.hasOwn(model, key)) return model[key] === "" ? null : model[key];
  return stockRecord.data.fields[baselineKey(method,key)]?.value ?? policyRecord.data.defaults[key] ?? null;
}
function missingInputs(method) {return policyRecord.data.methods[method].fields.filter(key=>preparedInput(method,key)==null);}
function status(message) { $("status").textContent = message; clearTimeout(statusTimer); statusTimer = setTimeout(() => $("status").textContent = "", 8000); }
async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}
function safeLink(url, label="Source") {
  try { const parsed = new URL(url); if (["https:","http:"].includes(parsed.protocol)) return `<a href="${escapeHtml(parsed.href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`; } catch {}
  return "No source link";
}
function invalidate() {
  inputVersion++;
  result = null; lastInputs = null;
  sensitivity = null;
  inputReview=null;
  $("input-readiness").textContent="Checking inputs…";
  $("review-summary").textContent="";
  $("input-checks").replaceChildren();
  $("confirmed").checked = false;
  $("save-scenario").disabled = true; $("export-scenario").disabled = true;
  $("result").innerHTML = '<p class="muted">Enter inputs to calculate.</p>';
  scheduleReview();
}
function renderSearch() {
  const query = $("stock-search").value.trim().toLowerCase();
  const matches = stocks.filter(s => !query || `${s.ticker} ${s.name}`.toLowerCase().includes(query));
  $("search-results").replaceChildren();
  for (const s of matches) {
    const button = document.createElement("button"); button.type = "button";
    button.textContent = `${s.ticker} · ${s.name}`; button.onclick = () => chooseStock(s.ticker).catch(e=>status(e.message));
    $("search-results").append(button);
  }
  if (!matches.length) $("search-results").textContent = "No matching company in the local data folder.";
}
async function chooseStock(ticker) {
  const request = ++stockRequest;
  $("research-case").hidden=true;
  invalidate();
  $("workspace").hidden = true;
  const loaded = await api(`/api/stocks/${encodeURIComponent(ticker)}`);
  if (request !== stockRequest) return;
  stockRecord = loaded;
  derivations=[]; inputReview=null;
  for(const [key,[label,value]] of Object.entries(rateFields)) $("rate-"+key).value=value;
  const s = stockRecord.data, price = s.fields.price;
  $("refresh-online").disabled=false;
  $("rate-risk_free").value = s.benchmark?.rate_value != null ? Number((s.benchmark.rate_value * 100).toFixed(5)) : 5;
  $("rate-result").textContent = s.benchmark?.rate_value != null ? `Saved risk-free benchmark: ${s.benchmark.source_name || "Source unspecified"}, ${s.benchmark.effective_date || "date unavailable"}. Other rate components are illustrative until reviewed.` : "No company benchmark saved. All rate components are illustrative until reviewed.";
  $("stock-search").value = `${s.ticker} · ${s.name}`;
  $("search-results").replaceChildren();
  $("company").hidden = false;
  $("company").innerHTML = `<div class="company-card"><div class="ticker">${escapeHtml(s.ticker)}</div><div><h2>${escapeHtml(s.name)}</h2><div class="help">${escapeHtml(s.industry)} · ${escapeHtml(s.archetype.replaceAll("_"," "))}</div></div><div class="quote"><small>LAST SAVED PRICE</small><br><strong>${price?.value ? peso(price.value) : "Unavailable"}</strong><div class="help">${escapeHtml(price?.as_of || "Date unavailable")}<br>Historical snapshot · offline</div></div></div>`;
  const links = document.createElement("div"); links.className = "company-links";
  links.innerHTML = `${safeLink(s.pse_edge_url, s.pse_edge_url?.includes("cmpy_id=") ? "PSE EDGE ↗" : "PSE EDGE directory ↗")} <a href="/api/brains/${encodeURIComponent(s.ticker)}" target="_blank" rel="noopener">View brain file ↗</a><span class="help">brain/${escapeHtml(s.ticker)}.toml</span>`;
  $("company").append(links);
  $("workspace").hidden = false;
  $("recommendation").textContent = s.rationale;
  renderMethods();
  $("scenario-name").value = `${s.ticker} · base case`;
  $("scenario-notes").value = "";
  const history = s.history || [];
  $("history").innerHTML = history.length ? `<table><thead><tr><th>Metric</th><th>Period end</th><th>Value / unit</th><th>Review status</th><th>Evidence</th></tr></thead><tbody>${history.map(f=>`<tr><td>${escapeHtml(f.metric)}</td><td>${escapeHtml(f.period_end)}</td><td>${escapeHtml(f.value)} ${escapeHtml(f.unit)}</td><td>${escapeHtml(f.status)}</td><td>${safeLink(f.source?.source_url)}</td></tr>`).join("")}</tbody></table>` : '<p class="help">No historical facts imported. Add reviewed figures through Edit company data.</p>';
}
function renderMethods(selected) {
  const policy = policyRecord.data;
  const recommended = policy.recommendations[stockRecord.data.archetype] || [];
  const available = $("advanced-methods").checked ? Object.keys(policy.methods) : basicMethods();
  const sorted = [...recommended.filter(m=>available.includes(m)), ...available.filter(m=>!recommended.includes(m))];
  $("method").replaceChildren();
  for (const key of sorted) {
    const option = document.createElement("option"); option.value = key;
    const missing = missingInputs(key).length;
    option.textContent = `${recommended.includes(key) ? "★ " : ""}${simpleNames[key] || policy.methods[key].name} · ${missing ? `${missing} missing from brain` : "Inputs available"}`;
    $("method").append(option);
  }
  $("method").value = selected && sorted.includes(selected) ? selected : sorted.find(m=>recommended.includes(m) && !missingInputs(m).length) || sorted[0];
  renderFields();
}
function renderFields(overrides) {
  derivations=[];
  const policy = policyRecord.data, method = policy.methods[$("method").value];
  $("rate-calculator").hidden = !method.fields.includes("discount_rate");
  const recommended = policy.recommendations[stockRecord.data.archetype] || [];
  $("method-description").textContent = `${method.description} ${recommended.includes($("method").value) ? "Suggested for this company profile; verify that the inputs meet this method’s definitions." : "Outside this profile’s recommendations. Document why it fits the business before relying on it."}`;
  const missing = missingInputs($("method").value);
  $("method-readiness").textContent = missing.length ? `Missing: ${missing.map(key=>fieldDefinition($("method").value,key).label).join(", ")}` : "Prefilled from company brain. Review, then calculate.";
  $("fields").replaceChildren();
  for (const key of [...method.fields, "price"]) {
    const definition = fieldDefinition($("method").value,key);
    const source = Object.hasOwn(stockRecord.data.models?.[$("method").value]||{},key) ? null : stockRecord.data.fields[baselineKey($("method").value, key)];
    const initial = overrides && Object.hasOwn(overrides,key) ? overrides[key] : preparedInput($("method").value,key) ?? "";
    const value = definition.unit === "rate" && initial !== "" ? Number((initial * 100).toFixed(8)) : initial;
    const field = document.createElement("div"); field.className="field";
    const selectedModel=stockRecord.data.models?.[$("method").value];
    const sourceText = overrides ? "Scenario input · review required" : selectedModel && Object.hasOwn(selectedModel,key) ? `Company assumption · ${selectedModel.as_of || "Date unavailable"}` : source?.value != null ? `${source.status || "Review required"} · ${source.period_end || source.as_of || "Date unavailable"}` : initial !== "" ? "Illustrative policy assumption" : "Required input";
    field.innerHTML = `<label for="input-${escapeHtml(key)}">${escapeHtml(definition.label)} <small>${definition.unit === "rate" ? "%" : escapeHtml(definition.unit)}</small></label><input id="input-${escapeHtml(key)}" data-key="${escapeHtml(key)}" type="number" step="any" ${key === "price" ? "" : "required"} value="${escapeHtml(value)}"><details class="field-help"><summary>Details</summary><p class="help">${escapeHtml(definition.help)}</p>${source?.note ? `<p class="help">${escapeHtml(source.note)}</p>` : ""}</details><small class="provenance">${escapeHtml(sourceText)}${source?.source_url ? ` · ${safeLink(source.source_url)}` : ""}</small>`;
    field.querySelector("input").addEventListener("input", () => {
      field.querySelector(".provenance").textContent = "Edited input · document your basis";
      derivations=derivations.filter(d=>d.output_field!==key);
      invalidate();
      showCurrentRatios();
    });
    const model = stockRecord.data.models?.[$("method").value];
    if (model && Object.hasOwn(model,key) && model.note) {
      const note = document.createElement("p"); note.className="help"; note.textContent=model.note;
      field.querySelector("details").append(note);
    }
    $("fields").append(field);
  }
  invalidate();
  showCurrentRatios();
  renderCashHelper();
}
function fieldDefinition(method,key) {
  const field={...policyRecord.data.fields[key]};
  if(key==="multiple" && method==="pe") field.help="Choose a comparison P/E using dated observations from similar businesses or this company's own history. Compare the same earnings basis (for example, trailing annual EPS), profitability, growth and debt; explain exclusions and your selected ratio in Notes / sources. Current price ÷ EPS gives current P/E, not an independent fair-value target. Practice example only: EPS 5 × an illustrative comparison P/E of 12 = 60. The 12 is not an industry average. Leave this blank until you have a basis, or use DEMO for practice.";
  if(key==="multiple") field.label=method==="pe"?"Comparison P/E":method==="pb"?"Comparison P/B":"Comparison price / cash earnings";
  if(key==="terminal_growth" && method==="ddm") {
    field.label="Long-run dividend growth";
    field.help="Assumed annual dividend growth starting with the next year's dividend and continuing indefinitely. This constant-growth DDM has no separate five-year forecast. Keep growth below Required yearly return and justify whether the payout can sustain it.";
  }
  if(key==="cash_flow" && method==="dcf_fcfe") {
    field.label="Annual cash available to shareholders";
    field.help="Shareholder cash (FCFE) = business cash (FCFF) − interest expense × (1 − tax rate) + new borrowing − debt repayments. Alternatively use net income + non-cash charges − capital investment − increase in operating working capital + net borrowing. Use cash after financing, discount at shareholders' required return, and do not subtract debt again.";
  }
  if(key==="terminal_growth" && ["justified_pb","residual_income"].includes(method)) {
    field.label="Long-run growth";
    field.help="With stable positive ROE and no new share issuance, growth = ROE × earnings retained. A growth rate above ROE needs another financing explanation. Residual income assumes the payout changes after year 5 to support this long-run growth.";
  }
  if(["nav","rnav"].includes(method) && key==="asset_value") {
    field.label="Reviewed gross asset value";
    field.help="Enter assets before deducting liabilities, using the same ownership scope as the liabilities and shares. For RNAV use reviewed current property/project values. Do not enter an already-net equity value here.";
  }
  if(["nav","rnav"].includes(method) && key==="liabilities") {
    field.label="Liabilities and other claims against those assets";
    field.help="Subtract all liabilities and non-common claims relating to the entered gross assets, using the same ownership scope. Do not use only parent-company debt, and do not subtract a liability twice.";
  }
  return field;
}
function showCurrentRatios() {
  const method=$("method").value, key=method==="pe"?"eps":method==="pb"?"bvps":null;
  $("current-ratios").hidden=!key;
  if(!key) return;
  const price=Number($("input-price")?.value), amount=Number($("input-"+key)?.value);
  const name=method==="pe"?"P/E":"P/B", label=policyRecord.data.fields[key].label;
  $("current-ratios").textContent=price>0 && amount>0 ? `Current ${name} = Share price (${numeric(price)}) ÷ ${label} (${numeric(amount)}) = ${numeric(price/amount)}×. Fair value uses the separate Comparison ${name} below; using this current ratio would just return the current price.` : `Enter a positive Share price and ${label} to calculate current ${name}.`;
}
function collectInputs() {
  const inputs = {};
  for (const input of $("fields").querySelectorAll("input")) {
    if (input.value === "") continue;
    const value = Number(input.value);
    inputs[input.dataset.key] = policyRecord.data.fields[input.dataset.key].unit === "rate" ? value/100 : value;
  }
  return inputs;
}
function renderResult(value) {
  $("result").innerHTML = `<div class="help">${escapeHtml(policyRecord.data.methods[value.method].name)} · per share</div><div class="fair-value">${peso(value.fair_value)}</div>${value.gap == null ? '<p class="help">Add a reference price to compare.</p>' : `<span class="gap">${value.gap >= 0 ? "+" : ""}${(value.gap * 100).toFixed(1)}% vs reference price</span>`}${value.warnings.map(w=>`<p class="warning">${escapeHtml(w)}</p>`).join("")}<details open><summary>Calculation</summary>${value.steps.map(s=>`<div class="calculation"><span>${escapeHtml(readableFormula(s.label))}</span><strong>${numeric(s.present_value ?? s.value)}</strong></div>`).join("")}</details>`;
  const qualification=document.createElement("p"); qualification.className="warning";
  qualification.textContent=inputReview ? `${inputReview.assumption_status} · Data: ${inputReview.data_status}. Calculation completed; this is not a verified price target.` : "Review unavailable: treat this result as an illustrative scenario.";
  $("result").prepend(qualification);
  $("save-scenario").disabled = false; $("export-scenario").disabled = false;
  if(value.formula) {const paragraph=document.createElement("p");paragraph.className="help";paragraph.textContent="Formula: "+value.formula;$("result").append(paragraph);}
  const exploration = document.createElement("div");
  exploration.innerHTML = '<hr><h3>Sensitivity</h3><label for="sensitivity-field">Assumption to vary</label><select id="sensitivity-field"></select><div class="fields"><div><label for="sensitivity-low">Lower input</label><input id="sensitivity-low" type="number" step="any"></div><div><label for="sensitivity-high">Higher input</label><input id="sensitivity-high" type="number" step="any"></div></div><button type="button" id="sensitivity-run" class="quiet">Compare values</button><div id="sensitivity-results"></div>';
  $("result").append(exploration);
  let comparisonVersion=0;
  const rangeNote=document.createElement("p");rangeNote.className="help";
  rangeNote.textContent="Automatic starting range: ±1 percentage point for rates, ±10% for other inputs (±1 unit if zero). Asset-discount ranges are shortened at the 0% and 100% boundaries. This is an illustrative stress test, not a peer benchmark or confidence interval. Edit the range to reflect your research.";
  exploration.querySelector('h3').after(rangeNote);
  for (const key of policyRecord.data.methods[value.method].fields) {
    const option = document.createElement("option"); option.value = key;
    const field = fieldDefinition(value.method,key); option.textContent = `${field.label} (${field.unit === "rate" ? "%" : field.unit})`;
    $("sensitivity-field").append(option);
  }
  function resetSensitivity() {
    comparisonVersion++;
    sensitivity = null; $("sensitivity-results").replaceChildren();
    const key = $("sensitivity-field").value, rate = policyRecord.data.fields[key].unit === "rate";
    const base = lastInputs[key] * (rate ? 100 : 1), delta = rate ? 1 : Math.abs(base) * .1 || 1;
    $("sensitivity-low").value = Number((base - delta).toFixed(8)); $("sensitivity-high").value = Number((base + delta).toFixed(8));
    if(key==="discount") {
      $("sensitivity-low").value=Math.max(0,base-delta);
      $("sensitivity-high").value=base+delta>=100 ? (base+100)/2 : base+delta;
    }
  }
  $("sensitivity-field").onchange = resetSensitivity;
  for (const id of ["sensitivity-low", "sensitivity-high"]) $(id).oninput = () => {comparisonVersion++;sensitivity=null;$("sensitivity-results").replaceChildren();};
  const preferred=["discount_rate","multiple","required_yield","cap_rate","discount","in_force_value"].find(key=>policyRecord.data.methods[value.method].fields.includes(key));
  if(preferred)$("sensitivity-field").value=preferred;
  resetSensitivity();
  $("sensitivity-run").onclick = async () => {
    const request=++comparisonVersion, version=inputVersion;
    try {
      const key = $("sensitivity-field").value, divisor = policyRecord.data.fields[key].unit === "rate" ? 100 : 1;
      if ($("sensitivity-low").value === "" || $("sensitivity-high").value === "") throw new Error("Enter both sensitivity inputs.");
      const low = Number($("sensitivity-low").value)/divisor, high = Number($("sensitivity-high").value)/divisor;
      if (low >= high) throw new Error("The lower input must be below the higher input.");
      $("sensitivity-results").textContent="Checking sensitivity…";
      const compared = await api("/api/compare", {method:value.method, inputs:lastInputs, field:key, low, high, confirmed:true});
      if (version !== inputVersion || request !== comparisonVersion || result !== value) return;
      sensitivity = {field:key, low, high};
      $("sensitivity-results").innerHTML = `<table><thead><tr><th>Case</th><th>Input</th><th>Fair value</th></tr></thead><tbody>${compared.cases.map(c=>`<tr><td>${escapeHtml(c.label)}</td><td>${numeric(c.input*divisor)}${divisor===100?"%":""}</td><td>${peso(c.result.fair_value)}</td></tr>`).join("")}</tbody></table>`;
      const summary=document.createElement("p");summary.className="warning";
      summary.textContent=`Tested values: ${peso(compared.summary.minimum)}–${peso(compared.summary.maximum)}. `+(compared.summary.crosses_reference_price===true ? "The values cross the reference price: the above/below-price conclusion changes within this range." : compared.summary.crosses_reference_price===null ? "Add a reference price to test whether the conclusion changes." : "The values do not cross the reference price in this range; this does not establish robustness outside these inputs.");
      $("sensitivity-results").prepend(summary);
    } catch(error) {
      if(version!==inputVersion || request!==comparisonVersion || result!==value)return;
      sensitivity=null;
      $("sensitivity-results").textContent="Sensitivity unavailable: "+error.message+" Adjust the range and compare again. The base calculation is unchanged.";
    }
  };
  $("sensitivity-run").click();
}
$("stock-search").addEventListener("input", renderSearch);
$("stock-search").addEventListener("focus", renderSearch);
$("all-stocks").onclick=()=>{$("stock-search").value="";renderSearch();};
$("method").addEventListener("change", ()=>renderFields());
$("advanced-methods").addEventListener("change", ()=>renderMethods($("method").value));
$("reset").onclick = ()=>renderFields();
$("confirmed").onchange=renderReadiness;
$("valuation-form").onsubmit = async event => {
  event.preventDefault();
  try {
    const inputs = collectInputs();
    const version = inputVersion;
    const response = await api("/api/calculate", {method:$("method").value, inputs, confirmed:$("confirmed").checked});
    const checked=await api("/api/review",{ticker:stockRecord.data.ticker,method:$("method").value,inputs,derivations});
    if (version !== inputVersion) return;
    inputReview=checked;
    renderReadiness();
    result = response; lastInputs = inputs; renderResult(result);
  } catch (error) { status(error.message); }
};
const rateFields = {risk_free:["Government-rate starting point (%)",5], beta:["Market sensitivity (beta)",1], premium:["Extra return for stock-market risk (%)",6], debt_cost:["Yearly borrowing cost before tax (%)",7], tax:["Tax rate on interest deductions (%)",25], debt_weight:["Debt share of total funding (%)",30]};
$("rate-fields").innerHTML = Object.entries(rateFields).map(([key,[label,value]])=>`<div><label for="rate-${key}">${label}</label><input id="rate-${key}" type="number" step="any" value="${value}"></div>`).join("");
$("apply-rate").onclick = () => {
  const read = key => { const text=$("rate-"+key).value; if(text==="") throw new Error("Fill all discount-rate components"); return Number(text); };
  try {
    const rf=read("risk_free")/100, beta=read("beta"), premium=read("premium")/100, debt=read("debt_cost")/100, tax=read("tax")/100, weight=read("debt_weight")/100;
    if(tax<0||tax>1||weight<0||weight>1||rf<0||premium<0||debt<0) throw new Error("Check rate components; tax and debt weight must be 0–100%.");
    const equity=rf+beta*premium;
    const fcff=$("method").value==="dcf_fcff", rate=fcff ? equity*(1-weight)+debt*(1-tax)*weight : equity;
    if(!$("input-discount_rate")) throw new Error("This method does not use a discount rate.");
    $("input-discount_rate").value=(rate*100).toFixed(4); invalidate();
    $("rate-result").textContent=`${fcff ? "WACC" : "Cost of equity"}: ${(rate*100).toFixed(2)}%. Components are illustrative until you verify them.`;
    $("scenario-notes").value += `\nDiscount-rate basis: rf=${rf}, beta=${beta}, ERP=${premium}, debt cost=${debt}, tax=${tax}, debt weight=${weight}; ${fcff ? "WACC" : "cost of equity"}=${rate}.`;
  } catch(e) { status(e.message); }
};
function scenarioPayload() {return {ticker:stockRecord.data.ticker, stock_revision:stockRecord.revision, policy_revision:policyRecord.revision, method:result.method, inputs:lastInputs, sensitivity, derivations, confirmed:true, name:$("scenario-name").value, notes:$("scenario-notes").value};}
$("save-scenario").onclick = async()=>{try { if(!result) return; await api("/api/scenarios", scenarioPayload()); status("Analysis saved in the scenarios folder."); }catch(e){status(e.message);}};
$("export-scenario").onclick = ()=>{
  if(!result) return;
  const data={...scenarioPayload(),result,input_review:inputReview,stock_snapshot:stockRecord.data,policy_snapshot:policyRecord.data};
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));
  const a=document.createElement("a");a.href=url;a.download=`${stockRecord.data.ticker}-valuation.json`;a.click();URL.revokeObjectURL(url);
};
async function loadSavedAnalysis(s) {
  try {
    if(!policyRecord.data.methods[s.result.method]) throw new Error("This saved method is unavailable in the current policies.");
    await chooseStock(s.ticker);
    if(!basicMethods().includes(s.result.method)) $("advanced-methods").checked=true;
    renderMethods(s.result.method);
    renderFields(s.result.inputs);
    derivations=structuredClone(s.derivations || []).filter(d=>d.output_field==="working_capital_increase" || s.result.inputs[d.output_field]===d.value);
    const components=derivations.find(d=>d.output_field==='asset_value')?.component_reconciliation?.components;
    if(s.result.method==='sotp' && components){$('cash-helper').replaceChildren();renderComponentHelper(components);}
    for(const d of derivations) {
      d.origin = d.origin || {saved_at:s.saved_at, name:s.name};
      for(const [key,value] of Object.entries(d.inputs || {})) {
        const input=$("derive-"+key);
        if(input) input.value=value;
        if(key==="tax") $("rate-tax").value=value*100;
      }
    }
    if(derivations.length) {
      const note=document.createElement("p");note.className="help";
      note.textContent="Saved helper evidence restored from the original analysis, not refreshed company data. Review its dates in Data checks; Use calculated figures replaces it with the helper values shown.";
      $("cash-helper").prepend(note);
    }
    $("scenario-name").value=s.name;$("scenario-notes").value=s.notes;
    scheduleReview();
    status("Saved inputs loaded. Review against current company data before recalculating.");
    $("workspace").scrollIntoView({behavior:"smooth"});
  } catch(error) {status(error.message);}
}
$("open-library").onclick=async()=>{try{
  savedScenarios=await api("/api/scenarios");$("library").hidden=false;$("saved-list").replaceChildren();
  if(!savedScenarios.length) $("saved-list").textContent="No analyses saved yet. Calculate a valuation, then save it here.";
  for(const s of savedScenarios){const row=document.createElement("div");row.className="saved-item";row.innerHTML=`<p>${escapeHtml(s.name)}<small>${escapeHtml(s.ticker)} · ${escapeHtml(s.saved_at)} · ${peso(s.result.fair_value)}</small></p>`;const button=document.createElement("button");button.className="quiet";button.textContent="Load inputs";button.onclick=()=>loadSavedAnalysis(s);row.append(button);$("saved-list").append(row);}
  $("library").scrollIntoView({behavior:"smooth"});
}catch(e){status(e.message);}};
$("close-library").onclick=()=>$("library").hidden=true;
function openEditor(target) {editTarget=target;$("editor-title").textContent=target==="stock"?`Edit ${stockRecord.data.ticker} baseline`:"Edit method policies";$("editor-json").value=JSON.stringify((target==="stock"?stockRecord:policyRecord).data,null,2);$("editor-error").textContent="";$("editor").showModal();}
$("edit-stock").onclick=()=>openStockEditor();$("edit-policy").onclick=()=>openPolicyEditor();$("close-editor").onclick=()=>$("editor").close();
$("editor-form").onsubmit=async event=>{event.preventDefault();try{const data=JSON.parse($("editor-json").value);const record=editTarget==="stock"?stockRecord:policyRecord;const path=editTarget==="stock"?`/api/stocks/${stockRecord.data.ticker}`:"/api/policy";const updated=await api(path,{data,revision:record.revision});if(editTarget==="policy")policyRecord=updated;await chooseStock(stockRecord.data.ticker);$("editor").close();status("Local file saved; previous version backed up. Inputs reset to updated defaults.");}catch(e){$("editor-error").textContent=e.message;}};
Promise.all([api("/api/stocks"),api("/api/policy")]).then(([s,p])=>{stocks=s;policyRecord=p;renderRateHelp();renderSearch();$("demo-start").hidden=!stocks.some(s=>s.ticker==="DEMO");}).catch(e=>status(e.message));
$("try-demo").onclick=()=>chooseStock("DEMO").catch(e=>status(e.message));

function openStockEditor() {
  const stock = stockRecord.data;
  $("stock-editor-title").textContent = `${stock.ticker} · company data`;
  $("company-name").value = stock.name; $("company-industry").value = stock.industry;
  $("company-rationale").value = stock.rationale || ""; $("company-notes").value = stock.notes || "";
  $("reporting-status").value=stock.reports?.review_status || "unreviewed";
  $("reporting-date").value=(stock.reports?.reviewed_on || "").slice(0,10);
  $("reporting-note").value=stock.reports?.review_note || "";
  $("stock-editor-error").textContent = "";
  $("company-archetype").replaceChildren();
  for (const key of new Set([stock.archetype, ...Object.keys(policyRecord.data.recommendations)])) {
    const option = document.createElement("option"); option.value = key; option.textContent = key.replaceAll("_", " ");
    $("company-archetype").append(option);
  }
  $("company-archetype").value = stock.archetype;
  $("stock-editor-fields").replaceChildren();
  $("stock-models").replaceChildren();
  for (const method of basicMethods()) {
    const model = stock.models?.[method] || {};
    const keys = policyRecord.data.methods[method].fields.filter(key=>["growth","terminal_growth","discount_rate","multiple","discount","required_yield"].includes(key));
    if (!keys.length) continue;
    const group = document.createElement("fieldset"); group.dataset.model = method;
    group.innerHTML = `<legend>${escapeHtml(simpleNames[method])}</legend><div class="fields"></div>`;
    for (const key of keys) {
      const definition = policyRecord.data.fields[key];
      const initial = Object.hasOwn(model,key) ? model[key] : policyRecord.data.defaults[key] ?? "";
      const value = initial === "" ? "" : initial * (definition.unit === "rate" ? 100 : 1);
      const row = document.createElement("div");
      row.innerHTML = `<label for="model-${method}-${key}">${escapeHtml(definition.label)} (${definition.unit === "rate" ? "%" : escapeHtml(definition.unit)})</label><input id="model-${method}-${key}" data-assumption="${key}" type="number" step="any" value="${escapeHtml(value)}">`;
      group.querySelector(".fields").append(row);
    }
    const evidence = document.createElement("div");
    evidence.innerHTML=`<label>Assumption basis<textarea data-model-note rows="2">${escapeHtml(model.note || "")}</textarea></label><label>Review date<input data-model-date type="date" value="${escapeHtml((model.as_of || "").slice(0,10))}"></label><label>Evidence<select data-model-evidence><option value="illustrative">Illustrative / still researching</option><option value="documented">Basis documented by me</option></select></label><p class="help">Explain each assumption, its source or reasoning, and period. Documented does not mean independently verified.</p>`;
    evidence.querySelector("[data-model-evidence]").value=model.evidence_status || "illustrative";group.append(evidence);
    group.addEventListener("input",()=>group.dataset.changed="true");
    group.addEventListener("change",()=>group.dataset.changed="true");
    $("stock-models").append(group);
  }
  const assumptionKeys = new Set(["growth", "discount_rate", "terminal_growth", "multiple", "discount", "required_yield", "cap_rate"]);
  for (const [key, definition] of Object.entries(policyRecord.data.fields)) {
    if (key === "cash_flow") continue;
    if (assumptionKeys.has(key) && !stock.fields[key]) continue;
    const original = stock.fields[key] || {};
    const value = original.value == null ? "" : definition.unit === "rate" ? Number((original.value * 100).toFixed(8)) : original.value;
    const fieldset = document.createElement("fieldset"); fieldset.dataset.field = key;
    fieldset.innerHTML = `<legend>${escapeHtml(definition.label)} · ${definition.unit === "rate" ? "%" : escapeHtml(definition.unit)}</legend><p class="help">${escapeHtml(definition.help)}</p><div class="fields"><div><label for="baseline-${escapeHtml(key)}">Value</label><input id="baseline-${escapeHtml(key)}" data-property="value" type="number" step="any" value="${escapeHtml(value)}"></div><div><label for="baseline-date-${escapeHtml(key)}">Effective / publication date</label><input id="baseline-date-${escapeHtml(key)}" data-property="as_of" type="date" value="${escapeHtml((original.as_of || "").slice(0,10))}"></div><div><label for="baseline-source-${escapeHtml(key)}">Source URL</label><input id="baseline-source-${escapeHtml(key)}" data-property="source_url" type="url" value="${escapeHtml(original.source_url || "")}"></div><div><label for="baseline-status-${escapeHtml(key)}">Review status</label><select id="baseline-status-${escapeHtml(key)}" data-property="status"><option value="needs_review">Needs review</option><option value="reviewed">Reviewed by me</option><option value="historical">Historical reference</option></select></div><div><label for="baseline-period-${escapeHtml(key)}">Financial period end</label><input id="baseline-period-${escapeHtml(key)}" data-property="period_end" type="date" value="${escapeHtml((original.period_end || "").slice(0,10))}"></div><div><label for="baseline-note-${escapeHtml(key)}">Basis / notes</label><textarea id="baseline-note-${escapeHtml(key)}" data-property="note" rows="2">${escapeHtml(original.note || "")}</textarea></div></div>`;
    fieldset.querySelector('[data-property="status"]').value = ["needs_review","reviewed","historical"].includes(original.status) ? original.status : "needs_review";
    const periodRow=document.createElement("div");
    periodRow.innerHTML=`<label for="baseline-duration-${escapeHtml(key)}">Period covered</label><select id="baseline-duration-${escapeHtml(key)}" data-property="period_type"><option value="unknown">Unknown / needs checking</option><option value="annual">Full financial year</option><option value="ttm">Trailing 12 months</option><option value="quarter">Single quarter</option><option value="ytd">Year to date (partial year)</option><option value="point_in_time">Balance at one date</option></select><p class="help">EPS, dividends and cash flows need a full-year or trailing-year basis. Book value, debt and share counts are balances at a date.</p>`;
    periodRow.querySelector('select').value=original.period_type || "unknown";
    fieldset.querySelector('.fields').append(periodRow);
    if(key==='eps') renderEpsEvidence(fieldset, original);
    fieldset.addEventListener("input", () => fieldset.dataset.changed = "true");
    fieldset.addEventListener("change", () => fieldset.dataset.changed = "true");
    $("stock-editor-fields").append(fieldset);
  }
  $("stock-editor").showModal();
}
$("close-stock-editor").onclick = () => $("stock-editor").close();
$("stock-advanced").onclick = () => {$("stock-editor").close(); openEditor("stock");};
$("stock-editor-form").onsubmit = async event => {
  event.preventDefault();
  try {
    const data = JSON.parse(JSON.stringify(stockRecord.data));
    data.name = $("company-name").value.trim(); data.industry = $("company-industry").value.trim();
    data.archetype = $("company-archetype").value; data.rationale = $("company-rationale").value.trim(); data.notes = $("company-notes").value;
    data.reports={...(data.reports || {}),review_status:$("reporting-status").value,reviewed_on:$("reporting-date").value,review_note:$("reporting-note").value.trim()};
    data.models = data.models || {};
    for (const group of $("stock-models").querySelectorAll('fieldset[data-changed="true"]')) {
      const method = group.dataset.model;
      const assumptions = {...(data.models[method] || {})};
      for (const input of group.querySelectorAll("[data-assumption]")) {
        const key=input.dataset.assumption;
        assumptions[key]=input.value === "" ? "" : Number(input.value)/(policyRecord.data.fields[key].unit === "rate" ? 100 : 1);
      }
      assumptions.note=group.querySelector("[data-model-note]").value.trim();
      assumptions.as_of=group.querySelector("[data-model-date]").value;
      assumptions.evidence_status=group.querySelector("[data-model-evidence]").value;
      data.models[method]=assumptions;
    }
    for (const group of $("stock-editor-fields").querySelectorAll('fieldset[data-changed="true"]')) {
      const key = group.dataset.field;
      const field = {...(data.fields[key] || {})};
      for (const input of group.querySelectorAll("[data-property]")) {
        field[input.dataset.property] = input.dataset.property === "value" ? (input.value === "" ? null : Number(input.value) / (policyRecord.data.fields[key].unit === "rate" ? 100 : 1)) : input.value;
      }
      if(key==='eps' && group.querySelector('[data-eps-key]')) {
        const bridge={...(field.eps_bridge || {})};
        for(const input of group.querySelectorAll('[data-eps-key]')) {
          bridge[input.dataset.epsKey]=input.type==='number' ? (input.value===''?null:Number(input.value)) : input.value;
        }
        if(Object.values(bridge).some(value=>value!==null && value!=='' && value!=='unreviewed')) field.eps_bridge=bridge;
      }
      field.updated_at = new Date().toISOString(); data.fields[key] = field;
    }
    const saved=await api(`/api/stocks/${data.ticker}`, {data, revision:stockRecord.revision});
    stocks = await api("/api/stocks");
    await chooseStock(data.ticker); $("stock-editor").close();
    status(saved.financial_review_reset ? "Company data saved. Changed financial inputs need a new review. Reopen Edit company data to review the saved figures; unresolved reporting issues remain open." : "Company data saved. Previous version backed up; valuation inputs refreshed.");
  } catch(error) {$("stock-editor-error").textContent = error.message;}
};

function openPolicyEditor() {
  const policy = policyRecord.data;
  $("policy-editor-error").textContent = "";
  $("policy-defaults").replaceChildren();
  const keys = new Set(["growth", "terminal_growth", "discount_rate", "discount", "required_yield", "multiple", ...Object.keys(policy.defaults)]);
  for (const key of keys) {
    const field = policy.fields[key], rate = field.unit === "rate";
    const value = policy.defaults[key] == null ? "" : policy.defaults[key] * (rate ? 100 : 1);
    const row = document.createElement("div");
    row.innerHTML = `<label for="policy-default-${escapeHtml(key)}">${escapeHtml(field.label)} (${rate ? "%" : escapeHtml(field.unit)})</label><input id="policy-default-${escapeHtml(key)}" data-key="${escapeHtml(key)}" type="number" step="any" value="${escapeHtml(value)}">`;
    $("policy-defaults").append(row);
  }
  $("policy-recommendations").replaceChildren();
  for (const [profile, methods] of Object.entries(policy.recommendations)) {
    const group = document.createElement("fieldset"); group.dataset.profile = profile;
    group.innerHTML = `<legend>${escapeHtml(profile.replaceAll("_", " "))}</legend>`;
    for (const key of [...methods, ...Object.keys(policy.methods).filter(key=>!methods.includes(key))]) {
      const label = document.createElement("label"); label.className = "confirmation";
      const check = document.createElement("input"); check.type = "checkbox"; check.value = key; check.checked = methods.includes(key);
      const text = document.createElement("span"); text.textContent = policy.methods[key].name;
      label.append(check, text); group.append(label);
    }
    $("policy-recommendations").append(group);
  }
  $("policy-editor").showModal();
}
$("close-policy-editor").onclick = () => $("policy-editor").close();
$("policy-advanced").onclick = () => {$("policy-editor").close();openEditor("policy");};
$("policy-editor-form").onsubmit = async event => {
  event.preventDefault();
  try {
    const data = JSON.parse(JSON.stringify(policyRecord.data));
    for (const input of $("policy-defaults").querySelectorAll("input")) {
      const key = input.dataset.key;
      if (input.value === "") delete data.defaults[key];
      else data.defaults[key] = Number(input.value)/(data.fields[key].unit === "rate" ? 100 : 1);
    }
    for (const group of $("policy-recommendations").querySelectorAll("fieldset")) {
      data.recommendations[group.dataset.profile] = [...group.querySelectorAll("input:checked")].map(input=>input.value);
    }
    policyRecord = await api("/api/policy", {data, revision:policyRecord.revision});
    renderMethods($("method").value); $("policy-editor").close();
    status("Policies saved; review the updated valuation inputs.");
  } catch(error) {$("policy-editor-error").textContent = error.message;}
};

function renderRateHelp() {
  for(const [key,text] of Object.entries(policyRecord.data.rate_help || {})) {
    const parent=$("rate-"+key)?.parentElement;
    if(parent && !parent.querySelector("details")) {
      const details=document.createElement("details");details.className="field-help";
      const summary=document.createElement("summary");summary.textContent="What is this?";
      const paragraph=document.createElement("p");paragraph.className="help";paragraph.textContent=text;
      details.append(summary,paragraph);parent.append(details);
    }
  }
}
function rememberDerivation(item) {
  derivations=derivations.filter(d=>d.output_field!==item.output_field);
  item.calculated_at=new Date().toISOString();
  item.source_note="Helper entries are editable; source snapshots are reference evidence, not proof of each entered value.";
  derivations.push(item);
}
function renderCashHelper() {
  $("cash-helper").replaceChildren();
  if($("method").value==='sotp') renderComponentHelper();
  if(["dcf_fcff","dcf_fcfe"].includes($("method").value)) renderCashStatementHelper();
  if($("method").value!=="dcf_fcff") return;
  const keys=["operating_profit","depreciation","other_noncash","capital_spending","additional_capex","working_capital_increase","debt","cash","other_claims"];
  const details=document.createElement("details");details.className="advanced";
  details.innerHTML='<summary>Calculate cash flow and net debt from report figures</summary><p class="help">Use annual figures in full pesos, with consistent company scope and period. Business cash = Operating profit × (1 − tax rate) + Depreciation + Other non-cash adjustments − Equipment/property spending − Other capital investment − Working-capital increase. Net claims = Debt − Available cash + Other claims. Enter zero only after checking an adjustment does not apply.</p><div class="fields cash-helper-fields"></div><button id="apply-derived-cash" type="button" class="quiet">Use calculated figures</button>';
  for(const key of keys) {
    const field=policyRecord.data.fields[key],value=stockRecord.data.fields[key]?.value??"";
    const row=document.createElement("div");row.innerHTML=`<label for="derive-${key}">${escapeHtml(field.label)}</label><input id="derive-${key}" type="number" step="any" value="${escapeHtml(value)}"><p class="help">${escapeHtml(field.help)}</p>`;
    details.querySelector(".fields").append(row);
  }
  $("cash-helper").append(details);
  const wc=document.createElement("details");
  wc.innerHTML='<summary>Calculate the working-capital increase</summary><p class="help">Working capital here = Operating trade receivables + Inventory − Operating trade payables. Increase = current-year total − previous-year total. Use comparable year-end balances; add other operating movements to the result if material. This is a starting bridge, not a substitute for reviewing the cash-flow notes.</p><div class="fields"></div><button type="button" id="derive-working-capital">Use working-capital increase</button>';
  const wcKeys=["receivables","inventory","payables","previous_receivables","previous_inventory","previous_payables","other_working_capital_change"];
  for(const key of wcKeys){const row=document.createElement("div");row.innerHTML=`<label for="derive-${key}">${escapeHtml(policyRecord.data.fields[key].label)}</label><input type="number" step="any" id="derive-${key}" value="${escapeHtml(stockRecord.data.fields[key]?.value??"")}">`;wc.querySelector(".fields").append(row);}
  details.append(wc);
  $("derive-working-capital").onclick=()=>{
    if(wcKeys.some(k=>$("derive-"+k).value==="")){status("Enter all six balances and the other operating change; use zero only when verified.");return;}
    const v=Object.fromEntries(wcKeys.map(k=>[k,Number($("derive-"+k).value)]));
    const change=v.receivables+v.inventory-v.payables-(v.previous_receivables+v.previous_inventory-v.previous_payables)+v.other_working_capital_change;
    $("derive-working_capital_increase").value=change;
    $("scenario-notes").value+=`\nWorking-capital increase = (${v.receivables} + ${v.inventory} − ${v.payables}) − (${v.previous_receivables} + ${v.previous_inventory} − ${v.previous_payables}) + ${v.other_working_capital_change} = ${change}.`;
    rememberDerivation({output_field:"working_capital_increase",value:change,inputs:v,formula:"current receivables + inventory − payables − (previous receivables + inventory − payables) + other operating change",sources:structuredClone(stockRecord.data.fields)});
    invalidate();status("Working-capital increase filled. Use calculated figures to update cash flow.");
  };
  $("apply-derived-cash").onclick=()=>{
    const values=Object.fromEntries(keys.map(key=>[key,$("derive-"+key).value===""?null:Number($("derive-"+key).value)]));
    let applied=false;
    if(["operating_profit","depreciation","other_noncash","capital_spending","additional_capex","working_capital_increase"].every(k=>values[k]!=null)) {
      if($("rate-tax").value===""){status("Enter the tax rate in the discount rate calculator; blank is not zero.");return;}
      const tax=Number($("rate-tax").value)/100;
      if(!Number.isFinite(tax)||tax<0||tax>1){status("Check the tax rate in the discount rate calculator.");return;}
      const cash=values.operating_profit*(1-tax)+values.depreciation+values.other_noncash-Math.abs(values.capital_spending)-Math.abs(values.additional_capex)-values.working_capital_increase;
      $("input-cash_flow").value=cash;applied=true;
      $("scenario-notes").value+=`\nBusiness cash = ${values.operating_profit} × (1 − ${tax}) + ${values.depreciation} + ${values.other_noncash} − ${Math.abs(values.capital_spending)} − ${Math.abs(values.additional_capex)} − ${values.working_capital_increase} = ${cash}.`;
      rememberDerivation({output_field:"cash_flow",value:cash,inputs:{...values,tax},formula:"operating profit × (1 − tax) + depreciation + other noncash − abs(capital spending) − abs(other investment) − working-capital increase",sources:structuredClone(stockRecord.data.fields)});
    }
    if(values.debt!=null && values.cash!=null && values.other_claims!=null){const claims=values.debt-values.cash+values.other_claims;$("input-net_debt").value=claims;applied=true;$("scenario-notes").value+=`\nNet claims = ${values.debt} − ${values.cash} + ${values.other_claims} = ${claims}.`;rememberDerivation({output_field:"net_debt",value:claims,inputs:{debt:values.debt,cash:values.cash,other_claims:values.other_claims},formula:"debt − available cash + other claims",sources:structuredClone(stockRecord.data.fields)});}
    if(applied){invalidate();status("Calculated figures applied. Review before valuing.");}else status("Complete the cash-flow inputs and adjustments, or debt, available cash and other claims. Missing is not zero.");
  };
}

let importMode="offline", importPreview=null;
$("report-file").onchange=()=>{
  $("report-period").value="";$("report-scale").value="1";$("report-pages").value="";
  importPreview=null;$("import-proposals").replaceChildren();$("apply-import").disabled=true;$("import-confirmed").checked=false;
};
async function openImport(mode) {
  $("import-findings").replaceChildren();
  if(!stockRecord) return;
  importMode=mode;importPreview=null;
  $("import-options").hidden=mode==="online";
  $("import-folder").textContent=mode==="online"?"Fetch the latest available PSE EDGE price, EPS and book value. Saved data remains unchanged until you apply the selected updates.":`Put downloaded PDF, saved HTML or text reports in reports/${stockRecord.data.ticker}/. Select one report below. Saved PSE EDGE HTML supplies its dates. For PDF/text, confirm that report's annual period and units.`;
  $("run-import").textContent=mode==="online"?"Fetch from PSE EDGE":"Scan selected report";
  $("import-status").textContent="";$("import-proposals").replaceChildren();$("apply-import").disabled=true;$("import-confirmed").checked=false;
  $("import-dialog").showModal();
  if(mode==="offline") {
    $("run-import").disabled=true;
    try {
      const listing=await api(`/api/reports/${stockRecord.data.ticker}`);
      $("import-folder").textContent=`Company folder: ${listing.folder}. Copy this path into File Explorer to add PDF, saved HTML or text reports. Reopen this window after adding a file. Review the proposed rows; missing figures must be entered through Edit company data. Assumptions still need your own basis.`;
      $("report-file").replaceChildren();
      for(const name of listing.files){const option=document.createElement("option");option.value=name;option.textContent=name;$("report-file").append(option);}
      $("report-period").value="";$("report-scale").value="1";$("report-pages").value="";
      $("import-status").textContent=listing.files.length?"Select one report and confirm its own period and units.":"No reports found. Add a file, then reopen this window.";
      $("run-import").disabled=!listing.files.length;
    }catch(error){$("import-status").textContent=error.message;}
  }
}
$("refresh-online").onclick=async()=>{await openImport("online");$("run-import").disabled=false;$("run-import").click();};
$("scan-reports").onclick=()=>openImport("offline");
$("close-import").onclick=()=>$("import-dialog").close();
$("run-import").onclick=async()=>{
  $("import-confirmed").checked=false;
  $("run-import").disabled=true;$("apply-import").disabled=true;$("import-status").textContent=importMode==="online"?"Fetching official pages…":"Reading local reports…";
  try {
    importPreview=await api(`/api/update/${stockRecord.data.ticker}`,{mode:importMode,file:$("report-file").value,pages:$("report-pages").value,period:$("report-period").value,scale:Number($("report-scale").value)});
    $("import-folder").textContent=importMode==="offline"?importPreview.folder:$("import-folder").textContent;
    $("import-status").textContent=[`${importPreview.candidates.length} proposed updates.`,...importPreview.warnings].join("\n");
    $("import-proposals").innerHTML=`<table><thead><tr><th>Apply</th><th>Figure</th><th>Saved</th><th>New</th><th>Period/date</th><th>Source / explanation</th></tr></thead><tbody>${importPreview.candidates.map(c=>`<tr><td><input type="checkbox" aria-label="Apply ${escapeHtml(c.key)}" value="${c.id}"></td><td>${escapeHtml(policyRecord.data.fields[c.key]?.label||c.key)}</td><td>${c.previous==null?"—":numeric(c.previous)}</td><td>${numeric(c.value)}</td><td>${escapeHtml(c.as_of)}</td><td class="import-note">${escapeHtml(c.source_file||"PSE EDGE")} · page ${escapeHtml(c.source_page||"—")} · ${escapeHtml(c.unit||"PHP/share")} · scale ${escapeHtml(c.scale??1)}<br>${escapeHtml(c.note)}</td></tr>`).join("")}</tbody></table>`;
    $("import-findings").innerHTML=(importPreview.findings || []).length ? '<h3>Disclosure passages to review</h3><p class="help">Keyword matches, not confirmed accounting problems. Check context, including negation and whether the issue is historical or resolved. Only selected passages are saved as unresolved review items. At most 20 matches per file; selected pages only.</p>'+importPreview.findings.map(f=>`<label class="confirmation"><input type="checkbox" value="${escapeHtml(f.id)}"><span>${escapeHtml(f.category)} · ${escapeHtml(f.source_file)}, page ${escapeHtml(f.source_page)}<br>${escapeHtml(f.excerpt)}</span></label>`).join('') : (importMode==='online' ? '<p class="help">Disclosure screening requires a local report; online refresh checks the summary and price only.</p>' : '<p class="help">No disclosure keywords detected in the scanned text. This does not establish that the report is free of issues.</p>');
    $("apply-import").disabled=!importPreview.candidates.length && !(importPreview.findings || []).length;
  }catch(error){$("import-status").textContent=error.message;}finally{$("run-import").disabled=false;}
};
$("apply-import").onclick=async()=>{
  try {
    const selected=[...$("import-proposals").querySelectorAll("input:checked")].map(input=>input.value);
    const selected_findings=[...$("import-findings").querySelectorAll("input:checked")].map(input=>input.value);
    const outcome=await api("/api/update-apply",{token:importPreview.token,selected,selected_findings,confirmed:$("import-confirmed").checked});
    await chooseStock(stockRecord.data.ticker);$("import-dialog").close();status(`${outcome.updated} figures updated; ${outcome.flagged || 0} disclosure passages saved.${outcome.reporting_review_required ? " Reporting review required; prior confirmation does not cover these imports." : ""}`);
  }catch(error){$("import-status").textContent=error.message;}
};


function renderCashStatementHelper(){
  const method=$("method").value;
  const definitions={
    operating_cash_flow:["Reported operating cash flow","Net cash from operating activities after reported cash taxes. Do not deduct working capital again."],
    interest_paid:["Interest paid on financing debt","Include financing interest once. Exclude amounts already counted in capital investment; explain your treatment."],
    interest_outside_cfo:["That interest paid outside operating cash flow","Part of the above interest classified outside operating activities. Enter zero if all is already deducted in operating cash."],
    tax:["Tax rate for the interest deduction (%)","Reviewed rate for the interest tax shield, not necessarily the headline income-tax rate."],
    capital_spending:["Equipment and property investment","Positive investment amount, consistent with the chosen lease treatment."],
    additional_capex:["Other capital investment","Software, intangibles and other investment not counted above. Enter a reviewed zero if none."],
    cfo_adjustment:["Other operating-cash adjustments","Signed adjustment: positive adds cash, negative subtracts cash. Explain normalization and lease-payment adjustments."],
    investment_adjustment:["Investment adjustments","Signed adjustment to cash after investment. A negative amount adds investment deductions, including any required non-cash lease additions."],
    debt:["Financing debt balance","Use the same financing/lease scope as the cash flow and discount rate."],
    cash:["Available excess cash","Exclude restricted cash and cash needed for operations when appropriate."],
    other_claims:["Other claims ahead of common shareholders","Include preferred and minority claims when required by the cash-flow ownership scope. Avoid double counting."],
    borrowings:["New debt financing","New borrowing within the chosen financing scope; explain non-cash lease financing if included."],
    repayments:["Debt principal repaid","Principal only, not interest. Include lease principal only when leases are financing."],
    common_adjustment:["Adjustment to cash attributable to common shareholders","Signed adjustment for non-common or minority cash flows not already removed. Explain ownership scope; cash distributions alone may not capture the full claim."]
  };
  const savedBridge=stockRecord.data.fields[baselineKey(method,'cash_flow')]?.cash_flow_reconciliation;
  const keys=['operating_cash_flow','interest_paid','interest_outside_cfo','tax','capital_spending','additional_capex','cfo_adjustment','investment_adjustment',...(method==='dcf_fcff'?['debt','cash','other_claims']:['borrowings','repayments','common_adjustment'])];
  const wrapper=document.createElement('div');wrapper.id='cash-statement-helper';
  wrapper.innerHTML='<details class="advanced"><summary>Reconcile a cash-flow statement</summary><p class="help">Annual figures in full pesos. Every adjustment needs a value, including reviewed zeros. Classification choices remain your responsibility.</p><div class="fields"></div><label>Period covered<select id="bridge-period-type"><option value="">Choose</option><option value="annual">Full year</option><option value="ttm">Trailing 12 months</option></select></label><label>Period end<input id="bridge-period-end" type="date"></label><label>Lease treatment<select id="bridge-lease"><option value="">Choose</option><option value="financing">Financing debt</option><option value="operating">Operating expense</option><option value="none">No material leases</option></select></label><p class="help">Financing leases: align lease investment, new financing, principal, interest and debt. Operating leases: include lease cash costs in normalized operating cash and exclude lease financing from debt/borrowing inputs. Explain adjustments below; the app does not reclassify leases automatically.</p><label>Sources and statement references<textarea id="bridge-source-note" rows="2"></textarea></label><label>Company / ownership scope<textarea id="bridge-scope-note" rows="2" placeholder="Consolidated or parent; treatment of minority and preferred interests"></textarea></label><label>Lease treatment explanation<textarea id="bridge-lease-note" rows="2"></textarea></label><label>Adjustment explanations<textarea id="bridge-adjustment-note" rows="2" placeholder="Explain signed adjustments, or why zero is appropriate"></textarea></label><button id="bridge-apply" type="button" class="quiet">Use reconciled cash flow</button><button id="bridge-save" type="button" class="quiet" disabled>Save cash-flow baseline and evidence</button><p class="help">Saves this cash-flow total and bridge to the company file for offline checks. Net claims remain separate. Saving does not approve the source assumptions.</p><div id="bridge-result" role="status"></div></details>';
  for(const key of keys){
    const [label,help]=definitions[key], row=document.createElement('div');
    const saved=savedBridge?.inputs?.[key] ?? stockRecord.data.fields[key]?.value;
    row.innerHTML=`<label for="bridge-${key}">${escapeHtml(label)}</label><input id="bridge-${key}" type="number" step="any" value="${saved==null?'':escapeHtml(key==='tax'?saved*100:saved)}"><p class="help">${escapeHtml(help)}</p>`;
    wrapper.querySelector('.fields').append(row);
  }
  $("cash-helper").append(wrapper);
  if(savedBridge?.basis){
    for(const [id,key] of Object.entries({'period-type':'period_type','period-end':'period_end',lease:'lease_treatment','source-note':'source_note','scope-note':'scope_note','lease-note':'lease_note','adjustment-note':'adjustment_note'})) $('bridge-'+id).value=savedBridge.basis[key] || '';
  }
  let bridgeVersion=0, latestBridge=null;
  wrapper.addEventListener('input',()=>{bridgeVersion++;latestBridge=null;$('bridge-save').disabled=true;});
  $('bridge-save').onclick=async()=>{
    if(!latestBridge)return;
    const ticker=stockRecord.data.ticker, data=structuredClone(stockRecord.data), record=structuredClone(latestBridge);
    const key=baselineKey(method,'cash_flow');
    data.fields[key]={value:record.cash_flow,period_type:record.basis.period_type,period_end:record.basis.period_end,
      as_of:record.basis.period_end,status:'needs_review',note:record.basis.source_note,unit:'PHP',
      cash_flow_reconciliation:{method:record.method,reconciliation_version:record.reconciliation_version,inputs:record.inputs,basis:record.basis}};
    $('bridge-save').disabled=true;
    try{
      const saved=await api(`/api/stocks/${ticker}`,{data,revision:stockRecord.revision});
      if(!wrapper.isConnected || stockRecord.data.ticker!==ticker)return;
      stockRecord=saved;
      $('bridge-result').textContent='Cash-flow baseline and evidence saved. Reporting review required; net claims were not saved.';
      invalidate();
    }catch(error){if(wrapper.isConnected){$('bridge-result').textContent=error.message;$('bridge-save').disabled=!latestBridge;}}
  };
  $('bridge-apply').onclick=async()=>{
    const version=inputVersion, submittedBridgeVersion=++bridgeVersion;
    try{
      const inputs=Object.fromEntries(keys.map(key=>[key,$('bridge-'+key).value===''?null:Number($('bridge-'+key).value)/(key==='tax'?100:1)]));
      const basis={period_type:$('bridge-period-type').value,period_end:$('bridge-period-end').value,lease_treatment:$('bridge-lease').value,source_note:$('bridge-source-note').value,scope_note:$('bridge-scope-note').value,lease_note:$('bridge-lease-note').value,adjustment_note:$('bridge-adjustment-note').value};
      const reconciled=await api('/api/reconcile-cash',{method,inputs,basis});
      if(version!==inputVersion || submittedBridgeVersion!==bridgeVersion || !wrapper.isConnected)return;
      latestBridge=reconciled;$('bridge-save').disabled=false;
      $('input-cash_flow').value=reconciled.cash_flow;
      if(method==='dcf_fcff')$('input-net_debt').value=reconciled.net_debt;
      const evidence={inputs:reconciled.inputs,reconciliation:reconciled,sources:structuredClone(stockRecord.data.fields),formula:reconciled.steps.map(step=>step.label).join('; ')};
      rememberDerivation({...evidence,output_field:'cash_flow',value:reconciled.cash_flow});
      if(method==='dcf_fcff')rememberDerivation({...evidence,output_field:'net_debt',value:reconciled.net_debt});
      invalidate();
      $('bridge-result').innerHTML=reconciled.steps.map(step=>`<p>${escapeHtml(step.label)} = <strong>${numeric(step.value)}</strong></p>`).join('')+reconciled.warnings.map(note=>`<p class="warning">${escapeHtml(note)}</p>`).join('');
      $('scenario-notes').value+='\nCash-flow reconciliation: '+JSON.stringify(basis);
    }catch(error){if(version===inputVersion && submittedBridgeVersion===bridgeVersion && wrapper.isConnected)$('bridge-result').textContent=error.message;}
  };
}

function renderEpsEvidence(fieldset, original) {
  const bridge=original.eps_bridge || {}, panel=document.createElement('details');
  panel.id='eps-evidence';
  panel.innerHTML='<summary>Trailing-year EPS calculation and review</summary><p class="help">For December year ends: annual EPS + current year-to-date EPS − prior year-to-date EPS. Use matching basic EPS and review share changes and restatements. Saving changed figures resets the review; reopen to record a new review.</p><div class="fields"></div>';
  for(const [key,label,type] of [
    ['annual_eps','Previous full-year basic EPS','number'],['annual_end','Full-year end','date'],
    ['current_ytd_eps','Current year-to-date basic EPS','number'],['current_ytd_end','Current YTD end','date'],
    ['prior_ytd_eps','Prior year-to-date basic EPS','number'],['prior_ytd_end','Prior YTD end','date'],
    ['reviewed_on','Comparability review date','date']]) {
    const row=document.createElement('label');row.textContent=label;
    const input=document.createElement('input');input.type=type;input.step='any';input.id='eps-'+key;input.dataset.epsKey=key;input.value=bridge[key]??'';row.append(input);panel.querySelector('.fields').append(row);
  }
  const review=document.createElement('div');
  review.innerHTML='<label>Share basis and revisions<select id="eps-review-status" data-eps-key="review_status"><option value="unreviewed">Not reconciled</option><option value="reconciled">Reconciled by me</option></select></label><label>Sources and comparability explanation<textarea id="eps-review-note" data-eps-key="review_note" rows="3"></textarea></label><button type="button" id="eps-use-total" class="quiet">Use calculated trailing EPS</button><p id="eps-total-message" role="status"></p>';
  panel.append(review);review.querySelector('select').value=bridge.review_status || 'unreviewed';review.querySelector('textarea').value=bridge.review_note || '';
  review.querySelector('button').onclick=()=>{
    const values=['annual_eps','current_ytd_eps','prior_ytd_eps'].map(key=>panel.querySelector('#eps-'+key).value);
    if(values.some(value=>value==='' || !Number.isFinite(Number(value)))) {panel.querySelector('#eps-total-message').textContent='Enter all three EPS figures.';return;}
    const total=Number(values[0])+Number(values[1])-Number(values[2]);
    $('baseline-eps').value=Number(total.toPrecision(12));$('baseline-duration-eps').value='ttm';$('baseline-period-eps').value=panel.querySelector('#eps-current_ytd_end').value;
    $('baseline-status-eps').value='needs_review';review.querySelector('select').value='unreviewed';fieldset.dataset.changed='true';
    panel.querySelector('#eps-total-message').textContent=`${values[0]} + ${values[1]} − ${values[2]} = ${numeric(total)}. Applied; check dates and share basis before relying on it.`;
  };
  fieldset.append(panel);
}

$('try-tel-case').onclick=async()=>{
  const button=$('try-tel-case');button.disabled=true;
  try {
    const startRequest=stockRequest;
    const example=await api('/api/examples/tel');
    if(startRequest!==stockRequest)return;
    const expectedRequest=stockRequest+1;
    await chooseStock('TEL');
    if(stockRequest!==expectedRequest)return;
    const windowStart=String(Number(example.analysis_date.slice(0,4))-1)+example.analysis_date.slice(4);
    const dividend=example.dividend_events.filter(e=>e.share_class==='common' && e.kind==='regular' && e.payment_date<=example.analysis_date && e.payment_date>windowStart).reduce((total,e)=>total+e.amount_per_share,0);
    renderMethods('ddm');
    renderFields({dividend,discount_rate:example.assumptions.discount_rate,terminal_growth:example.assumptions.terminal_growth,price:example.price.value});
    $('method-readiness').textContent='Dated research inputs loaded. Review assumptions, then calculate.';
    $('scenario-name').value='TEL research case · '+example.analysis_date;
    $('scenario-notes').value=JSON.stringify({research_case:example.title,analysis_date:example.analysis_date,price:example.price,assumptions:example.assumptions,dividend_events:example.dividend_events,source_review:example.source_review,annual_source_comparison:example.annual_source_comparison},null,2);
    const panel=$('research-case');panel.hidden=false;
    panel.innerHTML=`<h2>TEL research case · ${escapeHtml(example.analysis_date)}</h2><p class="warning">Illustrative dividend scenario, not a verified price target. ${escapeHtml(example.source_review.qualification)}</p><p>Reference price: ${peso(example.price.value)} · ${escapeHtml(example.price.as_of)}. ${escapeHtml(example.price.kind)}.</p><details><summary>Sources and assumptions</summary><p>${escapeHtml(example.assumptions.dividend_basis)}</p><p>${escapeHtml(example.assumptions.discount_rate_basis)}</p><p>${escapeHtml(example.assumptions.growth_basis)}</p>${example.dividend_events.map(e=>`<p>${escapeHtml(e.payment_date)} · ${peso(e.amount_per_share)} per common share · ${safeLink(e.source_url,'Dividend declaration ↗')}</p>`).join('')}<p>${safeLink(example.annual_source_comparison.source_url,'Annual filing ↗')} · ${safeLink(example.source_review.disclosure_url,'Reporting qualification ↗')}</p></details><p class="help">These editable scenario inputs do not replace your company brain. Sources and qualifications are included in the analysis notes when you save.</p>`;
    status('TEL case loaded. Review inputs before calculating.');
  }catch(error){status(error.message);}finally{button.disabled=false;}
};

$('try-bdo-case').onclick=async()=>{
  const button=$('try-bdo-case');button.disabled=true;
  try {
    const startRequest=stockRequest;
    const example=await api('/api/examples/bdo');
    if(startRequest!==stockRequest)return;
    const expectedRequest=stockRequest+1;
    await chooseStock('BDO');
    if(stockRequest!==expectedRequest)return;
    $('advanced-methods').checked=true;
    renderMethods('justified_pb');
    renderFields({bvps:example.reported.bvps,roe:example.assumptions.roe,
      discount_rate:example.assumptions.discount_rate,terminal_growth:example.assumptions.terminal_growth,
      price:example.reported.period_end_price});
    $('method-readiness').textContent='Historical bank example loaded. Review assumptions, then calculate.';
    $('scenario-name').value='BDO bank example · '+example.financial_period_end;
    $('scenario-notes').value=JSON.stringify({research_case:example.title,...example},null,2);
    const panel=$('research-case');panel.hidden=false;
    panel.innerHTML=`<h2>BDO bank example · ${escapeHtml(example.financial_period_end)}</h2><p class="warning">${escapeHtml(example.scope)}</p><p>Historical reference price: ${peso(example.reported.period_end_price)}. Book value per common share: ${peso(example.reported.bvps)}.</p><details><summary>Sources and assumptions</summary><p>${escapeHtml(example.assumptions.roe_basis)}</p><p>${escapeHtml(example.assumptions.return_basis)}</p><p>${escapeHtml(example.assumptions.growth_basis)}</p><p>${safeLink(example.sources.share_information,'Common equity and share information ↗')} · ${safeLink(example.sources.results,'Annual results ↗')} · ${safeLink(example.common_equity_reconciliation.source_url+'#page=197','Audited common-equity bridge (pages 197, 200) ↗')}</p>${example.limitations.map(note=>`<p>${escapeHtml(note)}</p>`).join('')}</details><p class="help">Scenario inputs leave your company brain unchanged. Sources, assumptions and limitations are included in saved analysis notes.</p>`;
    const policy=example.dividend_policy_check;
    if(policy){
      const annual=policy.quarterly_regular_dividend*policy.payments_per_year;
      const next=annual*(1+example.assumptions.terminal_growth);
      const required=example.reported.bvps*(example.assumptions.roe-example.assumptions.terminal_growth);
      const check=document.createElement('p');check.className='warning';
      check.innerHTML=`Bundled scenario check: annualized regular cash policy ${peso(annual)}; next-year cash at the selected growth ${peso(next)}; equivalent-model distribution ${peso(required)}. Additional distributions or capital release need support. This comparison uses the original example assumptions. ${safeLink(policy.source_url,'Dividend policy ↗')}`;
      panel.append(check);
    }
    status('BDO example loaded. Review inputs before calculating.');
  }catch(error){status(error.message);}finally{button.disabled=false;}
};

function renderComponentHelper(saved){
  saved=saved || Object.values(stockRecord.data.fields.asset_value?.sotp_components || {});
  const panel=document.createElement('details');panel.id='component-helper';panel.className='advanced';
  panel.innerHTML='<summary>Add up owned businesses</summary><p class="help">Enter full pesos. Enterprise value needs subsidiary net claims deducted first. Equity value already includes that deduction. Already-owned equity also includes your ownership percentage. Save the analysis to retain scenario rows. Save component baseline and evidence explicitly replaces the owned-asset total in the company brain; parent claims remain separate.</p><div id="component-rows"></div><button type="button" id="component-add" class="quiet">Add business</button> <button type="button" id="component-apply" class="quiet">Use component total</button><div id="component-result" role="status"></div>';
  $('cash-helper').append(panel);
  const save=document.createElement('button');save.id='component-save';save.type='button';save.className='quiet';save.textContent='Save component baseline and evidence';save.disabled=true;panel.append(save);
  let version=0, latest=null;
  function changed(){version++;latest=null;save.disabled=true;}
  panel.addEventListener('input',changed);
  function addRow(item={}){
    const row=document.createElement('fieldset');row.className='fields';
    row.innerHTML='<legend>Business or asset</legend>';
    const controls=[['name','Name','text'],['value','Starting value (PHP)','number'],['ownership','Ownership (%)','number'],['net_claims','Subsidiary net claims (PHP)','number'],['as_of','Valuation date','date'],['source_note','Source and valuation basis','text']];
    const choice=document.createElement('label');choice.textContent='Starting value represents';
    const select=document.createElement('select');select.dataset.component='basis';
    for(const [value,label] of [['equity','Equity value'],['enterprise','Enterprise value (before net claims)'],['attributable','Already-owned equity value']]){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);}
    select.value=item.basis || 'equity';choice.append(select);row.append(choice);
    for(const [key,label,type] of controls){
      const field=document.createElement('label');field.textContent=label;
      const input=document.createElement('input');input.type=type;input.step='any';input.dataset.component=key;
      input.value=item[key]==null?'':key==='ownership'?item[key]*100:item[key];field.append(input);row.append(field);
    }
    function scope(){
      const debt=row.querySelector('[data-component="net_claims"]'),owned=row.querySelector('[data-component="ownership"]');
      debt.disabled=select.value!=='enterprise';if(debt.disabled)debt.value='0';
      owned.disabled=select.value==='attributable';if(owned.disabled)owned.value='100';
    }
    select.onchange=()=>{changed();scope();};scope();
    const remove=document.createElement('button');remove.type='button';remove.className='quiet';remove.textContent='Remove business';remove.onclick=()=>{row.remove();changed();};row.append(remove);
    $('component-rows').append(row);changed();
  }
  for(const item of saved.length?saved:[{}])addRow(item);
  $('component-add').onclick=()=>addRow();
  $('component-apply').onclick=async()=>{
    const submitted=version, valuationVersion=inputVersion;
    try{
      const components=[...$('component-rows').children].map(row=>Object.fromEntries([...row.querySelectorAll('[data-component]')].map(input=>[input.dataset.component,input.type==='number'?(input.value===''?null:Number(input.value)/(input.dataset.component==='ownership'?100:1)):input.value])));
      const result=await api('/api/reconcile-components',{components});
      if(!panel.isConnected || submitted!==version || valuationVersion!==inputVersion)return;
      latest=result;save.disabled=false;
      $('input-asset_value').value=result.asset_value;
      rememberDerivation({output_field:'asset_value',value:result.asset_value,component_reconciliation:result,formula:'Sum of component equity values multiplied by ownership'});
      invalidate();
      $('component-result').innerHTML=result.steps.map(s=>`<p>${escapeHtml(s.name)}: ${escapeHtml(s.formula)} = ${peso(s.attributable_value)}</p>`).join('')+result.warnings.map(w=>`<p class="warning">${escapeHtml(w)}</p>`).join('');
    }catch(error){if(panel.isConnected && submitted===version)$('component-result').textContent=error.message;}
  };
  save.onclick=async()=>{
    if(!latest)return;
    const record=structuredClone(latest),data=structuredClone(stockRecord.data),ticker=data.ticker;
    const dates=record.components.map(c=>c.as_of).sort();
    data.fields.asset_value={value:record.asset_value,status:'needs_review',unit:'PHP',period_type:'point_in_time',
      period_end:dates.at(-1),as_of:dates.at(-1),note:'Sum of saved SOTP components; inspect individual sources, dates and ownership. Parent claims are separate.',
      sotp_components:Object.fromEntries(record.components.map((c,i)=>['component_'+(i+1),c]))};
    save.disabled=true;
    try{
      const stored=await api(`/api/stocks/${ticker}`,{data,revision:stockRecord.revision});
      if(!panel.isConnected || stockRecord.data.ticker!==ticker)return;
      stockRecord=stored;invalidate();
      $('component-result').textContent='Component baseline and evidence saved. Review required. Parent claims, shares and discount were not saved.';
    }catch(error){if(panel.isConnected){$('component-result').textContent=error.message;save.disabled=!latest;}}
  };
}
