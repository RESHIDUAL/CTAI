import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AIMSEvent(BaseModel):
    event_id: str
    trace_id: str
    agent_name: str
    event_type: str
    timestamp: str
    latency_ms: float
    tokens_consumed: int
    policy_status: str  # COMPLIANT | FLAGGED | BLOCKED
    details: Dict[str, Any]

class LyzrAIMSGovernance:
    """
    Lyzr AIMS (AI Management System) Telemetry and Governance Layer.
    Captures immutable execution traces, policy validations, token usage, and latency.
    """

    _events: List[AIMSEvent] = []

    @classmethod
    def record_event(
        cls,
        trace_id: str,
        agent_name: str,
        event_type: str,
        latency_ms: float,
        tokens_consumed: int,
        policy_status: str,
        details: Dict[str, Any]
    ) -> AIMSEvent:
        event = AIMSEvent(
            event_id=f"aims_evt_{uuid.uuid4().hex[:10]}",
            trace_id=trace_id,
            agent_name=agent_name,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            latency_ms=round(latency_ms, 2),
            tokens_consumed=tokens_consumed,
            policy_status=policy_status,
            details=details
        )
        cls._events.append(event)
        # Keep last 200 events in circular log
        if len(cls._events) > 200:
            cls._events.pop(0)
        return event

    @classmethod
    def get_events(cls, trace_id: Optional[str] = None) -> List[AIMSEvent]:
        if trace_id:
            return [e for e in cls._events if e.trace_id == trace_id]
        return list(reversed(cls._events))

    @classmethod
    def get_metrics_summary(cls) -> Dict[str, Any]:
        total_events = len(cls._events)
        total_tokens = sum(e.tokens_consumed for e in cls._events)
        avg_latency = round(sum(e.latency_ms for e in cls._events) / max(total_events, 1), 2)
        compliant_count = sum(1 for e in cls._events if e.policy_status == "COMPLIANT")
        blocked_count = sum(1 for e in cls._events if e.policy_status in {"FLAGGED", "BLOCKED"})
        
        return {
            "total_governed_events": total_events,
            "total_tokens_consumed": total_tokens,
            "average_latency_ms": avg_latency,
            "compliance_rate": f"{(compliant_count / max(total_events, 1)) * 100:.1f}%",
            "policy_violations_intercepted": blocked_count,
            "aims_status": "ACTIVE_GOVERNED"
        }
