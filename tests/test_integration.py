import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "21 CFR Part 11" in data["regulatory_mode"]

def test_api_protocols(client):
    res = client.get("/api/protocols")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    assert any(p["nct_id"] == "NCT05128990" for p in data)

def test_api_patients(client):
    res = client.get("/api/patients")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 7

def test_api_screen_eligible(client):
    # Patient 001 on T2D protocol is ELIGIBLE
    res = client.post("/api/screen", json={
        "protocol_id": "proto_t2d_ckd_02",
        "patient_id": "001"
    })
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["decision"] == "ELIGIBLE"
    assert dossier["fail_count"] == 0
    assert dossier["sha256_checksum"] is not None
    assert len(dossier["sha256_checksum"]) == 64

def test_api_screen_ineligible_with_why_breakdown(client):
    # Patient 002 has eGFR 61.2 (above 60 upper bound) -> INELIGIBLE
    res = client.post("/api/screen", json={
        "protocol_id": "proto_t2d_ckd_02",
        "patient_id": "002"
    })
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["decision"] == "INELIGIBLE"
    assert dossier["fail_count"] >= 1
    assert dossier["why_not_eligible"] is not None
    assert len(dossier["why_not_eligible"]["critical_barriers"]) >= 1

def test_api_adversarial_suite(client):
    res = client.post("/api/adversarial/run")
    assert res.status_code == 200
    data = res.json()
    assert data["suite_status"] == "PASSED"
    assert data["passed_tests"] == data["total_tests"]

def test_api_aims_telemetry(client):
    res = client.get("/api/aims/events")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "events" in data
    assert len(data["events"]) > 0

def test_static_index_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "CT·SCREEN" in res.text
    assert "21 CFR Part 11" in res.text
