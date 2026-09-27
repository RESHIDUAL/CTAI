import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class CoordinatorSignature(BaseModel):
    signed_by: str
    signed_at: str
    role: str = "Clinical Research Coordinator"
    action: str = "HUMAN_REVIEW_OVERRIDE"
    reason: str

class HITLWebhookEvent(BaseModel):
    event_id: str
    trace_id: str
    patient_id: str
    protocol_id: str
    confidence_score: float
    status: str = "PAUSED_PENDING_HUMAN_REVIEW"
    created_at: str
    reason: str
    details: Dict[str, Any] = {}

class HITLService:
    _paused_events: Dict[str, HITLWebhookEvent] = {}
    _webhook_urls: List[str] = []

    @classmethod
    def register_webhook(cls, url: str) -> None:
        if url and url not in cls._webhook_urls:
            cls._webhook_urls.append(url)

    @classmethod
    def get_webhooks(cls) -> List[str]:
        return list(cls._webhook_urls)

    @classmethod
    def trigger_pause_event(
        cls,
        trace_id: str,
        patient_id: str,
        protocol_id: str,
        confidence_score: float,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ) -> HITLWebhookEvent:
        event = HITLWebhookEvent(
            event_id=f"HITL-{trace_id[-8:].upper()}",
            trace_id=trace_id,
            patient_id=patient_id,
            protocol_id=protocol_id,
            confidence_score=confidence_score,
            status="PAUSED_PENDING_HUMAN_REVIEW",
            created_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            details=details or {}
        )
        cls._paused_events[event.event_id] = event

        for url in cls._webhook_urls:
            try:
                requests.post(url, json=event.model_dump(), timeout=3)
            except Exception:
                pass

        return event

    @classmethod
    def list_paused_events(cls) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in cls._paused_events.values()]

    @classmethod
    def resolve_event(cls, event_id: str, signature: CoordinatorSignature, override_decision: str) -> Optional[Dict[str, Any]]:
        if event_id in cls._paused_events:
            ev = cls._paused_events[event_id]
            ev.status = f"RESOLVED_{override_decision}"
            return {
                "event_id": event_id,
                "status": ev.status,
                "signature": signature.model_dump(),
                "override_decision": override_decision,
                "resolved_at": datetime.now(timezone.utc).isoformat()
            }
        return None

    @staticmethod
    def create_signature(signed_by: str, role: str, reason: str, action: str = "HUMAN_REVIEW_OVERRIDE") -> CoordinatorSignature:
        return CoordinatorSignature(
            signed_by=signed_by,
            signed_at=datetime.now(timezone.utc).isoformat(),
            role=role or "Clinical Research Coordinator",
            action=action,
            reason=reason or "Clinical evidence reviewed and verified"
        )
