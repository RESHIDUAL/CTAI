from typing import Dict, Any, List
from app.core.lyzr_client import LyzrEcosystemClient

class ProtocolCriteriaAgent:
    """
    Agent 1: Protocol Criteria Agent
    Specialized agent that extracts inclusion and exclusion rules from protocol text
    into candidate structured criteria JSON.
    NOTE: LLM only extracts and structures; it NEVER decides patient eligibility.
    """

    def __init__(self, client: LyzrEcosystemClient):
        self.client = client

    def extract_criteria(self, protocol_text: str, trace_id: str) -> Dict[str, Any]:
        return self.client.call_protocol_criteria_agent(protocol_text, trace_id)
