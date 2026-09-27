from typing import List, Dict, Any, Optional
from app.models.evaluation_models import (
    DecisionProvenance,
    PatientEvidence,
    EvaluationDetail,
    ProtocolSource,
    EvaluationResult
)

class ProvenanceManager:
    """
    Manages DecisionProvenance creation, canonical formatting, and verification.
    Ensures that evaluations are never independently reconstructed across the application.
    """

    @staticmethod
    def create_provenance(
        criterion_id: str,
        criterion_text: str,
        patient_value: Any,
        patient_unit: Optional[str],
        evidence_source: str,
        study_day: Optional[int],
        operator: str,
        threshold: Any,
        result: str,
        expression: str,
        protocol_page: int,
        protocol_section: str,
        raw_clause: Optional[str] = None,
        failure_reason: Optional[str] = None,
        evaluator: str = "deterministic_engine_v1.0"
    ) -> DecisionProvenance:
        return DecisionProvenance(
            criterion_id=criterion_id,
            criterion_text=criterion_text,
            patient_evidence=PatientEvidence(
                value=patient_value,
                unit=patient_unit,
                source=evidence_source,
                study_day=study_day
            ),
            evaluation=EvaluationDetail(
                operator=operator,
                threshold=threshold,
                result=EvaluationResult(result),
                expression=expression,
                evaluated_by=evaluator
            ),
            protocol_source=ProtocolSource(
                page=protocol_page,
                section=protocol_section,
                raw_clause=raw_clause
            ),
            failure_reason=failure_reason
        )

    @staticmethod
    def to_canonical_dict(provenance_list: List[DecisionProvenance]) -> List[Dict[str, Any]]:
        """
        Produces an immutable, sorted canonical representation for SHA-256 integrity hashing.
        """
        raw = [p.model_dump() for p in provenance_list]
        return sorted(raw, key=lambda x: x["criterion_id"])
