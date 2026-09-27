import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from app.models.patient_models import RawSyntheticPatient, LabObservation, DiagnosisRecord, MedicationRecord

class SyntheticFHIRGenerator:
    BORDERLINE_PRESETS = {
        "egfr_upper_borderline_eligible": {
            "name": "Borderline eGFR 59.9 mL/min (Eligible)",
            "age": 58,
            "gender": "male",
            "egfr": 59.9,
            "hba1c": 8.2,
            "washout_days": 45,
            "condition": "Type 2 Diabetes Mellitus"
        },
        "egfr_upper_borderline_ineligible": {
            "name": "Borderline eGFR 60.1 mL/min (Ineligible)",
            "age": 58,
            "gender": "male",
            "egfr": 60.1,
            "hba1c": 8.2,
            "washout_days": 45,
            "condition": "Type 2 Diabetes Mellitus"
        },
        "washout_borderline_fail": {
            "name": "Borderline Washout 29 Days (Ineligible)",
            "age": 62,
            "gender": "female",
            "egfr": 48.0,
            "hba1c": 8.5,
            "washout_days": 29,
            "condition": "Type 2 Diabetes Mellitus"
        },
        "washout_borderline_pass": {
            "name": "Borderline Washout 31 Days (Eligible)",
            "age": 62,
            "gender": "female",
            "egfr": 48.0,
            "hba1c": 8.5,
            "washout_days": 31,
            "condition": "Type 2 Diabetes Mellitus"
        },
        "missing_biomarker_human_review": {
            "name": "Missing HbA1c Observation (Requires Human Review)",
            "age": 54,
            "gender": "female",
            "egfr": 45.0,
            "hba1c": None,
            "washout_days": 60,
            "condition": "Type 2 Diabetes Mellitus"
        }
    }

    @classmethod
    def generate_borderline_fhir_bundle(cls, preset_key: str = "egfr_upper_borderline_eligible") -> Dict[str, Any]:
        preset = cls.BORDERLINE_PRESETS.get(preset_key, cls.BORDERLINE_PRESETS["egfr_upper_borderline_eligible"])
        patient_id = f"PAT-FHIR-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc)
        birth_year = now.year - preset["age"]
        birth_date = f"{birth_year}-05-14"

        entries: List[Dict[str, Any]] = [
            {
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "identifier": [{"system": "http://hospital.example.org/patients", "value": f"MRN-{patient_id}"}],
                    "active": True,
                    "name": [{"use": "official", "family": "BorderlineSubject", "given": ["Synthetic"]}],
                    "gender": preset["gender"],
                    "birthDate": birth_date
                }
            }
        ]

        if preset.get("egfr") is not None:
            entries.append({
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Observation",
                    "id": f"obs-egfr-{uuid.uuid4().hex[:6]}",
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "33914-3", "display": "eGFR"}], "text": "eGFR"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "effectiveDateTime": now.isoformat(),
                    "valueQuantity": {"value": preset["egfr"], "unit": "mL/min/1.73m2", "system": "http://unitsofmeasure.org", "code": "mL/min/1.73m2"}
                }
            })

        if preset.get("hba1c") is not None:
            entries.append({
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Observation",
                    "id": f"obs-hba1c-{uuid.uuid4().hex[:6]}",
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "4548-4", "display": "HbA1c"}], "text": "HbA1c"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "effectiveDateTime": now.isoformat(),
                    "valueQuantity": {"value": preset["hba1c"], "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"}
                }
            })

        if preset.get("condition"):
            entries.append({
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": {
                    "resourceType": "Condition",
                    "id": f"cond-{uuid.uuid4().hex[:6]}",
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
                    "verificationStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]},
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "E11.9", "display": preset["condition"]}], "text": preset["condition"]},
                    "subject": {"reference": f"Patient/{patient_id}"}
                }
            })

        washout_days = preset.get("washout_days", 45)
        last_taken_dt = now - timedelta(days=washout_days)
        entries.append({
            "fullUrl": f"urn:uuid:{uuid.uuid4()}",
            "resource": {
                "resourceType": "MedicationStatement",
                "id": f"med-{uuid.uuid4().hex[:6]}",
                "status": "stopped",
                "medicationCodeableConcept": {
                    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "1991302", "display": "Semaglutide (GLP-1)"}],
                    "text": "Semaglutide (GLP-1)"
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "effectivePeriod": {"end": last_taken_dt.isoformat()},
                "extension": [{"url": "http://hl7.org/fhir/StructureDefinition/washout-days", "valueInteger": washout_days}]
            }
        })

        return {
            "resourceType": "Bundle",
            "id": f"bundle-{uuid.uuid4().hex[:8]}",
            "type": "collection",
            "timestamp": now.isoformat(),
            "preset_key": preset_key,
            "preset_name": preset["name"],
            "entry": entries
        }

    @classmethod
    def convert_bundle_to_raw_patient(cls, bundle: Dict[str, Any]) -> RawSyntheticPatient:
        patient_res = None
        labs: Dict[str, LabObservation] = {}
        diagnoses: List[DiagnosisRecord] = []
        meds: List[MedicationRecord] = []
        now = datetime.now(timezone.utc)

        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            rtype = res.get("resourceType")
            if rtype == "Patient":
                patient_res = res
            elif rtype == "Observation":
                code_obj = res.get("code", {})
                codings = code_obj.get("coding", [])
                loinc = codings[0].get("code", "") if codings else ""
                test_name = code_obj.get("text", "") or (codings[0].get("display", "") if codings else "Lab")
                val_obj = res.get("valueQuantity", {})
                val = val_obj.get("value")
                unit = val_obj.get("unit", "")
                labs[test_name] = LabObservation(
                    loinc=loinc,
                    test_name=test_name,
                    value=float(val) if val is not None else None,
                    unit=unit,
                    study_day_offset=-2
                )
            elif rtype == "Condition":
                code_obj = res.get("code", {})
                codings = code_obj.get("coding", [])
                icd = codings[0].get("code", "R69") if codings else "R69"
                cname = code_obj.get("text", "") or (codings[0].get("display", "") if codings else "Condition")
                diagnoses.append(DiagnosisRecord(
                    icd10=icd,
                    condition_name=cname,
                    is_active=True,
                    study_day_offset=-10
                ))
            elif rtype == "MedicationStatement":
                med_obj = res.get("medicationCodeableConcept", {})
                codings = med_obj.get("coding", [])
                rx = codings[0].get("code", "") if codings else ""
                drug_name = med_obj.get("text", "") or (codings[0].get("display", "") if codings else "Medication")
                status = res.get("status", "stopped")
                preset_key = bundle.get("preset_key", "")
                
                day_offset = -45
                for ext in res.get("extension", []):
                    if "washout-days" in ext.get("url", ""):
                        day_offset = -abs(int(ext.get("valueInteger", 45)))
                        break
                
                meds.append(MedicationRecord(
                    rxnorm=rx,
                    drug_name=drug_name,
                    is_active=(status == "active"),
                    last_taken_day_offset=day_offset
                ))

        pid = patient_res.get("id", f"PAT-{uuid.uuid4().hex[:6]}") if patient_res else f"PAT-{uuid.uuid4().hex[:6]}"
        bdate = patient_res.get("birthDate", "1970-01-01") if patient_res else "1970-01-01"
        try:
            byear = int(bdate.split("-")[0])
            age = now.year - byear
        except Exception:
            age = 55
        gender = "M" if (patient_res and patient_res.get("gender") == "male") else "F"

        return RawSyntheticPatient(
            id=pid,
            raw_name="Synthetic Borderline Subject",
            raw_mrn=f"MRN-{pid}",
            raw_dob=bdate,
            raw_phone="555-019-9481",
            raw_address="742 Evergreen Terrace, Springfield, OR",
            raw_doctor="Dr. Clinical Specialist, MD",
            age_years=age,
            gender=gender,
            labs=labs,
            diagnoses=diagnoses,
            medications=meds,
            clinical_notes=["Synthetic borderline history generated for sensitivity and threshold verification."]
        )
