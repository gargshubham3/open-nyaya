from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from nyaya.mapper import LawMapper
from nyaya.auditor import CaseAuditor
from nyaya.parser import FIRParser
from nyaya.drafter import BailDrafter
from nyaya.models import FIRDetails, AccusedPerson, SectionCharge, MappingResult, AuditReport, BailApplicationDraft

app = FastAPI(
    title="open-nyaya",
    description="Open-Source Legal AI & Statutory Computing Toolkit for Indian Law",
    version="0.1.0"
)

mapper = LawMapper()
auditor = CaseAuditor(mapper)
parser = FIRParser(mapper)
drafter = BailDrafter(mapper)

class LookupRequest(BaseModel):
    act: str
    section: str

class TranslateRequest(BaseModel):
    charges: str

class SearchRequest(BaseModel):
    query: str
    act: Optional[str] = None
    limit: Optional[int] = 10

class AuditRequest(BaseModel):
    fir_text: Optional[str] = None
    fir_details: Optional[FIRDetails] = None

class DraftBailRequest(BaseModel):
    accused_name: str
    fir_number: str
    police_station: str
    district: str
    state: str = "Uttar Pradesh"
    sections_charged: str
    custody_days: int = 30
    section_35_notice_violated: bool = True
    videography_missing: bool = True

@app.post("/api/lookup", response_model=Optional[MappingResult])
def api_lookup(req: LookupRequest):
    res = mapper.lookup(req.act, req.section)
    if not res:
        raise HTTPException(status_code=404, detail="Section mapping not found")
    return res

@app.post("/api/translate", response_model=List[MappingResult])
def api_translate(req: TranslateRequest):
    return mapper.translate_string(req.charges)

@app.post("/api/search", response_model=List[MappingResult])
def api_search(req: SearchRequest):
    return mapper.search(req.query, act=req.act, limit=req.limit or 10)

@app.post("/api/audit", response_model=AuditReport)
def api_audit(req: AuditRequest):
    if req.fir_details:
        fir_obj = req.fir_details
    elif req.fir_text:
        fir_obj = parser.parse_text(req.fir_text)
    else:
        raise HTTPException(status_code=400, detail="Provide either fir_text or fir_details")
    return auditor.audit(fir_obj)

@app.post("/api/draft-bail", response_model=BailApplicationDraft)
def api_draft_bail(req: DraftBailRequest):
    translated = mapper.translate_string(req.sections_charged)
    charges = [
        SectionCharge(act=t.source.act if t.source else "IPC", section=t.source.section if t.source else t.lookup_key)
        for t in translated
    ] if translated else [SectionCharge(act="IPC", section="420")]

    fir_obj = FIRDetails(
        fir_number=req.fir_number,
        year=2026,
        police_station=req.police_station,
        district=req.district,
        state=req.state,
        accused_list=[AccusedPerson(name=req.accused_name, is_arrested=True, custody_days=req.custody_days)],
        sections_charged=charges,
        section_35_notice_issued=False if req.section_35_notice_violated else True,
        videography_recorded=False if req.videography_missing else True,
        recovery_made=True if req.videography_missing else False
    )
    report = auditor.audit(fir_obj)
    return drafter.draft_bail(fir_obj, report)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>open-nyaya | Indian Legal AI Toolkit</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">
    <!-- Header -->
    <header class="border-b border-slate-800 bg-slate-950/70 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">⚖️</span>
                <div>
                    <h1 class="text-xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">open-nyaya</h1>
                    <p class="text-xs text-slate-400">Open-Source Criminal Legal Computing for Modern India (BNS • BNSS • BSA)</p>
                </div>
            </div>
            <div class="flex items-center space-x-4 text-sm">
                <span class="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full font-mono text-xs">v0.1.0 (Live)</span>
                <a href="/docs" target="_blank" class="text-slate-400 hover:text-white transition">FastAPI Docs</a>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 py-8">
        <!-- Navigation Tabs -->
        <div class="flex border-b border-slate-800 space-x-8 mb-8">
            <button onclick="switchTab('translator')" id="tab-translator" class="py-3 px-1 border-b-2 border-amber-500 text-amber-400 font-medium text-sm flex items-center space-x-2">
                <span>🔄</span><span>Statutory Translator (BNS ↔ IPC)</span>
            </button>
            <button onclick="switchTab('auditor')" id="tab-auditor" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 font-medium text-sm flex items-center space-x-2">
                <span>🔍</span><span>FIR Procedural Auditor</span>
            </button>
            <button onclick="switchTab('drafter')" id="tab-drafter" class="py-3 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 font-medium text-sm flex items-center space-x-2">
                <span>📄</span><span>District Court Bail Drafter</span>
            </button>
        </div>

        <!-- TAB 1: TRANSLATOR -->
        <section id="panel-translator" class="space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Search Box -->
                <div class="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
                    <h2 class="text-lg font-semibold text-slate-200">Statutory Cross-Reference</h2>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Source Statute</label>
                        <select id="lookup-act" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500">
                            <option value="IPC">IPC (Indian Penal Code, 1860)</option>
                            <option value="BNS">BNS (Bharatiya Nyaya Sanhita, 2023)</option>
                            <option value="CRPC">CrPC (Code of Criminal Procedure, 1973)</option>
                            <option value="BNSS">BNSS (Bharatiya Nagarik Suraksha Sanhita, 2023)</option>
                            <option value="IEA">IEA (Indian Evidence Act, 1872)</option>
                            <option value="BSA">BSA (Bharatiya Sakshya Adhiniyam, 2023)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-slate-400 mb-1">Section Number</label>
                        <input id="lookup-section" type="text" placeholder="e.g. 420, 302, 120B, 41A, 437" value="420" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500" />
                    </div>
                    <button onclick="doLookup()" class="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-semibold py-2 px-4 rounded-lg text-sm transition">
                        Find Modern Mapping
                    </button>

                    <div class="pt-4 border-t border-slate-800">
                        <label class="block text-xs font-medium text-slate-400 mb-1">Or Parse Full Charges String</label>
                        <input id="translate-string" type="text" placeholder="e.g. IPC 420, 120B and CrPC 41A" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500 mb-2" />
                        <button onclick="doTranslateString()" class="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-2 px-4 rounded-lg text-sm transition">
                            Parse & Translate String
                        </button>
                    </div>
                </div>

                <!-- Result Display -->
                <div class="lg:col-span-2 bg-slate-950 p-6 rounded-xl border border-slate-800">
                    <h2 class="text-lg font-semibold text-slate-200 mb-4">Mapping Output</h2>
                    <div id="translator-output" class="text-sm text-slate-400">
                        Select an Act and enter a section to see the modern equivalent with full statutory details.
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB 2: AUDITOR -->
        <section id="panel-auditor" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
                    <h2 class="text-lg font-semibold text-slate-200">FIR & Remand Audit</h2>
                    <p class="text-xs text-slate-400">Paste FIR narrative or CCTNS text to detect violations of BNSS Section 35 (Old 41A), Section 105 (Videography), Section 479 (Undertrials), and Arnesh Kumar guidelines.</p>
                    <textarea id="audit-text" rows="10" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-amber-500 font-mono text-xs">FIRST INFORMATION REPORT
FIR No. 104/2026
Police Station: Hazratganj, Lucknow
Date of Report: 2026-03-05
Complainant: Vikas Sharma
Accused: Ramesh Kumar
Offences: Booked under IPC Section 420, 120B and 468.
Details: The accused Ramesh Kumar was arrested without notice and remanded. No videography of seizure was conducted. Accused has spent 20 days in custody without independent witness.</textarea>
                    <button onclick="doAudit()" class="w-full bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-semibold py-2 px-4 rounded-lg text-sm transition">
                        Audit for Procedural Violations
                    </button>
                </div>

                <div class="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
                    <h2 class="text-lg font-semibold text-slate-200">Procedural Audit Report</h2>
                    <div id="audit-output" class="text-sm text-slate-400">
                        Click 'Audit for Procedural Violations' to scan the FIR.
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB 3: DRAFTER -->
        <section id="panel-drafter" class="hidden space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="bg-slate-950 p-6 rounded-xl border border-slate-800 space-y-4">
                    <h2 class="text-lg font-semibold text-slate-200">Bail Petition Parameters</h2>
                    <div>
                        <label class="block text-xs text-slate-400 mb-1">Accused Name</label>
                        <input id="draft-accused" type="text" value="Ramesh Kumar" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">FIR Number</label>
                            <input id="draft-fir" type="text" value="104/2026" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                        </div>
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">Custody Days</label>
                            <input id="draft-days" type="number" value="25" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 mb-1">Police Station</label>
                        <input id="draft-ps" type="text" value="Hazratganj" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">District</label>
                            <input id="draft-dist" type="text" value="Lucknow" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                        </div>
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">State</label>
                            <input id="draft-state" type="text" value="Uttar Pradesh" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 mb-1">Sections Charged</label>
                        <input id="draft-sections" type="text" value="IPC 420, 120B, 468" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200" />
                    </div>
                    <button onclick="doDraftBail()" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-slate-950 font-semibold py-2 px-4 rounded-lg text-sm transition">
                        Generate BNSS Section 480 Petition
                    </button>
                </div>

                <div class="lg:col-span-2 bg-slate-950 p-6 rounded-xl border border-slate-800 flex flex-col">
                    <div class="flex items-center justify-between mb-4">
                        <h2 class="text-lg font-semibold text-slate-200">Court-Ready Bail Application</h2>
                        <button onclick="copyDraft()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded border border-slate-700 transition">
                            📋 Copy Pleading Text
                        </button>
                    </div>
                    <textarea id="draft-output" readonly rows="18" class="w-full bg-slate-900 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 focus:outline-none flex-grow leading-relaxed">
Click 'Generate BNSS Section 480 Petition' to produce the district court pleading.
                    </textarea>
                </div>
            </div>
        </section>
    </main>

    <script>
        function switchTab(tab) {
            ['translator', 'auditor', 'drafter'].forEach(t => {
                document.getElementById('panel-' + t).classList.add('hidden');
                document.getElementById('tab-' + t).classList.remove('border-amber-500', 'text-amber-400');
                document.getElementById('tab-' + t).classList.add('border-transparent', 'text-slate-400');
            });
            document.getElementById('panel-' + tab).classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.add('border-amber-500', 'text-amber-400');
            document.getElementById('tab-' + tab).classList.remove('border-transparent', 'text-slate-400');
        }

        async function doLookup() {
            const act = document.getElementById('lookup-act').value;
            const sec = document.getElementById('lookup-section').value;
            const out = document.getElementById('translator-output');
            out.innerHTML = '<div class="text-amber-400">Querying statutory database...</div>';

            try {
                const res = await fetch('/api/lookup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ act, section: sec })
                });
                if (!res.ok) throw new Error('Section not found');
                const data = await res.json();

                out.innerHTML = `
                    <div class="space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                            <span class="text-xs font-mono uppercase tracking-wider text-amber-500 font-semibold">${data.status}</span>
                            <span class="text-xs text-slate-400">${data.source ? data.source.act : ''}</span>
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-800">
                                <span class="text-xs text-slate-400">Source Section</span>
                                <div class="text-lg font-bold text-slate-100">${data.source ? data.source.section : ''}</div>
                                <div class="text-xs text-slate-300 mt-1">${data.source ? data.source.title : ''}</div>
                            </div>
                            <div class="bg-slate-900 p-4 rounded-lg border border-amber-500/30 bg-amber-500/5">
                                <span class="text-xs text-amber-400">Modern Equivalent (2023 Sanhita)</span>
                                <div class="text-lg font-bold text-amber-400">${data.target ? data.target.act + ' Sec ' + data.target.section : 'Repealed'}</div>
                                <div class="text-xs text-slate-300 mt-1">${data.target ? data.target.title : ''}</div>
                            </div>
                        </div>
                        <div class="p-4 bg-slate-900/60 rounded-lg text-slate-300 text-xs leading-relaxed border border-slate-800">
                            <strong>Statutory Statement:</strong> ${data.mapping_statement}
                        </div>
                        ${data.full_text ? `
                            <div class="mt-4">
                                <span class="text-xs font-semibold text-slate-400">Full Statutory Text (Excerpt):</span>
                                <pre class="mt-1 p-3 bg-slate-900 rounded border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap font-sans max-h-60 overflow-y-auto">${data.full_text}</pre>
                            </div>
                        ` : ''}
                    </div>
                `;
            } catch (err) {
                out.innerHTML = `<div class="text-red-400">Error: ${err.message}</div>`;
            }
        }

        async function doTranslateString() {
            const charges = document.getElementById('translate-string').value;
            const out = document.getElementById('translator-output');
            out.innerHTML = '<div class="text-amber-400">Parsing legal string...</div>';

            try {
                const res = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ charges })
                });
                const data = await res.json();
                if (data.length === 0) {
                    out.innerHTML = '<div class="text-yellow-400">No sections recognized. Try e.g. "IPC 420, 120B and CrPC 41A"</div>';
                    return;
                }

                let html = '<div class="space-y-3"><h3 class="text-sm font-semibold text-slate-200">Parsed Sections (' + data.length + '):</h3>';
                data.forEach(d => {
                    html += `
                        <div class="p-3 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-between">
                            <div>
                                <span class="font-bold text-amber-400">${d.source ? d.source.act + ' ' + d.source.section : d.lookup_key}</span>
                                <span class="text-slate-400 text-xs mx-2">corresponds to</span>
                                <span class="font-bold text-emerald-400">${d.target ? d.target.act + ' Sec ' + d.target.section : 'Repealed'}</span>
                            </div>
                            <span class="text-xs text-slate-400">${d.target ? d.target.title : ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
                out.innerHTML = html;
            } catch (err) {
                out.innerHTML = `<div class="text-red-400">Error: ${err.message}</div>`;
            }
        }

        async function doAudit() {
            const text = document.getElementById('audit-text').value;
            const out = document.getElementById('audit-output');
            out.innerHTML = '<div class="text-amber-400">Running procedural compliance audit...</div>';

            try {
                const res = await fetch('/api/audit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ fir_text: text })
                });
                const data = await res.json();

                let html = `
                    <div class="space-y-4">
                        <div class="p-4 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-between">
                            <div>
                                <div class="text-xs text-slate-400">Bail Favourability Score</div>
                                <div class="text-2xl font-bold text-emerald-400">${data.bail_favourability_score} / 100</div>
                            </div>
                            <div class="text-right">
                                <div class="text-xs text-slate-400">Procedural Flags</div>
                                <div class="text-xl font-bold text-amber-400">${data.flags.length} Defects Found</div>
                            </div>
                        </div>
                        <div class="space-y-3">
                `;

                data.flags.forEach(f => {
                    const borderCol = f.severity === 'CRITICAL' ? 'border-red-500/40 bg-red-500/5' : 'border-amber-500/40 bg-amber-500/5';
                    const textCol = f.severity === 'CRITICAL' ? 'text-red-400' : 'text-amber-400';
                    html += `
                        <div class="p-3 rounded-lg border ${borderCol}">
                            <div class="flex items-center justify-between mb-1">
                                <span class="text-xs font-bold ${textCol}">[${f.severity}] ${f.title}</span>
                                <span class="text-[10px] text-slate-400">${f.rule_id}</span>
                            </div>
                            <p class="text-xs text-slate-300 mb-2">${f.violation_detail}</p>
                            <div class="text-[11px] text-slate-400"><strong>Precedent:</strong> ${f.judicial_precedent}</div>
                            <div class="mt-2 text-xs bg-slate-950 p-2 rounded text-amber-300 font-mono">Defense Arg: ${f.suggested_defense_argument}</div>
                        </div>
                    `;
                });

                if (data.cross_examination_questions.length > 0) {
                    html += '<div class="mt-4"><h4 class="text-xs font-semibold text-slate-300 mb-2">Cross-Examination Questions for Police IO:</h4><ul class="space-y-1">';
                    data.cross_examination_questions.forEach(q => {
                        html += `<li class="text-xs text-slate-400 pl-3 border-l-2 border-amber-500">• ${q}</li>`;
                    });
                    html += '</ul></div>';
                }

                html += '</div></div>';
                out.innerHTML = html;
            } catch (err) {
                out.innerHTML = `<div class="text-red-400">Error: ${err.message}</div>`;
            }
        }

        async function doDraftBail() {
            const accused_name = document.getElementById('draft-accused').value;
            const fir_number = document.getElementById('draft-fir').value;
            const custody_days = parseInt(document.getElementById('draft-days').value) || 20;
            const police_station = document.getElementById('draft-ps').value;
            const district = document.getElementById('draft-dist').value;
            const state = document.getElementById('draft-state').value;
            const sections_charged = document.getElementById('draft-sections').value;

            const out = document.getElementById('draft-output');
            out.value = 'Drafting court pleading with dual statutory citations...';

            try {
                const res = await fetch('/api/draft-bail', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        accused_name, fir_number, police_station, district, state,
                        sections_charged, custody_days,
                        section_35_notice_violated: true, videography_missing: true
                    })
                });
                const data = await res.json();
                out.value = data.formatted_document;
            } catch (err) {
                out.value = 'Error generating bail petition: ' + err.message;
            }
        }

        function copyDraft() {
            const text = document.getElementById('draft-output').value;
            navigator.clipboard.writeText(text);
            alert('Pleading copied to clipboard!');
        }

        // Initialize default lookup
        doLookup();
    </script>
</body>
</html>
    """
