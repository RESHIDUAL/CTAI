import pytest
from agents.configs import LyzrAgentConfig
from agents.protocol_criteria_agent import ProtocolCriteriaAgent
from agents.medical_safety_agent import MedicalSafetyAgent
from agents.regulatory_audit_agent import RegulatoryAuditAgent
from agents.orchestrator import MultiAgentOrchestrator

def test_protocol_criteria_agent_execution():
    agent = ProtocolCriteriaAgent()
    res = agent.extract_criteria("Inclusion: eGFR 30 to 60 mL/min", "trace_agent_01")
    assert res["status"] == "SUCCESS"
    assert "data" in res

def test_medical_safety_agent_execution():
    agent = MedicalSafetyAgent()
    sample_patient = {
        "labs": {"eGFR": {"value": 45.0, "unit": "mL/min/1.73m2"}},
        "diagnoses": [{"condition_name": "Type 2 Diabetes Mellitus", "icd10": "E11.9", "is_active": True}],
        "medications": []
    }
    res = agent.validate_safety_profiles(sample_patient, "trace_agent_02")
    assert res["status"] == "VALIDATED"
    assert res["ontology_validation"]["snomed_aligned"] is True

def test_regulatory_audit_agent_execution():
    agent = RegulatoryAuditAgent()
    payload = {"decision": "ELIGIBLE", "patient": "PAT-001"}
    res = agent.synthesize_dossier(payload, "trace_agent_03")
    assert res["status"] == "SYNTHESIZED"
    assert len(res["sha256_seal"]) == 64

def test_multi_agent_orchestrator_pipeline():
    orchestrator = MultiAgentOrchestrator()
    score = orchestrator.calculate_confidence_score(pass_count=4, fail_count=0, unknown_count=0)
    assert score == 1.00

    low_score = orchestrator.calculate_confidence_score(pass_count=3, fail_count=0, unknown_count=1)
    assert low_score < 0.90

    pause_res = orchestrator.check_hitl_pause(low_score, "trace_agent_04", {})
    assert pause_res["hitl_paused"] is True
