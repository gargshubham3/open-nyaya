import pytest
from fastapi.testclient import TestClient
from nyaya.web import app

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_api_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "open-nyaya" in response.text

def test_api_lookup(client):
    response = client.post("/api/lookup", json={"act": "IPC", "section": "420"})
    assert response.status_code == 200
    data = response.json()
    assert data["target"]["section"] == "318"
    assert "Cheating" in data["target"]["title"]

def test_api_translate(client):
    response = client.post("/api/translate", json={"charges": "IPC 420, 120B"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_api_audit(client):
    sample = "FIR No. 99/2026. PS: Hazratganj. Accused Ramesh Kumar arrested without notice under IPC 420."
    response = client.post("/api/audit", json={"fir_text": sample})
    assert response.status_code == 200
    data = response.json()
    assert "bail_favourability_score" in data
    assert len(data["flags"]) > 0

def test_api_draft_bail(client):
    payload = {
        "accused_name": "Ramesh Kumar",
        "fir_number": "99/2026",
        "police_station": "Hazratganj",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
        "sections_charged": "IPC 420, 120B",
        "custody_days": 20,
        "section_35_notice_violated": True,
        "videography_missing": True
    }
    response = client.post("/api/draft-bail", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "formatted_document" in data
    assert "SECTION 480" in data["statutory_provision"].upper()
