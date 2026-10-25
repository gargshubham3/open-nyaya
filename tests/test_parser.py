import pytest
from nyaya.parser import FIRParser

@pytest.fixture(scope="module")
def parser():
    return FIRParser()

def test_parse_sample_fir(parser):
    text = """
    FIRST INFORMATION REPORT
    FIR No. 156/2026
    Police Station: Gomti Nagar
    District: Lucknow
    State: Uttar Pradesh
    Date of Report: 2026-04-12
    Complainant: Alok Verma
    Accused: Sunil Mehta
    Offences: Charged under IPC Section 420 and 120B.
    Details: The accused was arrested without notice under section 35. Seizure was made without videography. Accused has been 15 days in custody.
    """
    fir = parser.parse_text(text)
    assert fir.fir_number == "156/2026"
    assert "Gomti Nagar" in fir.police_station
    assert fir.accused_list[0].name == "Sunil Mehta"
    assert fir.section_35_notice_issued is False
    assert fir.videography_recorded is False
    assert fir.accused_list[0].custody_days == 15
    assert len(fir.sections_charged) >= 2
