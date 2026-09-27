import os
from typing import Dict, Any

class LyzrAgentConfig:
    ENVIRONMENT_ID = os.getenv("LYZR_ENVIRONMENT_ID", "env_clinical_trial_01")
    AGENT_API_BASE_URL = os.getenv("LYZR_BASE_URL", "https://agent-prod.studio.lyzr.ai/v3/inference/chat/")
    API_KEY = os.getenv("LYZR_API_KEY", "")
    USER_ID = os.getenv("LYZR_USER_ID", "coordinator@clinicaltrial.org")
    
    PROTOCOL_AGENT_ID = os.getenv("LYZR_PROTOCOL_AGENT_ID", os.getenv("LYZR_AGENT_ID", "6aafa27f23bdcdc9f029eeba"))
    MEDICAL_SAFETY_AGENT_ID = os.getenv("LYZR_MEDICAL_SAFETY_AGENT_ID", "agent_medical_safety_01")
    REGULATORY_AUDIT_AGENT_ID = os.getenv("LYZR_AUDIT_AGENT_ID", "agent_regulatory_audit_01")

    PROTOCOL_CRITERIA_SYSTEM_PROMPT = (
        "You are the Lyzr Protocol Criteria Agent. Your role is to ingest clinical trial "
        "protocol clauses and extract inclusion and exclusion rules into strict JSON schemas. "
        "Do not evaluate patient data. Do not hallucinate biomarker thresholds or operators. "
        "Extract concept names, operators (GREATER_THAN, LESS_THAN, BETWEEN, EQUAL, WASHOUT_DAYS), "
        "thresholds, units, and protocol citations."
    )

    MEDICAL_SAFETY_SYSTEM_PROMPT = (
        "You are the Lyzr Medical Safety Agent. Your role is to validate candidate patient "
        "biomarkers, diagnoses, and medication histories against clinical ontologies (SNOMED-CT, "
        "ICD-10, LOINC). Verify standard unit normalizations and highlight discrepancies. "
        "Patient eligibility must strictly follow deterministic mathematical evaluation."
    )

    REGULATORY_AUDIT_SYSTEM_PROMPT = (
        "You are the Lyzr Regulatory Audit Agent. Your role is to format immutable clinical "
        "screening decision paths into FDA 21 CFR Part 11 compliant audit dossiers. Ensure "
        "citations are cross-referenced to protocol page numbers, calculate cryptographic SHA-256 "
        "integrity seals, and record provenance events for Lyzr AIMS governance."
    )

    CRITERIA_JSON_SCHEMA: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "criterion_id": {"type": "string"},
            "type": {"type": "string", "enum": ["INCLUSION", "EXCLUSION"]},
            "category": {"type": "string", "enum": ["DEMOGRAPHIC", "BIOMARKER", "DIAGNOSIS", "MEDICATION_WASHOUT"]},
            "concept_name": {"type": "string"},
            "concept_code": {"type": "string"},
            "operator": {"type": "string", "enum": [">", ">=", "<", "<=", "==", "BETWEEN", "WASHOUT_DAYS"]},
            "threshold": {"type": ["number", "array", "string"]},
            "unit": {"type": "string"},
            "washout_days": {"type": "integer"},
            "protocol_citation": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "section": {"type": "string"},
                    "raw_clause": {"type": "string"}
                },
                "required": ["page", "section", "raw_clause"]
            }
        },
        "required": ["criterion_id", "type", "category", "concept_name", "operator", "threshold", "protocol_citation"]
    }
