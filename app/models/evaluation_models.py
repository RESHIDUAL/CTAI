from enum import Enum
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, Field

class EvaluationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class PatientEvidence(BaseModel):
    value: Any
    unit: Optional[str] = None
    source: str
    study_day: Optional[int] = None

class EvaluationDetail(BaseModel):
    operator: str
    threshold: Any
    result: EvaluationResult
    expression: str
    evaluated_by: str = "deterministic_engine_v1.0"

class ProtocolSource(BaseModel):
    page: int
    section: str
    raw_clause: Optional[str] = None

class DecisionProvenance(BaseModel):
    """
    Central Decision Provenance Model.
    The single source of truth for dashboard display, Why Not Eligible panel,
    audit dossier, JSON export, AIMS logs, HITL review, and SHA-256 hashing.
    """
    criterion_id: str
    criterion_text: str
    patient_evidence: PatientEvidence
    evaluation: EvaluationDetail
    protocol_source: ProtocolSource
    failure_reason: Optional[str] = None
