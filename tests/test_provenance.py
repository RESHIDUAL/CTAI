import pytest
from app.core.provenance import ProvenanceManager
from app.models.evaluation_models import EvaluationResult

def test_provenance_creation_and_canonical_sorting():
    p1 = ProvenanceManager.create_provenance(
        criterion_id="INC_02",
        criterion_text="eGFR >= 60",
        patient_value=59.9,
        patient_unit="mL/min/1.73m2",
        evidence_source="Lab Record LAB_0042",
        study_day=-3,
        operator=">=",
        threshold=60.0,
        result="FAIL",
        expression="59.9 >= 60.0",
        protocol_page=14,
        protocol_section="4.1 Inclusion Criteria",
        failure_reason="Below protocol threshold"
    )

    p2 = ProvenanceManager.create_provenance(
        criterion_id="INC_01",
        criterion_text="Age >= 18",
        patient_value=54,
        patient_unit="years",
        evidence_source="Demographics",
        study_day=0,
        operator=">=",
        threshold=18,
        result="PASS",
        expression="54 >= 18",
        protocol_page=12,
        protocol_section="4.1 Inclusion Criteria"
    )

    assert p1.evaluation.result == EvaluationResult.FAIL
    assert p2.evaluation.result == EvaluationResult.PASS
    assert p1.patient_evidence.value == 59.9

    canonical = ProvenanceManager.to_canonical_dict([p1, p2])
    # Must be sorted by criterion_id
    assert canonical[0]["criterion_id"] == "INC_01"
    assert canonical[1]["criterion_id"] == "INC_02"
