import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from nyaya.models import MappingResult, MappingSource, MappingTarget

DATA_DIR = Path(__file__).parent / "data"

# Known procedural metadata for common criminal offenses
OFFENSE_DATABASE: Dict[str, Dict[str, Any]] = {
    # Keyed by standard normalized identifier (e.g., "IPC:420", "BNS:318", "BNS:318(4)")
    "IPC:420": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Cheating and dishonestly inducing delivery of property"},
    "BNS:318": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Cheating"},
    "BNS:318(4)": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Cheating and dishonestly inducing delivery of property"},
    "IPC:302": {"punishment_years": 99.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Murder"},
    "BNS:103": {"punishment_years": 99.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Punishment for murder"},
    "IPC:307": {"punishment_years": 10.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Attempt to murder"},
    "BNS:109": {"punishment_years": 10.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Attempt to murder"},
    "IPC:379": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Theft"},
    "BNS:303": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Theft"},
    "BNS:303(2)": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Theft punishment"},
    "IPC:120B": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Criminal conspiracy"},
    "BNS:61": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Criminal conspiracy"},
    "BNS:61(2)": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Criminal conspiracy"},
    "IPC:323": {"punishment_years": 1.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Voluntarily causing hurt"},
    "BNS:115": {"punishment_years": 1.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Voluntarily causing hurt"},
    "BNS:115(2)": {"punishment_years": 1.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Voluntarily causing hurt"},
    "IPC:324": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Causing hurt by dangerous weapons"},
    "BNS:118": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Causing hurt by dangerous weapons"},
    "IPC:325": {"punishment_years": 7.0, "bailable": True, "cognizable": True, "compoundable": True, "offense": "Voluntarily causing grievous hurt"},
    "BNS:117": {"punishment_years": 7.0, "bailable": True, "cognizable": True, "compoundable": True, "offense": "Voluntarily causing grievous hurt"},
    "BNS:117(2)": {"punishment_years": 7.0, "bailable": True, "cognizable": True, "compoundable": True, "offense": "Voluntarily causing grievous hurt"},
    "IPC:354": {"punishment_years": 5.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Assault to woman with intent to outrage modesty"},
    "BNS:74": {"punishment_years": 5.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Assault or criminal force to woman with intent to outrage modesty"},
    "IPC:406": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Criminal breach of trust"},
    "BNS:316": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Criminal breach of trust"},
    "BNS:316(2)": {"punishment_years": 3.0, "bailable": False, "cognizable": True, "compoundable": True, "offense": "Criminal breach of trust"},
    "IPC:467": {"punishment_years": 10.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Forgery of valuable security"},
    "BNS:338": {"punishment_years": 10.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Forgery of valuable security"},
    "IPC:468": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Forgery for purpose of cheating"},
    "BNS:336": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Forgery for purpose of cheating"},
    "BNS:336(3)": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Forgery for purpose of cheating"},
    "IPC:471": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Using as genuine a forged document"},
    "BNS:340": {"punishment_years": 7.0, "bailable": False, "cognizable": True, "compoundable": False, "offense": "Using as genuine a forged document"},
    "IPC:504": {"punishment_years": 2.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Intentional insult with intent to provoke breach of peace"},
    "BNS:352": {"punishment_years": 2.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Intentional insult with intent to provoke breach of peace"},
    "IPC:506": {"punishment_years": 2.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Criminal intimidation"},
    "BNS:351": {"punishment_years": 2.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Criminal intimidation"},
    "BNS:351(2)": {"punishment_years": 2.0, "bailable": True, "cognizable": False, "compoundable": True, "offense": "Criminal intimidation"},
}

class LawMapper:
    """
    Bidirectional statutory cross-reference engine for Indian Law.
    Maps between IPC ↔ BNS, CrPC ↔ BNSS, and IEA ↔ BSA.
    """
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self._raw_datasets: Dict[str, List[Dict[str, Any]]] = {}
        self._indexes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self._statute_texts: Dict[str, Dict[str, str]] = {}
        self._load_all()

    def _load_all(self):
        datasets = [
            ("ipc_to_bns", "ipc_to_bns.json"),
            ("bns_to_ipc", "bns_to_ipc.json"),
            ("crpc_to_bnss", "crpc_to_bnss.json"),
            ("bnss_to_crpc", "bnss_to_crpc.json"),
            ("iea_to_bsa", "iea_to_bsa.json"),
            ("bsa_to_iea", "bsa_to_iea.json"),
        ]
        for name, filename in datasets:
            path = self.data_dir / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    self._raw_datasets[name] = items
                    self._indexes[name] = self._build_index(items)

        # Load statute texts
        statute_files = [
            ("BNS", "bns_sections.json"),
            ("BNSS", "bnss_sections.json"),
            ("BSA", "bsa_sections.json"),
        ]
        for act_key, filename in statute_files:
            path = self.data_dir / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    sections_list = json.load(f)
                    act_dict = {}
                    for s in sections_list:
                        num = str(s.get("section_number", "")).strip().lower()
                        act_dict[num] = s.get("text", "")
                    self._statute_texts[act_key] = act_dict

    def _normalize_key(self, key: str) -> str:
        """
        Normalizes a section string:
        e.g., 'Sec. 420', 'Section 420', 'u/s 420', ' 120-B ' -> '120B'
        """
        k = str(key).strip().upper()
        # Remove common prefixes
        k = re.sub(r'^(SECTION|SEC|U/S|US)\.?\s*', '', k, flags=re.IGNORECASE)
        # Remove hyphens or spaces in sub-clauses like 120-B -> 120B
        k = re.sub(r'[\s\-]+', '', k)
        return k.lower()

    def _build_index(self, items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}
        for item in items:
            # Index by lookup_key
            lk = str(item.get("lookup_key", "")).strip().lower()
            if lk:
                norm_lk = self._normalize_key(lk)
                index[norm_lk] = item
                index[lk] = item

            # Index by source section
            src = item.get("source", {})
            src_sec = str(src.get("section", "")).strip().lower()
            if src_sec:
                norm_src = self._normalize_key(src_sec)
                if norm_src not in index:
                    index[norm_src] = item

            # Index by source subsection if present (e.g. 35(3))
            sub = src.get("sub_section")
            if sub:
                norm_sub = self._normalize_key(str(sub))
                if norm_sub not in index:
                    index[norm_sub] = item

        return index

    def _normalize_act_name(self, act: str) -> str:
        a = act.upper().strip()
        if "PENAL" in a or a == "IPC":
            return "IPC"
        if "NYAYA" in a or a == "BNS":
            return "BNS"
        if "CRIMINAL PROCEDURE" in a or a == "CRPC" or a == "CR.P.C":
            return "CRPC"
        if "NAGARIK" in a or a == "BNSS":
            return "BNSS"
        if "EVIDENCE" in a or a == "IEA":
            return "IEA"
        if "SAKSHYA" in a or a == "BSA":
            return "BSA"
        return a

    def lookup(self, act: str, section: str) -> Optional[MappingResult]:
        """
        Looks up a single section under a specific Act.
        Returns a rich MappingResult object with full source, target, status, and text.
        """
        act_norm = self._normalize_act_name(act)
        sec_norm = self._normalize_key(section)

        table_map = {
            "IPC": "ipc_to_bns",
            "BNS": "bns_to_ipc",
            "CRPC": "crpc_to_bnss",
            "BNSS": "bnss_to_crpc",
            "IEA": "iea_to_bsa",
            "BSA": "bsa_to_iea",
        }

        table_name = table_map.get(act_norm)
        if not table_name or table_name not in self._indexes:
            return None

        index = self._indexes[table_name]
        raw = index.get(sec_norm)

        # Try base section if sub-section was passed, e.g., '318(4)' -> '318'
        if not raw and "(" in sec_norm:
            base_sec = sec_norm.split("(")[0]
            raw = index.get(base_sec)

        if not raw:
            return None

        # Fetch full text if available
        target_info = raw.get("target") or {}
        target_act_norm = self._normalize_act_name(target_info.get("act", ""))
        target_sec = str(target_info.get("section", "")).strip().lower()
        full_text = self._statute_texts.get(target_act_norm, {}).get(target_sec)

        src_info = raw.get("source")
        target_obj = MappingTarget(**target_info) if target_info else None
        source_obj = MappingSource(**src_info) if src_info else None

        return MappingResult(
            id=raw.get("id", ""),
            lookup_key=str(raw.get("lookup_key", "")),
            status=raw.get("status", "Retained"),
            mapping_statement=raw.get("mapping_statement", ""),
            source=source_obj,
            target=target_obj,
            full_text=full_text,
        )

    def translate_string(self, charges_string: str) -> List[MappingResult]:
        """
        Takes legal text or charges string like:
        "IPC 420, 120B, 467, CrPC 41A" or "Sections 302, 120B IPC and 35 BNSS"
        Parses all sections and resolves their modern/colonial mappings.
        """
        results: List[MappingResult] = []
        seen = set()

        act_keywords = {"IPC", "BNS", "CRPC", "BNSS", "IEA", "BSA"}

        # First, search for explicit patterns like: "IPC 420", "Section 420 IPC", "u/s 420, 120B IPC", "BNS Sec 318"
        # Split text into lines or sentences
        lines = re.split(r'[\n\;]', charges_string)

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if this line references offences or acts
            has_act = any(re.search(r'\b' + re.escape(ak) + r'\b', line_str, re.IGNORECASE) for ak in act_keywords)
            has_sec_word = bool(re.search(r'\b(?:SECTION|SEC|U\/S|OFFENCE|OFFENSE)\b', line_str, re.IGNORECASE))

            if not (has_act or has_sec_word):
                continue

            # Determine prevailing Act in this line
            detected_acts = []
            for ak in ["IPC", "BNS", "CRPC", "BNSS", "IEA", "BSA"]:
                if re.search(r'\b' + re.escape(ak) + r'\b', line_str, re.IGNORECASE):
                    detected_acts.append(ak)

            primary_act = detected_acts[0] if detected_acts else "IPC"

            # Extract section numbers that follow 'sec', 'u/s', or act name, or are in a comma-separated list
            # Match 120B, 318(4), 420, 41A, 303(2), etc.
            # Avoid matching 4-digit years like 2023, 2024, 2026
            sec_candidates = re.findall(r'\b([0-9]{1,3}[A-Za-z]?(?:\([0-9a-zA-Z]+\))?)\b', line_str)

            for cand in sec_candidates:
                # Discard common non-section numbers (e.g. single digit dates or day numbers if ambiguous)
                res = self.lookup(primary_act, cand)
                if res and res.id not in seen:
                    results.append(res)
                    seen.add(res.id)

        return results

    def get_offense_metadata(self, act: str, section: str) -> Dict[str, Any]:
        """
        Returns penalty, bailability, and cognizable status for common criminal sections.
        """
        act_norm = self._normalize_act_name(act)
        sec_norm = self._normalize_key(section)
        key = f"{act_norm}:{sec_norm.upper()}"

        if key in OFFENSE_DATABASE:
            return OFFENSE_DATABASE[key]

        # Check without subsection
        if "(" in sec_norm:
            base_key = f"{act_norm}:{sec_norm.split('(')[0].upper()}"
            if base_key in OFFENSE_DATABASE:
                return OFFENSE_DATABASE[base_key]

        # Default fallback
        return {
            "punishment_years": 3.0,
            "bailable": True,
            "cognizable": True,
            "compoundable": False,
            "offense": f"Offence under Section {section} {act_norm}"
        }

    def search(self, query: str, act: Optional[str] = None, limit: int = 15) -> List[MappingResult]:
        """
        Full text keyword search across all statutes, section titles, and mapping statements.
        """
        query_lower = query.lower().strip()
        results: List[MappingResult] = []
        seen_ids = set()

        table_order = ["ipc_to_bns", "crpc_to_bnss", "iea_to_bsa", "bns_to_ipc", "bnss_to_crpc", "bsa_to_iea"]
        if act:
            act_norm = self._normalize_act_name(act)
            if act_norm in ["IPC", "BNS"]:
                table_order = ["ipc_to_bns", "bns_to_ipc"]
            elif act_norm in ["CRPC", "BNSS"]:
                table_order = ["crpc_to_bnss", "bnss_to_crpc"]
            elif act_norm in ["IEA", "BSA"]:
                table_order = ["iea_to_bsa", "bsa_to_iea"]

        for tbl in table_order:
            items = self._raw_datasets.get(tbl, [])
            for item in items:
                src = item.get("source") or {}
                tgt = item.get("target") or {}
                stmt = (item.get("mapping_statement") or "").lower()
                src_title = str(src.get("title") or "").lower()
                tgt_title = str(tgt.get("title") or "").lower()
                sec_no = str(src.get("section") or "").lower()

                if query_lower in src_title or query_lower in tgt_title or query_lower in stmt or query_lower == sec_no:
                    item_id = item.get("id", "")
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        target_obj = MappingTarget(**tgt) if tgt else None
                        source_obj = MappingSource(**src) if src else None
                        results.append(MappingResult(
                            id=item_id,
                            lookup_key=str(item.get("lookup_key", "")),
                            status=item.get("status", "Retained"),
                            mapping_statement=item.get("mapping_statement", ""),
                            source=source_obj,
                            target=target_obj
                        ))
                        if len(results) >= limit:
                            return results

        return results
