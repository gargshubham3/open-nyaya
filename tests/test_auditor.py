import pytest
from nyaya.auditor import CaseAuditor
from nyaya.models import FIRDetails, AccusedPerson, SectionCharge

@pytest.fixture(scope="module")
def auditor():
    return CaseAuditor()

def test_audit_section_35_notice_violation(auditor):
    # Offense <= 7 years (IPC 420 is 7 yrs), no notice issued, arrested
    fir = FIRDetails(
        fir_number="12/2026",
        year=2026,
        police_station="Cyber Crime PS",
        district="Bengaluru",
        accused_list=[AccusedPerson(name="Amit Roy", is_arrested=True)],
        sections_charged=[SectionCharge(act="IPC", section="420")],
        section_35_notice_issued=False
    )
    report = auditor.audit(fir)
    flag_ids = [f.rule_id for f in report.flags]
    assert "RULE-BNSS-35-NOTICE" in flag_ids
    assert report.bail_favourability_score >= 70

def test_audit_no_section_35_violation_for_heinous_crimes(auditor):
    # Offense > 7 years (IPC 302 murder), notice under Sec 35 does not apply
    fir = FIRDetails(
        fir_number="15/2026",
        year=2026,
        police_station="Kotwali",
        district="Varanasi",
        accused_list=[AccusedPerson(name="Kailash", is_arrested=True)],
        sections_charged=[SectionCharge(act="IPC", section="302")],
        section_35_notice_issued=False
    )
    report = auditor.audit(fir)
    flag_ids = [f.rule_id for f in report.flags]
    assert "RULE-BNSS-35-NOTICE" not in flag_ids

def test_audit_videography_violation(auditor):
    fir = FIRDetails(
        fir_number="20/2026",
        year=2026,
        police_station="Andheri",
        district="Mumbai",
        accused_list=[AccusedPerson(name="Suresh", is_arrested=True)],
        sections_charged=[SectionCharge(act="IPC", section="379")],
        videography_recorded=False,
        recovery_made=True
    )
    report = auditor.audit(fir)
    flag_ids = [f.rule_id for f in report.flags]
    assert "RULE-BNSS-105-VIDEOGRAPHY" in flag_ids

def test_audit_undertrial_custody_threshold(auditor):
    # Theft is max 3 years (approx 1095 days).
    # 1/3rd for first offender is approx 365 days.
    # Accused has been in jail for 400 days -> statutory right to bail under BNSS 479!
    fir = FIRDetails(
        fir_number="99/2026",
        year=2026,
        police_station="Civil Lines",
        district="Delhi",
        accused_list=[AccusedPerson(
            name="Imran Khan",
            is_arrested=True,
            custody_days=400,
            is_first_offender=True
        )],
        sections_charged=[SectionCharge(act="IPC", section="379")]
    )
    report = auditor.audit(fir)
    flag_ids = [f.rule_id for f in report.flags]
    assert "RULE-BNSS-479-STATUTORY-BAIL" in flag_ids

def test_audit_unconstitutional_custody_over_24h(auditor):
    fir = FIRDetails(
        fir_number="45/2026",
        year=2026,
        police_station="South Ext",
        district="Delhi",
        accused_list=[AccusedPerson(name="Mohan", is_arrested=True)],
        sections_charged=[SectionCharge(act="IPC", section="323")],
        magistrate_production_hours=36.0
    )
    report = auditor.audit(fir)
    flag_ids = [f.rule_id for f in report.flags]
    assert "RULE-CONST-ART22-DETENTION" in flag_ids
