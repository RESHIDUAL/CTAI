from enum import Enum
from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field

class CriterionType(str, Enum):
    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"

class CriterionCategory(str, Enum):
    DEMOGRAPHIC = "DEMOGRAPHIC"
    BIOMARKER = "BIOMARKER"
    DIAGNOSIS = "DIAGNOSIS"
    MEDICATION_WASHOUT = "MEDICATION_WASHOUT"
    CLINICAL_STATUS = "CLINICAL_STATUS"

class OperatorType(str, Enum):
    GREATER_THAN = ">"
    GREATER_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_OR_EQUAL = "<="
    EQUAL = "=="
    BETWEEN = "BETWEEN"
    EXCLUDES = "EXCLUDES"
    WASHOUT_DAYS = "WASHOUT_DAYS"

class ProtocolCitation(BaseModel):
    page: int
    section: str
    paragraph: Optional[int] = 1
    raw_clause: str

class CriterionDefinition(BaseModel):
    criterion_id: str
    type: CriterionType
    category: CriterionCategory
    concept_name: str
    concept_code: Optional[str] = None  # e.g., LOINC: 33914-3 or ICD-10: E11.9
    operator: OperatorType
    threshold: Optional[Union[float, int, List[float], str]] = None
    unit: Optional[str] = None
    washout_days: Optional[int] = None
    protocol_citation: ProtocolCitation
    description: str

class ProtocolSchema(BaseModel):
    id: str
    nct_id: str
    title: str
    phase: str
    indication: str
    investigational_drug: str
    version: str = "1.0"
    m11_aligned: bool = True
    criteria: List[CriterionDefinition] = []

class ValidationGateResult(BaseModel):
    is_valid: bool
    validated_criteria: List[CriterionDefinition] = []
    rejected_criteria: List[dict] = []
    validation_errors: List[str] = []
