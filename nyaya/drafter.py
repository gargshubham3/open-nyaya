from typing import Optional, List, Dict, Any
from nyaya.models import FIRDetails, AuditReport, BailApplicationDraft
from nyaya.mapper import LawMapper

class BailDrafter:
    """
    District Court Pleading Generator for Indian Advocates.
    Produces formatted, court-ready Regular Bail Applications under Section 480 / 483 BNSS, 2023
    incorporating dual statutory references (BNS + old IPC) and binding Supreme Court precedents.
    """

    def __init__(self, mapper: Optional[LawMapper] = None):
        self.mapper = mapper or LawMapper()

    def draft_bail(self, fir: FIRDetails, audit_report: Optional[AuditReport] = None, custom_grounds: Optional[List[str]] = None) -> BailApplicationDraft:
        accused = fir.accused_list[0] if fir.accused_list else None
        accused_name = accused.name if accused else "The Applicant"
        custody_text = f"in custody for {accused.custody_days} days" if (accused and accused.custody_days) else "presently in judicial custody"

        # Format dual sections: e.g. "Section 318(4) BNS [formerly Section 420 IPC]"
        formatted_sections_list = []
        for chg in fir.sections_charged:
            mapped = self.mapper.lookup(chg.act, chg.section)
            if mapped and mapped.target:
                formatted_sections_list.append(
                    f"Section {mapped.target.section} {mapped.target.act} (formerly Section {chg.section} {chg.act})"
                )
            else:
                formatted_sections_list.append(f"Section {chg.section} of {chg.act}")

        charges_str = ", ".join(formatted_sections_list) if formatted_sections_list else "Sections as charged in FIR"

        # Court Heading
        court_heading = f"IN THE COURT OF THE LEARNED SESSIONS JUDGE / CHIEF JUDICIAL MAGISTRATE AT {fir.district.upper()}, {fir.state.upper()}"
        case_title = f"IN THE MATTER OF:\n{accused_name.upper()}\n...APPLICANT / ACCUSED\n\nVERSUS\n\nSTATE OF {fir.state.upper()}\n...RESPONDENT"

        # Generate Grounds
        grounds: List[str] = [
            f"1. That the Applicant is an innocent and law-abiding citizen of India, having deep roots in society, and has been falsely implicated in the present case due to extraneous considerations and mala fide motives.",
            f"2. That the Applicant was arrested in connection with FIR No. {fir.fir_number} registered at Police Station {fir.police_station} and is {custody_text}, having clean antecedents with no prior conviction.",
            "3. That the cardinal principle of criminal jurisprudence is that 'Bail is the rule and Jail is an exception', as authoritatively laid down by the Hon'ble Supreme Court in State of Rajasthan v. Balchand (AIR 1977 SC 2447) and reiterated in Satender Kumar Antil v. CBI ((2022) 10 SCC 51).",
            "4. That the investigation qua the Applicant is virtually complete, all relevant documents/materials have been seized, and no fruitful purpose will be served by detaining the Applicant in custodial incarceration pending trial.",
        ]

        # Inject procedural defect grounds from Audit Report
        if audit_report and audit_report.flags:
            for i, flag in enumerate(audit_report.flags, start=5):
                grounds.append(
                    f"{i}. That {flag.suggested_defense_argument} (Violating {flag.statutory_reference}, relying on {flag.judicial_precedent})."
                )

        if custom_grounds:
            for cg in custom_grounds:
                grounds.append(f"• {cg}")

        # Precedent Citations
        precedents = [
            "Satender Kumar Antil v. Central Bureau of Investigation, (2022) 10 SCC 51",
            "Arnesh Kumar v. State of Bihar, (2014) 8 SCC 273",
            "Sanjay Chandra v. Central Bureau of Investigation, (2012) 1 SCC 40",
            "Dataram Singh v. State of Uttar Pradesh, (2018) 3 SCC 22",
            "Shafhi Mohammad v. State of Himachal Pradesh, (2018) 5 SCC 311"
        ]

        # Statutory Undertakings
        undertakings = [
            "That the Applicant undertakes to join and cooperate with the investigation as and when directed by the Investigating Agency or this Hon'ble Court.",
            "That the Applicant undertakes not to tamper with the evidence or influence any prosecution witness directly or indirectly.",
            "That the Applicant will not leave the territorial jurisdiction of this Hon'ble Court without prior permission.",
            "That the Applicant is ready and willing to furnish solvent local surety and bail bond to the complete satisfaction of this Hon'ble Court."
        ]

        prayer = (
            f"WHEREFORE, in light of the facts and circumstances stated hereinabove, it is most respectfully prayed "
            f"that this Hon'ble Court may be pleased to:\n\n"
            f"A. Release the Applicant/Accused, namely {accused_name}, on regular bail in connection with "
            f"FIR No. {fir.fir_number} registered at Police Station {fir.police_station} for offences under {charges_str};\n\n"
            f"B. Pass any such other or further order(s) as this Hon'ble Court may deem fit and proper in the "
            f"interest of justice and equity."
        )

        verification = (
            f"VERIFICATION:\n\n"
            f"I, the Pairokar / Advocate for the Applicant, do hereby verify and declare that the contents of "
            f"the above bail application are true and correct to the best of my knowledge and information derived "
            f"from the case records. No part of it is false and nothing material has been concealed therein.\n\n"
            f"Verified at {fir.district} on this day of {fir.year}."
        )

        # Build full formatted court document in Markdown / Plain text
        formatted_doc = f"""{court_heading}

BAIL APPLICATION NO. _______ OF {fir.year}
IN
FIR NO.: {fir.fir_number}
POLICE STATION: {fir.police_station}
UNDER SECTIONS: {charges_str}

{case_title}

APPLICATION FOR GRANT OF REGULAR BAIL UNDER SECTION 480 OF THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 (BNSS) [FORMERLY SECTION 437/439 CR.P.C.] ON BEHALF OF THE APPLICANT/ACCUSED.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant is filing the present application seeking regular bail in connection with the above-mentioned FIR registered at Police Station {fir.police_station}.

2. GROUNDS FOR BAIL:
{chr(10).join(grounds)}

3. LANDMARK PRECEDENTS RELIED UPON:
{chr(10).join(['- ' + p for p in precedents])}

4. UNDERTAKINGS:
{chr(10).join(['- ' + u for u in undertakings])}

PRAYER:
{prayer}

THROUGH COUNSEL

ADVOCATE FOR THE APPLICANT
DISTRICT COURT BAR ASSOCIATION, {fir.district.upper()}

{verification}
"""

        return BailApplicationDraft(
            court_heading=court_heading,
            case_title=case_title,
            accused_name=accused_name,
            fir_number=fir.fir_number,
            police_station=fir.police_station,
            statutory_provision="Section 480 of Bharatiya Nagarik Suraksha Sanhita, 2023",
            charges_formatted=charges_str,
            grounds=grounds,
            precedent_citations=precedents,
            undertakings=undertakings,
            prayer=prayer,
            verification=verification,
            formatted_document=formatted_doc
        )
