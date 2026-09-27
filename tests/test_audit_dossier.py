import pytest
from app.services.dossier_export import DossierExportService

def test_sha256_canonical_hashing_tamper_detection():
    payload1 = {
        "protocol_id": "NCT05128990",
        "patient_id": "PATIENT-001",
        "decision": "ELIGIBLE",
        "evaluations": [
            {"criterion_id": "INC_01", "result": "PASS", "val": 54},
            {"criterion_id": "INC_02", "result": "PASS", "val": 44.0}
        ]
    }

    hash1 = DossierExportService.calculate_sha256(payload1)
    assert len(hash1) == 64

    # Identical content with different key order must produce identical SHA-256 (canonical sorting)
    payload1_reordered = {
        "decision": "ELIGIBLE",
        "evaluations": [
            {"criterion_id": "INC_01", "result": "PASS", "val": 54},
            {"criterion_id": "INC_02", "result": "PASS", "val": 44.0}
        ],
        "patient_id": "PATIENT-001",
        "protocol_id": "NCT05128990"
    }
    hash1_reordered = DossierExportService.calculate_sha256(payload1_reordered)
    assert hash1 == hash1_reordered

    # Altered value must produce completely different hash (tamper evidence)
    payload_tampered = {
        "protocol_id": "NCT05128990",
        "patient_id": "PATIENT-001",
        "decision": "INELIGIBLE",  # Tampered!
        "evaluations": payload1["evaluations"]
    }
    hash_tampered = DossierExportService.calculate_sha256(payload_tampered)
    assert hash1 != hash_tampered
