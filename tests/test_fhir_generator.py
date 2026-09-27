import pytest
from app.services.fhir_generator import SyntheticFHIRGenerator

def test_generate_borderline_egfr_eligible_bundle():
    bundle = SyntheticFHIRGenerator.generate_borderline_fhir_bundle("egfr_upper_borderline_eligible")
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) >= 3
    
    patient = SyntheticFHIRGenerator.convert_bundle_to_raw_patient(bundle)
    assert patient.id.startswith("PAT-FHIR-")
    assert "eGFR" in patient.labs
    assert patient.labs["eGFR"].value == 59.9

def test_generate_borderline_egfr_ineligible_bundle():
    bundle = SyntheticFHIRGenerator.generate_borderline_fhir_bundle("egfr_upper_borderline_ineligible")
    patient = SyntheticFHIRGenerator.convert_bundle_to_raw_patient(bundle)
    assert "eGFR" in patient.labs
    assert patient.labs["eGFR"].value == 60.1

def test_generate_borderline_washout_bundles():
    fail_bundle = SyntheticFHIRGenerator.generate_borderline_fhir_bundle("washout_borderline_fail")
    fail_pat = SyntheticFHIRGenerator.convert_bundle_to_raw_patient(fail_bundle)
    assert len(fail_pat.medications) >= 1
    assert fail_pat.medications[0].last_taken_day_offset == -29

    pass_bundle = SyntheticFHIRGenerator.generate_borderline_fhir_bundle("washout_borderline_pass")
    pass_pat = SyntheticFHIRGenerator.convert_bundle_to_raw_patient(pass_bundle)
    assert len(pass_pat.medications) >= 1
    assert pass_pat.medications[0].last_taken_day_offset == -31
