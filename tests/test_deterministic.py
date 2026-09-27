import pytest
from app.core.deterministic_engine import DeterministicScreeningEngine
from app.models.protocol_models import CriterionDefinition, CriterionType, CriterionCategory, OperatorType, ProtocolCitation
from app.models.patient_models import DeidentifiedPatient, LabObservation, MedicationRecord
from app.models.dossier_models import EvaluationStatus, EligibilityDecision

def test_deterministic_boundary_math():
    crit = CriterionDefinition(
        criterion_id="INC_EGFR",
        type=CriterionType.INCLUSION,
        category=CriterionCategory.BIOMARKER,
        concept_name="eGFR",
        operator=OperatorType.BETWEEN,
        threshold=[30.0, 60.0],
        unit="mL/min/1.73m2",
        protocol_citation=ProtocolCitation(page=10, section="4.1", raw_clause="eGFR 30 to 60"),
        description="eGFR range test"
    )

    # 59.9 -> PASS
    pat_59_9 = DeidentifiedPatient(
        pseudonym_id="PAT-599", age_years=55, gender="M",
        labs={"eGFR": LabObservation(test_name="eGFR", value=59.9, unit="mL/min/1.73m2")}
    )
    res_59_9 = DeterministicScreeningEngine.evaluate_criterion(crit, pat_59_9)
    assert res_59_9.status == EvaluationStatus.PASS

    # 60.0 -> PASS (Inclusive boundary)
    pat_60_0 = DeidentifiedPatient(
        pseudonym_id="PAT-600", age_years=55, gender="M",
        labs={"eGFR": LabObservation(test_name="eGFR", value=60.0, unit="mL/min/1.73m2")}
    )
    res_60_0 = DeterministicScreeningEngine.evaluate_criterion(crit, pat_60_0)
    assert res_60_0.status == EvaluationStatus.PASS

    # 60.1 -> FAIL (Exceeds boundary)
    pat_60_1 = DeidentifiedPatient(
        pseudonym_id="PAT-601", age_years=55, gender="M",
        labs={"eGFR": LabObservation(test_name="eGFR", value=60.1, unit="mL/min/1.73m2")}
    )
    res_60_1 = DeterministicScreeningEngine.evaluate_criterion(crit, pat_60_1)
    assert res_60_1.status == EvaluationStatus.FAIL

def test_deterministic_missing_lab_causes_unknown():
    crit = CriterionDefinition(
        criterion_id="INC_HBA1C",
        type=CriterionType.INCLUSION,
        category=CriterionCategory.BIOMARKER,
        concept_name="HbA1c",
        operator=OperatorType.BETWEEN,
        threshold=[7.5, 10.5],
        unit="%",
        protocol_citation=ProtocolCitation(page=10, section="4.1", raw_clause="HbA1c 7.5 to 10.5%"),
        description="HbA1c range test"
    )

    # Patient missing HbA1c lab observation
    pat_missing = DeidentifiedPatient(pseudonym_id="PAT-MISSING", age_years=55, gender="F", labs={})
    res = DeterministicScreeningEngine.evaluate_criterion(crit, pat_missing)
    assert res.status == EvaluationStatus.UNKNOWN

    decision, _, _, _ = DeterministicScreeningEngine.screen_patient([crit], pat_missing)
    assert decision == EligibilityDecision.REQUIRES_HUMAN_REVIEW

def test_medication_washout_calculation():
    crit = CriterionDefinition(
        criterion_id="EXC_WASH",
        type=CriterionType.EXCLUSION,
        category=CriterionCategory.MEDICATION_WASHOUT,
        concept_name="GLP-1",
        operator=OperatorType.WASHOUT_DAYS,
        threshold=30,
        washout_days=30,
        protocol_citation=ProtocolCitation(page=15, section="4.2", raw_clause="Washout >= 30 days"),
        description="Washout test"
    )

    # 12 days ago -> FAIL (requires 30)
    pat_fail = DeidentifiedPatient(
        pseudonym_id="PAT-WASH-FAIL", age_years=60, gender="F",
        medications=[MedicationRecord(drug_name="Ozempic GLP-1", is_active=False, last_taken_day_offset=-12)]
    )
    res_fail = DeterministicScreeningEngine.evaluate_criterion(crit, pat_fail)
    assert res_fail.status == EvaluationStatus.FAIL

    # 45 days ago -> PASS
    pat_pass = DeidentifiedPatient(
        pseudonym_id="PAT-WASH-PASS", age_years=60, gender="F",
        medications=[MedicationRecord(drug_name="Ozempic GLP-1", is_active=False, last_taken_day_offset=-45)]
    )
    res_pass = DeterministicScreeningEngine.evaluate_criterion(crit, pat_pass)
    assert res_pass.status == EvaluationStatus.PASS
