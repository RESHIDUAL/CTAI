import pytest
from app.core.phi_scrubber import SyntheticPhiScrubber
from app.models.patient_models import RawSyntheticPatient

def test_phi_scrubber_redaction_and_zero_leak():
    raw = RawSyntheticPatient(
        id="999",
        raw_name="John Doe",
        raw_mrn="MRN-123456",
        raw_dob="1978-03-14",
        raw_phone="(555) 123-4567",
        raw_address="123 Maple Street, Anytown USA",
        raw_doctor="Dr. Gregory House, MD",
        age_years=48,
        gender="Male",
        clinical_notes=[
            "Patient John Doe arrived with MRN: 123456, phone (555) 123-4567, email john.doe@example.com, SSN 000-12-3456. Resides at 123 Maple Street. Attending was Dr. Gregory House."
        ]
    )

    deid = SyntheticPhiScrubber.deidentify_patient(raw)

    # Verify pseudonym assigned
    assert deid.pseudonym_id == "PATIENT-999"
    assert deid.age_years == 48  # Retained per HIPAA safe harbor for age < 89

    # Verify note is sanitized across all 8 identifiers
    cleaned_note = deid.clinical_notes[0]
    assert "John" not in cleaned_note
    assert "Doe" not in cleaned_note
    assert "123456" not in cleaned_note
    assert "(555) 123-4567" not in cleaned_note
    assert "john.doe@example.com" not in cleaned_note
    assert "000-12-3456" not in cleaned_note
    assert "PATIENT-999" in cleaned_note

    # Verify Redaction Certificate covers all supported categories
    cert = deid.redaction_cert
    assert cert is not None
    assert cert.zero_leak_verified is True
    categories_found = {r.category for r in cert.redactions}
    assert "NAME" in categories_found
    assert "MRN" in categories_found
    assert "PHONE" in categories_found
    assert "EMAIL" in categories_found
    assert "SSN" in categories_found
    assert "DOB" in categories_found
    assert "ADDRESS" in categories_found
    assert "CLINICIAN" in categories_found
