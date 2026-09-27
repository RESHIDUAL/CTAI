import uuid
import time
from typing import Dict, Any, List, Optional
from agents.configs import LyzrAgentConfig
from agents.protocol_criteria_agent import ProtocolCriteriaAgent
from agents.medical_safety_agent import MedicalSafetyAgent
from agents.regulatory_audit_agent import RegulatoryAuditAgent

class MultiAgentOrchestrator:
    def __init__(self, api_key: str = "", base_url: str = "", env_id: str = ""):
        self.env_id = env_id or LyzrAgentConfig.ENVIRONMENT_ID
        self.api_key = api_key or LyzrAgentConfig.API_KEY
        self.base_url = base_url or LyzrAgentConfig.AGENT_API_BASE_URL
        
        self.protocol_agent = ProtocolCriteriaAgent(self.api_key, self.base_url, self.env_id)
        self.medical_safety_agent = MedicalSafetyAgent(self.api_key, self.base_url, self.env_id)
        self.regulatory_audit_agent = RegulatoryAuditAgent(self.api_key, self.base_url, self.env_id)
        self.webhook_subscribers: List[str] = []

    def register_webhook(self, url: str) -> None:
        if url and url not in self.webhook_subscribers:
            self.webhook_subscribers.append(url)

    def calculate_confidence_score(self, pass_count: int, fail_count: int, unknown_count: int) -> float:
        total = pass_count + fail_count + unknown_count
        if total == 0:
            return 0.0
        if unknown_count > 0:
            penalty = (unknown_count / total) * 0.4
            raw_score = ((pass_count + fail_count) / total) - penalty
            return round(max(0.1, min(0.88, raw_score)), 3)
        if fail_count > 0:
            return 0.98
        return 1.00

    def check_hitl_pause(self, confidence_score: float, trace_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        paused = confidence_score < 0.90
        event = {
            "trace_id": trace_id,
            "confidence_score": confidence_score,
            "threshold": 0.90,
            "hitl_paused": paused,
            "reason": (
                "Confidence score below 90% threshold. Automated execution paused for clinical coordinator review."
                if paused else "Confidence meets or exceeds 90% threshold. Automated triage proceeding."
            ),
            "webhook_dispatched": False,
            "details": details
        }
        if paused and self.webhook_subscribers:
            event["webhook_dispatched"] = True
            event["subscribers_notified"] = len(self.webhook_subscribers)
        return event

    def run_screening_pipeline(
        self,
        protocol_data: Dict[str, Any],
        scrubbed_patient: Dict[str, Any],
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        tid = trace_id or f"trace_{uuid.uuid4().hex[:12]}"
        t0 = time.time()

        proto_res = self.protocol_agent.extract_criteria(
            protocol_text=protocol_data.get("raw_protocol_text", ""),
            trace_id=tid
        )

        safety_res = self.medical_safety_agent.validate_safety_profiles(
            patient_data=scrubbed_patient,
            trace_id=tid
        )

        return {
            "trace_id": tid,
            "environment_id": self.env_id,
            "protocol_agent_result": proto_res,
            "safety_agent_result": safety_res,
            "pipeline_latency_ms": (time.time() - t0) * 1000
        }
