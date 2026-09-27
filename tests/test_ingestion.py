import pytest
import io
import docx
import pandas as pd
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app.services.ingestion_service import IngestionService

client = TestClient(app)

def test_ingest_protocol_text():
    sample_text = (
        "Phase 3 Protocol NCT05912345. "
        "Inclusion Criteria: "
        "1. Subject eGFR between 30 and 60 mL/min/1.73m2. "
        "2. HbA1c between 7.0 and 10.5%. "
        "3. Age >= 18 years."
    )
    proto = IngestionService.ingest_protocol_document(sample_text, title="Renal Study")
    assert proto.nct_id == "NCT05912345"
    assert len(proto.criteria) >= 2
    concept_names = [c.concept_name for c in proto.criteria]
    assert "eGFR" in concept_names
    assert "HbA1c" in concept_names

def test_ingest_patient_text():
    sample_notes = (
        "Patient 58 yo male with Type 2 Diabetes Mellitus. "
        "eGFR: 45.5 mL/min/1.73m2. HbA1c: 8.2%. "
        "Discontinued semaglutide 35 days ago."
    )
    patient = IngestionService.ingest_patient_record(sample_notes, name="Marcus Clinical")
    assert patient.age_years == 58
    assert "eGFR" in patient.labs
    assert patient.labs["eGFR"].value == 45.5
    assert len(patient.diagnoses) >= 1
    assert any("Diabetes" in d.condition_name for d in patient.diagnoses)

def test_ingest_protocol_file_upload():
    content = b"Study NCT09911223. Inclusion: eGFR between 25 and 55 mL/min/1.73m2. HbA1c between 6.5 and 9.0%."
    files = {"file": ("protocol_upload.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/api/ingest/protocol/file", files=files, data={"title": "Uploaded Protocol"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["protocol"]["nct_id"] == "NCT09911223"

def test_ingest_ehr_file_upload():
    content = b"Candidate 62 yo female with NSCLC. Platelets: 180. ANC: 2500."
    files = {"file": ("patient_record.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/api/ingest/ehr/file", files=files, data={"name": "Sarah Miller"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["patient"]["age_years"] == 62
    assert "Platelets" in data["patient"]["labs"]

def test_get_ingest_library():
    response = client.get("/api/ingest/library")
    assert response.status_code == 200
    data = response.json()
    assert "protocols" in data
    assert "patients" in data
    assert len(data["protocols"]) > 0
    assert len(data["patients"]) > 0

def test_ingest_word_docx():
    doc = docx.Document()
    doc.add_heading("Trial Protocol NCT08812345", 0)
    doc.add_paragraph("Inclusion Criteria: eGFR between 35 and 65 mL/min/1.73m2. HbA1c between 7.2 and 9.8%.")
    buf = io.BytesIO()
    doc.save(buf)
    
    files = {"file": ("protocol.docx", io.BytesIO(buf.getvalue()), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/ingest/protocol/file", files=files, data={"title": "Word Protocol"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["protocol"]["nct_id"] == "NCT08812345"

def test_ingest_excel_xlsx():
    df = pd.DataFrame([
        {"Biomarker": "eGFR", "Value": "48.2", "Unit": "mL/min/1.73m2"},
        {"Biomarker": "HbA1c", "Value": "8.5", "Unit": "%"}
    ])
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    
    files = {"file": ("patient_labs.xlsx", io.BytesIO(buf.getvalue()), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res = client.post("/api/ingest/ehr/file", files=files, data={"name": "Lab Excel Subject"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "eGFR" in data["patient"]["labs"]

def test_ingest_image_ocr():
    img = Image.new("RGB", (320, 70), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Patient 56 yo male eGFR: 52.4 HbA1c: 7.9%", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    files = {"file": ("scanned_ehr.png", io.BytesIO(buf.getvalue()), "image/png")}
    res = client.post("/api/ingest/ehr/file", files=files, data={"name": "OCR Patient"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["patient"]["age_years"] == 56
    assert "eGFR" in data["patient"]["labs"]

def test_ingest_synthetic_pdf_protocol_and_ehr():
    import os
    proto_path = r"C:\Users\Eshwar G\Downloads\Synthetic_Clinical_Trial_Protocol.pdf"
    ehr_path = r"C:\Users\Eshwar G\Downloads\Synthetic_Deidentified_EHR.pdf"
    
    if os.path.exists(proto_path) and os.path.exists(ehr_path):
        with open(proto_path, "rb") as f:
            p_bytes = f.read()
        with open(ehr_path, "rb") as f:
            e_bytes = f.read()
            
        p_files = {"file": ("Synthetic_Clinical_Trial_Protocol.pdf", io.BytesIO(p_bytes), "application/pdf")}
        p_res = client.post("/api/ingest/protocol/file", files=p_files, data={"title": "Synthetic Protocol"})
        assert p_res.status_code == 200
        p_data = p_res.json()
        assert p_data["status"] == "SUCCESS"
        assert p_data["protocol"]["nct_id"] == "SYN-RENAL-001"
        assert len(p_data["protocol"]["criteria"]) >= 6
        
        e_files = {"file": ("Synthetic_Deidentified_EHR.pdf", io.BytesIO(e_bytes), "application/pdf")}
        e_res = client.post("/api/ingest/ehr/file", files=e_files, data={"name": "Synthetic EHR"})
        assert e_res.status_code == 200
        e_data = e_res.json()
        assert e_data["status"] == "SUCCESS"
        assert e_data["patient"]["age_years"] == 54
        assert e_data["patient"]["gender"] == "F"
        assert "eGFR" in e_data["patient"]["labs"]
        
        # Test full screening against each other
        screen_res = client.post("/api/screen", json={
            "protocol_id": p_data["protocol"]["id"],
            "patient_id": e_data["patient"]["id"]
        })
        assert screen_res.status_code == 200
        dossier = screen_res.json()
        assert dossier["decision"] == "ELIGIBLE"
        assert dossier["fail_count"] == 0
        assert len(dossier["sha256_checksum"]) == 64

