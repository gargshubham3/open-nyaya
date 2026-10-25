import re
from typing import Optional, List, Dict, Any
from datetime import datetime
from nyaya.models import FIRDetails, AccusedPerson, SectionCharge
from nyaya.mapper import LawMapper

class FIRParser:
    """
    Rule-based and heuristic parser for Indian First Information Reports (FIRs)
    and charge-sheet summaries (both CCTNS digital format and narrative plain text).
    """

    def __init__(self, mapper: Optional[LawMapper] = None):
        self.mapper = mapper or LawMapper()

    def parse_text(self, text: str) -> FIRDetails:
        # Extract FIR Number and Year
        fir_no_match = re.search(r'(?:FIR\s*(?:NO|NUMBER|NO\.)[\s\:\.\/]*)([0-9]+(?:\/[0-9]+)?)', text, re.IGNORECASE)
        fir_number = fir_no_match.group(1) if fir_no_match else "001/2026"

        year_match = re.search(r'\b(202[3-9]|201[0-9])\b', text)
        year = int(year_match.group(1)) if year_match else 2026

        # Extract Police Station
        ps_match = re.search(r'(?:POLICE\s*STATION|P\.?S\.?)[\s\:\.\-]*([A-Za-z0-9\s\,\.]+?)(?=\n|District|Dist|Date|\;|\,|$)', text, re.IGNORECASE)
        police_station = ps_match.group(1).strip() if ps_match else "Local Police Station"

        # Extract District
        dist_match = re.search(r'(?:DISTRICT|DIST\.?)[\s\:\.\-]*([A-Za-z0-9\s]+?)(?=\n|State|P\.?S|Date|\;|\,|$)', text, re.IGNORECASE)
        district = dist_match.group(1).strip() if dist_match else "District"

        # Extract Complainant
        comp_match = re.search(r'(?:COMPLAINANT|INFORMANT|COMPLAINANT\s*NAME)[\s\:\.\-]*([A-Za-z\s\.\']+?)(?=\n|S\/o|W\/o|D\/o|Age|Address|\;|$)', text, re.IGNORECASE)
        complainant = comp_match.group(1).strip() if comp_match else None

        # Extract Accused Names
        accused_list: List[AccusedPerson] = []
        acc_match = re.search(r'(?:ACCUSED|NAME\s*OF\s*ACCUSED)[\s\:\.\-]*([A-Za-z\s\.\']+?)(?=\n|S\/o|W\/o|D\/o|Age|Address|\;|$)', text, re.IGNORECASE)
        if acc_match:
            raw_acc_name = acc_match.group(1).strip()
            # Split if multiple accused
            names = re.split(r'\,|\band\b', raw_acc_name)
            for n in names:
                clean_n = n.strip()
                if clean_n and len(clean_n) > 2 and clean_n.lower() not in ["unknown", "nil", "na"]:
                    accused_list.append(AccusedPerson(
                        name=clean_n,
                        is_arrested=True,
                        custody_days=None,
                        is_first_offender=True
                    ))

        if not accused_list:
            # Fallback search for accused pattern: "accused Ramesh Kumar" or "arrest of Ramesh Kumar"
            acc_fallback = re.search(r'(?:accused|arrest of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', text)
            if acc_fallback:
                accused_list.append(AccusedPerson(
                    name=acc_fallback.group(1).strip(),
                    is_arrested=True
                ))
            else:
                accused_list.append(AccusedPerson(name="Accused Person", is_arrested=True))

        # Extract Sections Charged
        sections_charged: List[SectionCharge] = []
        
        # Look for specific lines containing offences/sections
        sec_lines = []
        for line in text.split("\n"):
            line_str = line.strip()
            if re.search(r'\b(?:OFFENCE|OFFENSE|SECTION|SEC|ACT|IPC|BNS|CRPC|BNSS|UNDER)\b', line_str, re.IGNORECASE):
                # Exclude lines that are headers, dates, or factual narrative details
                if not re.search(r'^(?:DATE|TIME|FIR\s*NO|DISTRICT|POLICE\s*STATION|DETAILS|FACTS|BRIEF|RECOVERY|SEIZURE)', line_str, re.IGNORECASE):
                    sec_lines.append(line_str)

        sec_text = "\n".join(sec_lines) if sec_lines else text
        translated_results = self.mapper.translate_string(sec_text)
        
        for tr in translated_results:
            src_act = tr.source.act if tr.source else "IPC"
            src_sec = tr.source.section if tr.source else tr.lookup_key
            meta = self.mapper.get_offense_metadata(src_act, src_sec)
            sections_charged.append(SectionCharge(
                act=src_act,
                section=src_sec,
                description=meta.get("offense"),
                bailable=meta.get("bailable"),
                compoundable=meta.get("compoundable"),
                max_punishment_years=meta.get("punishment_years"),
                cognizable=meta.get("cognizable")
            ))

        # Check for Procedural indicators in text
        text_lower = text.lower()
        sec_35_notice = None
        if (
            "without notice" in text_lower
            or "no notice" in text_lower
            or "without issuing notice" in text_lower
            or "arrested without notice" in text_lower
        ):
            sec_35_notice = False
        elif (
            "notice under section 35" in text_lower
            or "notice u/s 35" in text_lower
            or "41a notice" in text_lower
            or "notice u/s 41a" in text_lower
            or "served notice" in text_lower
        ):
            sec_35_notice = True

        videography = None
        if (
            "no videography" in text_lower
            or "not recorded" in text_lower
            or "without videography" in text_lower
            or "no video recording" in text_lower
        ):
            videography = False
        elif (
            "videography" in text_lower
            or "video recording" in text_lower
            or "audio-video" in text_lower
        ):
            videography = True

        ind_witness = None
        if (
            "no independent witness" in text_lower
            or "refused to join" in text_lower
            or "without independent witness" in text_lower
            or "without any independent witness" in text_lower
        ):
            ind_witness = False
        elif "independent witness" in text_lower or "public witness" in text_lower:
            ind_witness = True

        recovery = None
        if "recovery" in text_lower or "seized" in text_lower or "seizure" in text_lower:
            recovery = True

        # Extract custody days if mentioned
        custody_days_match = re.search(r'([0-9]+)\s*(?:days\s*(?:in\s*)?(?:custody|jail|detention|remand))', text, re.IGNORECASE)
        if custody_days_match and accused_list:
            accused_list[0].custody_days = int(custody_days_match.group(1))

        return FIRDetails(
            fir_number=fir_number,
            year=year,
            police_station=police_station,
            district=district,
            complainant_name=complainant,
            accused_list=accused_list,
            sections_charged=sections_charged,
            section_35_notice_issued=sec_35_notice,
            videography_recorded=videography,
            independent_witness_present=ind_witness,
            recovery_made=recovery
        )
