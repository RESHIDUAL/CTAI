from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class LabObservation(BaseModel):
    test_name: str
    loinc: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    study_day_offset: Optional[int] = None  # e.g., -4 means 4 days before baseline
    source_record: Optional[str] = "Lab Panel"

class DiagnosisRecord(BaseModel):
    icd10: str
    condition_name: str
    is_active: bool = True
    study_day_offset: Optional[int] = None

class MedicationRecord(BaseModel):
    drug_name: str
    rxnorm: Optional[str] = None
    is_active: bool = False
    last_taken_day_offset: Optional[int] = None  # Days prior to screening (e.g. -12 means taken 12 days ago)
    washout_status: Optional[str] = None

class RawSyntheticPatient(BaseModel):
    id: str
    raw_name: str
    raw_mrn: str
    raw_dob: str
    raw_phone: str
    raw_address: str
    raw_doctor: str
    age_years: int
    gender: str
    labs: Dict[str, LabObservation] = {}
    diagnoses: List[DiagnosisRecord] = []
    medications: List[MedicationRecord] = []
    clinical_notes: List[str] = []

class RedactionItem(BaseModel):
    category: str  # NAME, MRN, PHONE, DOB, ADDRESS, DOCTOR
    original_snippet: str
    replacement: str

class RedactionCertificate(BaseModel):
    pseudonym_id: str
    scrubbed_at: str
    identifiers_detected: int
    redactions: List[RedactionItem] = []
    dates_shifted: int
    zero_leak_verified: bool = True

class DeidentifiedPatient(BaseModel):
    pseudonym_id: str
    age_years: int
    gender: str
    labs: Dict[str, LabObservation] = {}
    diagnoses: List[DiagnosisRecord] = []
    medications: List[MedicationRecord] = []
    clinical_notes: List[str] = []
    redaction_cert: Optional[RedactionCertificate] = None
