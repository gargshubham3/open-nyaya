# ⚖️ open-nyaya

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 27/27 Passed](https://img.shields.io/badge/tests-27%2F27%20passed-brightgreen.svg)]()
[![Law: BNS • BNSS • BSA 2023](https://img.shields.io/badge/statutes-BNS%20%E2%80%A2%20BNSS%20%E2%80%A2%20BSA-orange.svg)]()

> **Open-Source Legal AI & Statutory Computing Toolkit for Modern Indian Criminal Law.**
> Seamlessly bridges colonial criminal law (*IPC, CrPC, Indian Evidence Act*) with modern Indian law (*Bharatiya Nyaya Sanhita, Bharatiya Nagarik Suraksha Sanhita, Bharatiya Sakshya Adhiniyam*), audits police procedural violations, and drafts district court pleadings.

---

## 🌟 Why open-nyaya?

Over **50 million cases** clog Indian courts, with undertrials comprising over **75% of the prison population**. The transition from colonial procedural codes to BNS/BNSS/BSA in 2024 has introduced disorientation for 2+ million advocates and judges.

`open-nyaya` provides a free, open-source foundation:
1. **Statutory Cross-Referencing:** 2,600+ bidirectional section mappings and full text for all 358 BNS, 531 BNSS, and 170 BSA sections.
2. **FIR & Procedural Compliance Auditor:** Detects police violations of **BNSS Section 35** (mandatory notice for offenses $\le 7$ years under *Arnesh Kumar* / *Satender Kumar Antil*), **BNSS Section 105** (mandatory videography of search/seizure), and **BNSS Section 479** (statutory undertrial bail).
3. **Automated Bail Pleading Drafter:** Generates court-ready Regular Bail Applications under **Section 480 BNSS** with dual citations (e.g. `Section 318 BNS [formerly Section 420 IPC]`), verified undertakings, and Supreme Court precedents.
4. **Zero-Setup Web Dashboard & CLI:** A command-line tool with rich terminal formatting, and a local web interface.

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/your-username/open-nyaya.git
cd open-nyaya
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Python API

```python
from nyaya import LawMapper, CaseAuditor, FIRParser, BailDrafter

# 1. Statutory Translation (IPC <-> BNS)
mapper = LawMapper()
result = mapper.lookup("IPC", "420")
print(result.target.act, "Section", result.target.section)
# -> Bharatiya Nyaya Sanhita, 2023 Section 318 (Cheating)

# 2. Parse & Audit an FIR for Procedural Violations
parser = FIRParser()
fir = parser.parse_text("""
FIRST INFORMATION REPORT
FIR No. 104/2026, PS: Hazratganj, Lucknow
Accused Ramesh Kumar booked under IPC 420 and 120B.
Arrested without notice. No videography of search conducted. Accused has been 25 days in custody.
""")

auditor = CaseAuditor()
report = auditor.audit(fir)
print(f"Bail Score: {report.bail_favourability_score}/100")
for flag in report.flags:
    print(f"[{flag.severity}] {flag.title}")
    print(f" -> Precedent: {flag.judicial_precedent}")

# 3. Generate Court-Ready Bail Application
drafter = BailDrafter()
draft = drafter.draft_bail(fir, report)
print(draft.formatted_document)
```

---

## 💻 Command Line Interface (CLI)

`open-nyaya` ships with a CLI tool:

```bash
# Lookup any section
open-nyaya lookup IPC 420
open-nyaya lookup CrPC 41A
open-nyaya lookup BNS 103

# Translate complex charges string
open-nyaya translate "IPC 420, 120B and CrPC 41A"

# Search across statutes
open-nyaya search "murder" --limit 5

# Audit an FIR file
open-nyaya audit sample_fir.txt

# Draft a District Court Bail Application
open-nyaya draft-bail \
  --accused "Pawan Sharma" \
  --fir "104/2026" \
  --ps "Hazratganj" \
  --district "Lucknow" \
  --sections "IPC 420, 120B, 468" \
  --custody-days 30 \
  --output bail_petition.txt
```

---

## 🌐 Interactive Web Dashboard

Launch the embedded web dashboard:

```bash
open-nyaya serve --port 8000
```
Open `http://localhost:8000` in your browser. The application includes:
- **Statutory Translator:** Live section mapping with full statute text previews.
- **Procedural Auditor:** Paste any FIR or charge-sheet to get instant procedural red flags, defense arguments, and cross-examination questions for the Investigating Officer (IO).
- **Bail Pleading Drafter:** 1-click generation of formatted district court pleadings.

---

## 📐 Project Architecture

```
open-nyaya/
├── nyaya/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Pydantic schemas (FIRDetails, AuditReport, etc.)
│   ├── mapper.py            # Bidirectional statutory mapping & text retrieval
│   ├── auditor.py           # Procedural compliance engine (BNSS 35, 105, 479)
│   ├── parser.py            # Indian FIR / police text extractor
│   ├── drafter.py           # Court-ready pleading generator (Section 480 BNSS)
│   ├── cli.py               # Click & Rich terminal interface
│   ├── web.py               # FastAPI server & responsive Web UI
│   └── data/                # Complete statutory JSON datasets
│       ├── ipc_to_bns.json  (569 mappings)
│       ├── bns_to_ipc.json  (544 mappings)
│       ├── crpc_to_bnss.json(557 mappings)
│       ├── bnss_to_crpc.json(583 mappings)
│       ├── iea_to_bsa.json  (190 mappings)
│       ├── bsa_to_iea.json  (186 mappings)
│       ├── bns_sections.json (358 full text sections)
│       ├── bnss_sections.json(531 full text sections)
│       └── bsa_sections.json (170 full text sections)
├── tests/                   # 27 automated unit & integration tests
├── pyproject.toml           # Pip packaging & CLI entrypoints
└── README.md
```

---

## 🧪 Running Automated Tests

Run the full test suite with `pytest`:

```bash
pytest -v
```

All 27 test cases test:
- Bidirectional statutory resolution (IPC $\leftrightarrow$ BNS, CrPC $\leftrightarrow$ BNSS, IEA $\leftrightarrow$ BSA).
- Procedural defect rules under *Satender Kumar Antil* and *Arnesh Kumar*.
- FIR text parsing and linguistic edge-case handling.
- District court pleading format and mandatory clauses.
- REST API and CLI commands.

---

## 📜 License & Open Public Goods

Licensed under the **Apache License, Version 2.0**. Free for developers, legal aid clinics, researchers, and citizens building towards a faster, transparent justice ecosystem for India.
