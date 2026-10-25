import pytest
from nyaya.drafter import BailDrafter
from nyaya.auditor import CaseAuditor
from nyaya.models import FIRDetails, AccusedPerson, SectionCharge

@pytest.fixture(scope="module")
def drafter():
    return BailDrafter()

@pytest.fixture(scope="module")
def auditor():
    return CaseAuditor()

def test_draft_bail_contents(drafter, auditor):
    fir = FIRDetails(
        fir_number="210/2026",
        year=2026,
        police_station="Noida Sector 20",
        district="Gautam Buddha Nagar",
        state="Uttar Pradesh",
        accused_list=[AccusedPerson(
            name="Pawan Sharma",
            is_arrested=True,
            custody_days=25
        )],
        sections_charged=[
            SectionCharge(act="IPC", section="420"),
            SectionCharge(act="IPC", section="120B")
        ],
        section_35_notice_issued=False,
        videography_recorded=False,
        recovery_made=True
    )

    report = auditor.audit(fir)
    draft = drafter.draft_bail(fir, report)

    assert "IN THE COURT OF THE LEARNED" in draft.court_heading
    assert "PAWAN SHARMA" in draft.case_title
    assert "SECTION 480" in draft.statutory_provision.upper()
    assert "Satender Kumar Antil" in draft.formatted_document
    assert "Arnesh Kumar" in draft.formatted_document
    assert "Section 318" in draft.charges_formatted
    assert "PRAYER" in draft.formatted_document
    assert "VERIFICATION" in draft.formatted_document
    assert len(draft.grounds) >= 5
