import pytest
from app.core.validation_gate import ProtocolValidationGate

def test_validation_gate_valid_criterion():
    valid_crit = {
        "criterion_id": "INC_TEST_01",
        "type": "INCLUSION",
        "category": "BIOMARKER",
        "concept_name": "eGFR",
        "operator": ">=",
        "threshold": 60.0,
        "unit": "mL/min/1.73m2",
        "protocol_citation": {
            "page": 10,
            "section": "4.1 Inclusion Criteria",
            "paragraph": 2,
            "raw_clause": "eGFR >= 60.0 mL/min/1.73m2"
        },
        "description": "eGFR test"
    }
    is_valid, reason, obj = ProtocolValidationGate.validate_criterion(valid_crit)
    assert is_valid is True
    assert obj is not None
    assert obj.criterion_id == "INC_TEST_01"

def test_validation_gate_rejects_missing_between_bounds():
    malformed_between = {
        "criterion_id": "INC_TEST_02",
        "type": "INCLUSION",
        "category": "BIOMARKER",
        "concept_name": "HbA1c",
        "operator": "BETWEEN",
        "threshold": [7.5],  # Missing upper bound!
        "unit": "%",
        "protocol_citation": {"page": 10, "section": "4.1"},
        "description": "HbA1c test"
    }
    is_valid, reason, obj = ProtocolValidationGate.validate_criterion(malformed_between)
    assert is_valid is False
    assert "BETWEEN requires 2 numeric bounds" in reason
    assert obj is None

def test_validation_gate_rejects_invalid_operator():
    bad_op = {
        "criterion_id": "INC_TEST_03",
        "type": "INCLUSION",
        "category": "BIOMARKER",
        "concept_name": "ANC",
        "operator": "APPROXIMATELY",  # Illegal operator!
        "threshold": 1500,
        "unit": "/uL",
        "protocol_citation": {"page": 10, "section": "4.1"},
        "description": "ANC test"
    }
    is_valid, reason, obj = ProtocolValidationGate.validate_criterion(bad_op)
    assert is_valid is False
    assert "Invalid or missing operator" in reason

def test_validation_gate_rejects_missing_citation():
    no_citation = {
        "criterion_id": "INC_TEST_04",
        "type": "INCLUSION",
        "category": "DEMOGRAPHIC",
        "concept_name": "Age",
        "operator": ">=",
        "threshold": 18,
        "protocol_citation": {},  # Missing page & section
        "description": "Age test"
    }
    is_valid, reason, obj = ProtocolValidationGate.validate_criterion(no_citation)
    assert is_valid is False
    assert "Citation missing" in reason
