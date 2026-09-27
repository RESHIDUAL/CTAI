from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class EligibilityDecision(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    REQUIRES_HUMAN_REVIEW = "REQUIRES_HUMAN_REVIEW"

class CriterionEvaluation(BaseModel):
    criterion_id: str
    criterion_type: str  # INCLUSION or EXCLUSION
    category: str
    concept_name: str
    rule_summary: str
    patient_value_str: str
    status: EvaluationStatus
    calculation_trace: str
    evidence_source: str
    protocol_citation: str
    failure_reason: Optional[str] = None

class WhyNotEligibleSummary(BaseModel):
    failed_criteria_count: int
    unknown_criteria_count: int
    critical_barriers: List[str] = []

class DecisionPathStep(BaseModel):
    step_number: int
    name: str
    status: str
    details: str

class AuditDossier(BaseModel):
    dossier_id: str
    protocol_nct_id: str
    protocol_title: str
    patient_pseudonym: str
    timestamp_utc: str
    decision: EligibilityDecision
    decision_rationale: str
    pass_count: int
    fail_count: int
    unknown_count: int
    evaluations: List[CriterionEvaluation]
    why_not_eligible: Optional[WhyNotEligibleSummary] = None
    decision_path: List[DecisionPathStep] = []
    
    # 21 CFR Part 11 Traceability & Integrity
    sha256_checksum: str
    regulatory_framework: str = "21 CFR Part 11-Oriented Traceability Prototype"
    protocol_representation: str = "Inspired by FDA M11 Concepts"
    coordinator_signature: Optional[Dict[str, Any]] = None
    crc_signature: Optional[Dict[str, Any]] = None
    aims_trace_id: str
    execution_mode: str = "Lyzr Agent API / Responsible AI"
    confidence_score: float = 1.0
    hitl_paused: bool = False
    hitl_reason: Optional[str] = None

