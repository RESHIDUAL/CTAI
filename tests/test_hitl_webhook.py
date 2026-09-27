import pytest
from app.services.hitl_service import HITLService

def test_hitl_pause_event_creation_and_resolution():
    event = HITLService.trigger_pause_event(
        trace_id="trace_test_hitl_01",
        patient_id="PAT-BORDERLINE-01",
        protocol_id="proto_t2d_ckd_02",
        confidence_score=0.72,
        reason="Confidence score 72% below 90% threshold"
    )
    assert event.event_id.startswith("HITL-")
    assert event.status == "PAUSED_PENDING_HUMAN_REVIEW"
    assert event.confidence_score == 0.72

    events = HITLService.list_paused_events()
    assert any(e["event_id"] == event.event_id for e in events)

    sig = HITLService.create_signature(
        signed_by="Dr. Sarah Coordinator, MD",
        role="Lead Study Coordinator",
        reason="Lab panel verified against primary hospital source."
    )
    resolved = HITLService.resolve_event(event.event_id, sig, "ELIGIBLE")
    assert resolved is not None
    assert resolved["status"] == "RESOLVED_ELIGIBLE"
    assert resolved["override_decision"] == "ELIGIBLE"

def test_hitl_webhook_registration():
    url = "https://example.org/clinical-webhooks/pause-handler"
    HITLService.register_webhook(url)
    assert url in HITLService.get_webhooks()
