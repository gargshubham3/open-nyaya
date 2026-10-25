from typing import List, Dict, Any, Optional
from datetime import datetime
from nyaya.models import FIRDetails, AuditFlag, AuditReport
from nyaya.mapper import LawMapper

class CaseAuditor:
    """
    District Court Procedural Auditor for Indian Criminal Proceedings.
    Audits FIRs, charge-sheets, and custody timelines against:
    - Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)
    - Code of Criminal Procedure, 1973 (CrPC)
    - Supreme Court landmark precedents (Arnesh Kumar, Satender Kumar Antil, D.K. Basu).
    """

    def __init__(self, mapper: Optional[LawMapper] = None):
        self.mapper = mapper or LawMapper()

    def audit(self, fir: FIRDetails) -> AuditReport:
        flags: List[AuditFlag] = []
        cross_exam_questions: List[str] = []

        # Find primary accused
        accused = fir.accused_list[0] if fir.accused_list else None
        accused_name = accused.name if accused else "Accused"

        # 1. Determine maximum punishment among all charged sections
        max_punishment_years = 0.0
        has_only_bailable = True
        charged_sections_readable = []

        for chg in fir.sections_charged:
            meta = self.mapper.get_offense_metadata(chg.act, chg.section)
            years = meta.get("punishment_years", 3.0)
            if years > max_punishment_years:
                max_punishment_years = years
            if not meta.get("bailable", True):
                has_only_bailable = False
            charged_sections_readable.append(f"{chg.act} {chg.section} ({meta.get('offense', '')})")

        # -------------------------------------------------------------
        # RULE 1: Notice of Appearance under BNSS Sec 35(3) (Old CrPC 41A)
        # -------------------------------------------------------------
        if max_punishment_years <= 7.0 and accused and accused.is_arrested:
            if fir.section_35_notice_issued is False or fir.section_35_notice_issued is None:
                flags.append(AuditFlag(
                    severity="CRITICAL",
                    rule_id="RULE-BNSS-35-NOTICE",
                    title="Violation of Mandatory Notice under Section 35(3) BNSS [Old CrPC 41A]",
                    violation_detail=(
                        f"All charged offences carry maximum imprisonment of 7 years or less "
                        f"(Max: {max_punishment_years:g} years). Police arrested {accused_name} without "
                        "prior service of Notice of Appearance under Section 35(3) BNSS."
                    ),
                    statutory_reference="Section 35(3) to 35(6) of BNSS, 2023 (formerly Section 41A CrPC)",
                    judicial_precedent="Satender Kumar Antil v. CBI (2022) 10 SCC 51; Arnesh Kumar v. State of Bihar (2014) 8 SCC 273",
                    suggested_defense_argument=(
                        "The arrest is unlawful in violation of the binding directions of the Hon'ble Supreme Court "
                        "in Satender Kumar Antil (Category A). Since Section 35 BNSS notice was not served, "
                        "the applicant is entitled to regular bail forthwith."
                    )
                ))
                cross_exam_questions.append(
                    "Did you issue and serve a notice of appearance under Section 35(3) BNSS upon the accused prior to his arrest?"
                )
                cross_exam_questions.append(
                    "Is there any written recording in the Case Diary demonstrating why immediate arrest was indispensable?"
                )

        # -------------------------------------------------------------
        # RULE 2: Mandatory Audio-Video Recording under BNSS Section 105
        # -------------------------------------------------------------
        if fir.recovery_made is True or fir.videography_recorded is False:
            if fir.videography_recorded is False:
                flags.append(AuditFlag(
                    severity="HIGH",
                    rule_id="RULE-BNSS-105-VIDEOGRAPHY",
                    title="Non-Compliance with Mandatory Videography under Section 105 BNSS",
                    violation_detail=(
                        "Section 105 BNSS strictly mandates that search and seizure proceedings must be "
                        "recorded through audio-video electronic means and submitted to the Magistrate. "
                        "No valid electronic recording was conducted or cataloged."
                    ),
                    statutory_reference="Section 105 of BNSS, 2023; Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (BSA)",
                    judicial_precedent="Shafhi Mohammad v. State of Himachal Pradesh (2018) 5 SCC 311",
                    suggested_defense_argument=(
                        "The alleged recovery is contaminated and untrustworthy due to direct violation of "
                        "the statutory mandate of Section 105 BNSS requiring contemporaneous electronic videography."
                    )
                ))
                cross_exam_questions.append(
                    "Was the entire search and seizure videographed as mandated under Section 105 of BNSS, 2023?"
                )
                cross_exam_questions.append(
                    "Can you produce the hash value, certificate, and electronic device used to record the alleged seizure?"
                )

        # -------------------------------------------------------------
        # RULE 3: Maximum Undertrial Detention under BNSS Section 479 (Old CrPC 436A)
        # -------------------------------------------------------------
        if accused and accused.is_arrested and accused.custody_days is not None:
            custody_years = accused.custody_days / 365.25
            
            # BNSS 479: 1/3rd threshold for first offenders, 1/2 for others (excluding death/life)
            threshold_fraction = (1.0 / 3.0) if accused.is_first_offender else (1.0 / 2.0)
            threshold_years = max_punishment_years * threshold_fraction

            if max_punishment_years < 99.0 and custody_years >= threshold_years:
                flags.append(AuditFlag(
                    severity="CRITICAL",
                    rule_id="RULE-BNSS-479-STATUTORY-BAIL",
                    title="Absolute Statutory Right to Bail under Section 479 BNSS [Old CrPC 436A]",
                    violation_detail=(
                        f"The accused has undergone {accused.custody_days} days ({custody_years:.1f} years) in custody, "
                        f"which exceeds the statutory threshold of {threshold_fraction*100:.0f}% of the maximum punishment "
                        f"({max_punishment_years:g} years) for a {'first-time' if accused.is_first_offender else 'repeat'} offender."
                    ),
                    statutory_reference="Section 479 of BNSS, 2023 (formerly Section 436A CrPC)",
                    judicial_precedent="In Re: Policy Strategy for Grant of Bail (SMWP (Crl) No. 4/2021); Bhim Singh v. UOI (2015) 13 SCC 605",
                    suggested_defense_argument=(
                        f"The applicant is entitled to mandatory statutory bail as a matter of right under Section 479 BNSS, "
                        f"having completed more than {threshold_fraction*100:.0f}% of maximum custody without completion of trial."
                    )
                ))
                cross_exam_questions.append(
                    f"Isn't it correct that the accused has already served {accused.custody_days} days in detention while trial is yet to commence?"
                )

        # -------------------------------------------------------------
        # RULE 4: 24-Hour Production Before Magistrate (Article 22(2) & BNSS 58)
        # -------------------------------------------------------------
        if fir.magistrate_production_hours is not None and fir.magistrate_production_hours > 24.0:
            flags.append(AuditFlag(
                severity="CRITICAL",
                rule_id="RULE-CONST-ART22-DETENTION",
                title="Unconstitutional Custody Exceeding 24 Hours [Art 22(2) & BNSS 58]",
                violation_detail=(
                    f"The accused was detained for {fir.magistrate_production_hours:.1f} hours prior to production "
                    "before the Judicial Magistrate, exceeding the constitutional and statutory ceiling of 24 hours."
                ),
                statutory_reference="Article 22(2) Constitution of India; Section 58 of BNSS, 2023 (formerly Section 57 CrPC)",
                judicial_precedent="D.K. Basu v. State of West Bengal (1997) 1 SCC 416; Manoj v. State of M.P. (1999) 3 SCC 715",
                suggested_defense_argument=(
                    "The initial detention beyond 24 hours without judicial order is illegal and violative of Article 21 and 22(2), "
                    "vitiating the subsequent police remand."
                )
            ))
            cross_exam_questions.append(
                f"What is the exact time when you took the accused into physical custody, and what time was he produced before the Magistrate?"
            )

        # -------------------------------------------------------------
        # RULE 5: Arrest Memo & Independent Witness (BNSS Section 36 / CrPC 41B)
        # -------------------------------------------------------------
        if fir.independent_witness_present is False and accused and accused.is_arrested:
            flags.append(AuditFlag(
                severity="HIGH",
                rule_id="RULE-BNSS-36-WITNESS",
                title="Arrest Memo Defect: Lack of Independent Attesting Witness",
                violation_detail=(
                    "Section 36 BNSS mandates that every arrest memo must be attested by at least one independent "
                    "witness (family member or respectable member of the locality). No independent witness was joined."
                ),
                statutory_reference="Section 36 of BNSS, 2023 (formerly Section 41B CrPC)",
                judicial_precedent="D.K. Basu Guidelines (1997) 1 SCC 416",
                suggested_defense_argument=(
                    "The arrest memo lacks independent attestation from any local resident, indicating manufactured police paperwork."
                )
            ))
            cross_exam_questions.append(
                "Did you make any written effort to call local shopkeepers or residents to sign the arrest memo?"
            )

        # -------------------------------------------------------------
        # RULE 6: Delay in Lodging FIR
        # -------------------------------------------------------------
        if fir.date_of_occurrence and fir.date_of_report:
            try:
                # Basic string or ISO date comparison
                t_occ = datetime.fromisoformat(fir.date_of_occurrence.replace("Z", ""))
                t_rep = datetime.fromisoformat(fir.date_of_report.replace("Z", ""))
                diff_hours = (t_rep - t_occ).total_seconds() / 3600.0
                if diff_hours > 48.0:
                    flags.append(AuditFlag(
                        severity="MEDIUM",
                        rule_id="RULE-FIR-DELAY",
                        title=f"Unexplained FIR Delay ({diff_hours:.0f} hours)",
                        violation_detail=(
                            f"There is a substantial delay of {diff_hours:.0f} hours between the alleged occurrence "
                            f"({fir.date_of_occurrence}) and registration of FIR ({fir.date_of_report}) with no plausible explanation."
                        ),
                        statutory_reference="Section 173 of BNSS, 2023 (formerly Section 154 CrPC)",
                        judicial_precedent="State of A.P. v. M. Madhusudhan Rao (2008) 15 SCC 582; Lalita Kumari v. Govt of UP (2014) 2 SCC 1",
                        suggested_defense_argument=(
                            "The inordinate and unexplained delay in lodging the FIR gives rise to a legitimate suspicion "
                            "of deliberation, concoction, and roping in innocent persons as an afterthought."
                        )
                    ))
                    cross_exam_questions.append(
                        f"Why was there a delay of {diff_hours:.0f} hours in lodging the FIR when the police station is within accessible distance?"
                    )
            except Exception:
                pass

        # -------------------------------------------------------------
        # Calculate Bail Favourability Score (0 to 100)
        # -------------------------------------------------------------
        score = 50  # Baseline neutral
        for f in flags:
            if f.severity == "CRITICAL":
                score += 25
            elif f.severity == "HIGH":
                score += 15
            elif f.severity == "MEDIUM":
                score += 8

        if has_only_bailable:
            score = 100
        elif max_punishment_years <= 7.0:
            score += 10

        score = max(5, min(95, score))

        summary = (
            f"Audit completed for FIR No. {fir.fir_number} ({fir.police_station}). "
            f"Identified {len(flags)} procedural flags. "
            f"Bail favourability index: {score}/100. "
            f"Primary offense threshold: {max_punishment_years:g} years maximum imprisonment."
        )

        return AuditReport(
            fir_number=fir.fir_number,
            police_station=fir.police_station,
            accused_name=accused_name,
            flags=flags,
            bail_favourability_score=score,
            summary=summary,
            cross_examination_questions=cross_exam_questions
        )
