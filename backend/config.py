import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Governed Clinical Trial Screening & Traceability Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Lyzr Ecosystem Configuration
    LYZR_API_KEY: str = os.getenv("LYZR_API_KEY", "")
    LYZR_BASE_URL: str = os.getenv("LYZR_INFERENCE_ENDPOINT", os.getenv("LYZR_BASE_URL", "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"))
    LYZR_ENVIRONMENT_ID: str = os.getenv("LYZR_ENVIRONMENT_ID", "env_clinical_trial_01")
    LYZR_AGENT_ID: str = os.getenv("LYZR_AGENT_ID", "")
    LYZR_USER_ID: str = os.getenv("LYZR_USER_ID", "")
    LYZR_SESSION_ID: str = os.getenv("LYZR_SESSION_ID", "")
    
    # Regulatory Traceability Settings
    PART_11_ORGANIZATION: str = "BioTrial Clinical Research Network"
    PART_11_SYSTEM_ID: str = "Lyzr-CTScreen-v1.0"
    AUDIT_RETENTION_YEARS: int = 25
    
    # Compliance & Safety
    ALLOW_DEMO_FALLBACK: bool = True
    STRICT_VALIDATION_GATE: bool = True

settings = Settings()
