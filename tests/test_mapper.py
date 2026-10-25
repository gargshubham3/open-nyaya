import pytest
from nyaya.mapper import LawMapper

@pytest.fixture(scope="module")
def mapper():
    return LawMapper()

def test_ipc_to_bns_lookup(mapper):
    res = mapper.lookup("IPC", "420")
    assert res is not None
    assert "318" in res.target.section
    assert res.target.act == "Bharatiya Nyaya Sanhita, 2023"
    assert "Cheating" in res.target.title

def test_ipc_murder_lookup(mapper):
    res = mapper.lookup("IPC", "302")
    assert res is not None
    assert res.target.section == "103"
    assert "murder" in res.target.title.lower()

def test_ipc_conspiracy_lookup(mapper):
    res = mapper.lookup("IPC", "120B")
    assert res is not None
    assert res.target.section == "61"

def test_crpc_notice_lookup(mapper):
    res = mapper.lookup("CrPC", "41A")
    assert res is not None
    assert res.target.section == "35"
    assert res.target.act == "Bharatiya Nagarik Suraksha Sanhita, 2023"

def test_crpc_bail_lookup(mapper):
    res = mapper.lookup("CrPC", "437")
    assert res is not None
    assert res.target.section == "480"

    res_session = mapper.lookup("CrPC", "439")
    assert res_session is not None
    assert res_session.target.section == "483"

def test_iea_electronic_evidence_lookup(mapper):
    # Old Section 65B IEA -> Section 63 BSA
    res = mapper.lookup("IEA", "65B")
    assert res is not None
    assert res.target.section == "63"
    assert res.target.act == "Bharatiya Sakshya Adhiniyam, 2023"

def test_normalization_and_formatting(mapper):
    # Handles prefixes and spaces
    assert mapper.lookup("IPC", "sec. 420") is not None
    assert mapper.lookup("IPC", "u/s 420") is not None
    assert mapper.lookup("ipc", " 120-B ") is not None
    assert mapper.lookup("CRPC", "Section 41A") is not None

def test_nonexistent_section_returns_none(mapper):
    assert mapper.lookup("IPC", "99999") is None
    assert mapper.lookup("XYZ", "100") is None

def test_translate_string_multi(mapper):
    res = mapper.translate_string("Accused booked under IPC 420, 120B and 468")
    assert len(res) == 3
    sec_targets = [r.target.section for r in res]
    assert "318" in sec_targets
    assert "61" in sec_targets
    assert "336" in sec_targets

def test_search_murder(mapper):
    results = mapper.search("murder", limit=5)
    assert len(results) > 0
    assert any("murder" in (r.source.title.lower() if r.source else "") for r in results)

def test_offense_metadata(mapper):
    meta_420 = mapper.get_offense_metadata("IPC", "420")
    assert meta_420["punishment_years"] == 7.0
    assert meta_420["bailable"] is False
    assert meta_420["cognizable"] is True

    meta_302 = mapper.get_offense_metadata("IPC", "302")
    assert meta_302["punishment_years"] == 99.0
    assert meta_302["bailable"] is False
