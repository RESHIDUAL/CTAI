from typing import Dict, Any
from app.core.lyzr_client import LyzrEcosystemClient

class RegulatoryAuditAgent:
    """
    Agent 3: Regulatory Audit Agent
    Specialized agent that synthesizes deterministic screening provenance,
    EHR evidence quotations, and protocol citations into a Part 11-oriented audit dossier.
    """

    def __init__(self, client: LyzrEcosystemClient):
        self.client = client

    def synthesize_dossier(self, decision_summary: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        return self.client.call_regulatory_audit_agent(decision_summary, trace_id)
