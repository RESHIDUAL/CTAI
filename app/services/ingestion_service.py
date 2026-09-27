import re
import json
import uuid
import io
import csv
from typing import Dict, Any, List, Optional
from app.models.protocol_models import ProtocolSchema, CriterionDefinition, CriterionType, CriterionCategory, OperatorType, ProtocolCitation
from app.models.patient_models import RawSyntheticPatient, LabObservation, DiagnosisRecord, MedicationRecord
from app.core.phi_scrubber import SyntheticPhiScrubber

class IngestionService:
    @staticmethod
    def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
        fn = filename.lower()
        
        # 1. PDF Documents
        if fn.endswith(".pdf"):
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                pages_text = [page.get_text() for page in doc]
                combined = "\n".join(pages_text).strip()
                if combined:
                    return combined
            except Exception:
                pass

            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                pages_text = [page.extract_text() or "" for page in reader.pages]
                combined = "\n".join(pages_text).strip()
                if combined:
                    return combined
            except Exception:
                pass

        # 2. Microsoft Word Documents (.docx)
        if fn.endswith(".docx") or fn.endswith(".doc"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                lines: List[str] = []
                for p in doc.paragraphs:
                    if p.text.strip():
                        lines.append(p.text.strip())
                for table in doc.tables:
                    for row in table.rows:
                        row_vals = [c.text.strip() for c in row.cells if c.text.strip()]
                        if row_vals:
                            lines.append(" | ".join(row_vals))
                combined = "\n".join(lines).strip()
                if combined:
                    return combined
            except Exception:
                pass

        # 3. Excel and Tabular Documents (.xlsx, .xls, .csv, .tsv)
        if fn.endswith((".xlsx", ".xls", ".csv", ".tsv")):
            # CSV or TSV
            if fn.endswith((".csv", ".tsv")):
                try:
                    delim = "\t" if fn.endswith(".tsv") else ","
                    decoded = file_bytes.decode("utf-8", errors="ignore")
                    reader = csv.reader(io.StringIO(decoded), delimiter=delim)
                    lines = [" | ".join(r) for r in reader if any(c.strip() for c in r)]
                    return "\n".join(lines)
                except Exception:
                    pass

            # XLSX or XLS
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
                lines = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    for row in ws.iter_rows(values_only=True):
                        row_str = [str(c).strip() for c in row if c is not None and str(c).strip()]
                        if row_str:
                            lines.append(" | ".join(row_str))
                combined = "\n".join(lines).strip()
                if combined:
                    return combined
            except Exception:
                pass

        # 4. Images (.png, .jpg, .jpeg, .tiff, .bmp, .webp) via RapidOCR
        if fn.endswith((".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")):
            try:
                from PIL import Image
                import numpy as np
                from rapidocr_onnxruntime import RapidOCR
                img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                img_np = np.array(img)
                ocr = RapidOCR()
                result, _ = ocr(img_np)
                if result:
                    lines = [line[1] for line in result if line and len(line) > 1]
                    combined = "\n".join(lines).strip()
                    if combined:
                        return combined
            except Exception:
                pass

        # 5. Plaintext, JSON, Markdown, XML fallback
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raw_str = file_bytes.decode("latin1", errors="ignore")
            clean_ascii = "".join([c if ord(c) < 128 and (c.isalnum() or c in " \n\r\t.,;:()[]{}-_%/|=>") else " " for c in raw_str])
            lines = [line.strip() for line in clean_ascii.splitlines() if len(line.strip()) > 3]
            return "\n".join(lines[:300])

    @classmethod
    def ingest_protocol_document(cls, text: str, title: Optional[str] = None, nct_id: Optional[str] = None) -> ProtocolSchema:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "criteria" in parsed:
                return ProtocolSchema(**parsed)
        except Exception:
            pass

        proto_id = f"proto_custom_{uuid.uuid4().hex[:6]}"
        
        # Trial ID detection
        trial_match = re.search(r"(?:Trial\s*ID|Protocol\s*ID)[:\s]+([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        detected_nct = nct_id or (trial_match.group(1).strip() if trial_match else None)
        if not detected_nct:
            nct_match = re.search(r"NCT\d{8}", text, re.IGNORECASE)
            detected_nct = nct_match.group(0).upper() if nct_match else f"NCT{uuid.uuid4().int % 90000000 + 10000000}"

        # Study Title detection
        title_match = re.search(r"Study Title[:\s]+([^\r\n]+)", text, re.IGNORECASE)
        doc_title = title or (title_match.group(1).strip() if title_match else "Ingested Clinical Protocol")
        criteria: List[CriterionDefinition] = []

        # 1. Age Rule
        age_match = re.search(r"Age\s*(?:must be\s*)?(?:greater than or equal to|>=)\s*(\d+)", text, re.IGNORECASE)
        if age_match:
            val = int(age_match.group(1))
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_AGE_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.DEMOGRAPHIC,
                concept_name="Age",
                operator=OperatorType.GREATER_OR_EQUAL,
                threshold=val,
                unit="years",
                protocol_citation=ProtocolCitation(page=1, section="Inclusion Criteria", raw_clause=age_match.group(0)),
                description=f"Age must be greater than or equal to {val} years."
            ))

        # 2. eGFR Range (Inclusion)
        egfr_range_match = re.search(r"eGFR\s*(?:must be\s*)?(?:between|from)?\s*(\d+(?:\.\d+)?)\s*(?:to|-|and)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if egfr_range_match:
            low, high = float(egfr_range_match.group(1)), float(egfr_range_match.group(2))
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_EGFR_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.BIOMARKER,
                concept_name="eGFR",
                concept_code="33914-3",
                operator=OperatorType.BETWEEN,
                threshold=[low, high],
                unit="mL/min/1.73m2",
                protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=egfr_range_match.group(0)),
                description=f"Estimated GFR must be between {low} and {high} mL/min/1.73m2."
            ))
        else:
            # eGFR Greater Than (Inclusion)
            egfr_gt_match = re.search(r"eGFR\s*(?:must be\s*)?(?:greater than or equal to|>=)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
            if egfr_gt_match:
                val = float(egfr_gt_match.group(1))
                criteria.append(CriterionDefinition(
                    criterion_id=f"INC_EGFR_{uuid.uuid4().hex[:4]}",
                    type=CriterionType.INCLUSION,
                    category=CriterionCategory.BIOMARKER,
                    concept_name="eGFR",
                    concept_code="33914-3",
                    operator=OperatorType.GREATER_OR_EQUAL,
                    threshold=val,
                    unit="mL/min/1.73m2",
                    protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=egfr_gt_match.group(0)),
                    description=f"eGFR must be >= {val} mL/min/1.73m2."
                ))
            else:
                egfr_gt_strict = re.search(r"eGFR\s*(?:must be\s*)?(?:greater than|>)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
                if egfr_gt_strict:
                    val = float(egfr_gt_strict.group(1))
                    criteria.append(CriterionDefinition(
                        criterion_id=f"INC_EGFR_{uuid.uuid4().hex[:4]}",
                        type=CriterionType.INCLUSION,
                        category=CriterionCategory.BIOMARKER,
                        concept_name="eGFR",
                        concept_code="33914-3",
                        operator=OperatorType.GREATER_THAN,
                        threshold=val,
                        unit="mL/min/1.73m2",
                        protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=egfr_gt_strict.group(0)),
                        description=f"eGFR must be greater than {val} mL/min/1.73m2."
                    ))

        # 3. eGFR Less Than (Severe Impairment Exclusion)
        egfr_lt_match = re.search(r"eGFR\s*(?:less than or equal to|<=|<|less than)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if egfr_lt_match:
            val = float(egfr_lt_match.group(1))
            criteria.append(CriterionDefinition(
                criterion_id=f"EXC_EGFR_{uuid.uuid4().hex[:4]}",
                type=CriterionType.EXCLUSION,
                category=CriterionCategory.BIOMARKER,
                concept_name="eGFR",
                concept_code="33914-3",
                operator=OperatorType.LESS_THAN,
                threshold=val,
                unit="mL/min/1.73m2",
                protocol_citation=ProtocolCitation(page=1, section="Exclusion Criteria", raw_clause=egfr_lt_match.group(0)),
                description=f"eGFR less than {val} mL/min/1.73m2 excludes the patient."
            ))

        # 4. HbA1c Range (Inclusion)
        hba1c_match = re.search(r"HbA1c\s*(?:must be\s*)?(?:between|from)?\s*(\d+(?:\.\d+)?)\s*%?\s*(?:to|-|and)\s*(\d+(?:\.\d+)?)%?", text, re.IGNORECASE)
        if hba1c_match:
            low, high = float(hba1c_match.group(1)), float(hba1c_match.group(2))
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_HBA1C_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.BIOMARKER,
                concept_name="HbA1c",
                concept_code="4548-4",
                operator=OperatorType.BETWEEN,
                threshold=[low, high],
                unit="%",
                protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=hba1c_match.group(0)),
                description=f"HbA1c between {low}% and {high}%."
            ))

        # 5. ANC (Absolute Neutrophil Count)
        anc_match = re.search(r"ANC\s*(?:>=|greater than or equal to|>)\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if anc_match:
            val = float(anc_match.group(1))
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_ANC_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.BIOMARKER,
                concept_name="ANC",
                concept_code="26499-4",
                operator=OperatorType.GREATER_OR_EQUAL,
                threshold=val,
                unit="/uL",
                protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=anc_match.group(0)),
                description=f"Absolute Neutrophil Count >= {val} /uL."
            ))

        # 6. Platelets
        plt_match = re.search(r"(?:platelets?|plt)\s*(?:>=|greater than or equal to|>)\s*(\d+)", text, re.IGNORECASE)
        if plt_match:
            val = float(plt_match.group(1))
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_PLT_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.BIOMARKER,
                concept_name="Platelets",
                concept_code="777-3",
                operator=OperatorType.GREATER_OR_EQUAL,
                threshold=val,
                unit="/uL",
                protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause=plt_match.group(0)),
                description=f"Platelet count >= {val} /uL."
            ))

        # 7. Diagnoses (Inclusion)
        if "type 2 diabetes" in text.lower() or "t2d" in text.lower() or "diabetes mellitus" in text.lower():
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_DIAG_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.DIAGNOSIS,
                concept_name="Type 2 Diabetes Mellitus",
                concept_code="E11.9",
                operator=OperatorType.EQUAL,
                protocol_citation=ProtocolCitation(page=1, section="Inclusion Criteria", raw_clause="Patient must have documented Type 2 diabetes mellitus."),
                description="Documented Type 2 diabetes mellitus required."
            ))
        elif "lung cancer" in text.lower() or "nsclc" in text.lower():
            criteria.append(CriterionDefinition(
                criterion_id=f"INC_DIAG_{uuid.uuid4().hex[:4]}",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.DIAGNOSIS,
                concept_name="Non-Small Cell Lung Cancer",
                concept_code="C34.90",
                operator=OperatorType.EQUAL,
                protocol_citation=ProtocolCitation(page=1, section="Inclusion Criteria", raw_clause="Patient must have non-small cell lung cancer."),
                description="Documented non-small cell lung cancer required."
            ))

        # 8. Malignancy / Cancer (Exclusion)
        if "active malignancy" in text.lower() or "active cancer" in text.lower():
            criteria.append(CriterionDefinition(
                criterion_id=f"EXC_MAL_{uuid.uuid4().hex[:4]}",
                type=CriterionType.EXCLUSION,
                category=CriterionCategory.DIAGNOSIS,
                concept_name="Active Malignancy",
                concept_code="C80.1",
                operator=OperatorType.EXCLUDES,
                protocol_citation=ProtocolCitation(page=1, section="Exclusion Criteria", raw_clause="Any documented active cancer excludes the patient."),
                description="Any documented active cancer excludes the patient."
            ))

        # 9. Pregnancy (Exclusion)
        if "pregnancy" in text.lower() or "pregnant" in text.lower():
            criteria.append(CriterionDefinition(
                criterion_id=f"EXC_PREG_{uuid.uuid4().hex[:4]}",
                type=CriterionType.EXCLUSION,
                category=CriterionCategory.CLINICAL_STATUS,
                concept_name="Pregnancy",
                operator=OperatorType.EXCLUDES,
                protocol_citation=ProtocolCitation(page=1, section="Exclusion Criteria", raw_clause="Current pregnancy excludes the patient."),
                description="Current pregnancy excludes the patient."
            ))

        # 10. Medication Washout Exclusion
        wash_match = re.search(r"(?:washout|discontinued?|prior treatment with|use of)\s*([a-zA-Z0-9\-\s]+?)\s*(?:within)?\s*(?:the previous\s*)?(\d+)\s*days", text, re.IGNORECASE)
        if wash_match:
            drug = wash_match.group(1).strip()
            drug = re.sub(r"^(?:Use of\s+|prior\s+|treatment with\s+)", "", drug, flags=re.IGNORECASE).strip()
            days = int(wash_match.group(2))
            criteria.append(CriterionDefinition(
                criterion_id=f"EXC_WASH_{uuid.uuid4().hex[:4]}",
                type=CriterionType.EXCLUSION,
                category=CriterionCategory.MEDICATION_WASHOUT,
                concept_name=drug,
                operator=OperatorType.GREATER_OR_EQUAL,
                threshold=days,
                washout_days=days,
                unit="days",
                protocol_citation=ProtocolCitation(page=1, section="Exclusion", raw_clause=wash_match.group(0)),
                description=f"Must have discontinued {drug} at least {days} days prior to screening."
            ))

        # Default Age Criterion if not present
        if not any(c.category == CriterionCategory.DEMOGRAPHIC for c in criteria):
            criteria.append(CriterionDefinition(
                criterion_id="INC_AGE_DEFAULT",
                type=CriterionType.INCLUSION,
                category=CriterionCategory.DEMOGRAPHIC,
                concept_name="Age",
                operator=OperatorType.GREATER_OR_EQUAL,
                threshold=18,
                unit="years",
                protocol_citation=ProtocolCitation(page=1, section="Eligibility", raw_clause="Age >= 18"),
                description="Subject must be 18 years of age or older."
            ))

        # Indication detection
        indication = "Renal Impairment in Type 2 Diabetes"
        if "lung cancer" in text.lower() or "nsclc" in text.lower():
            indication = "Advanced Non-Small Cell Lung Cancer"
        elif "breast cancer" in text.lower():
            indication = "Metastatic Breast Cancer"

        return ProtocolSchema(
            id=proto_id,
            nct_id=detected_nct,
            title=doc_title,
            phase="Phase 2/3",
            indication=indication,
            investigational_drug="Investigational Candidate / Placebo",
            version="1.0",
            m11_aligned=True,
            criteria=criteria
        )

    @classmethod
    def ingest_patient_record(cls, text: str, name: Optional[str] = "Ingested Patient") -> RawSyntheticPatient:
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and "resourceType" in parsed and parsed["resourceType"] == "Bundle":
                from app.services.fhir_generator import SyntheticFHIRGenerator
                return SyntheticFHIRGenerator.convert_bundle_to_raw_patient(parsed)
            if isinstance(parsed, dict) and "raw_name" in parsed:
                return RawSyntheticPatient(**parsed)
        except Exception:
            pass

        pat_id = f"PAT-INGEST-{uuid.uuid4().hex[:6].upper()}"
        
        # Check for explicit patient ID
        pat_id_match = re.search(r"(?:Synthetic Patient ID|Patient identifier)[:\s]+([A-Za-z0-9\-]+)", text, re.IGNORECASE)
        if pat_id_match:
            pat_id = pat_id_match.group(1).strip()

        # Check for screening date
        scr_date = None
        scr_match = re.search(r"Screening date[:\s]+(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
        if scr_match:
            try:
                from datetime import datetime
                scr_date = datetime.strptime(scr_match.group(1), "%Y-%m-%d").date()
            except Exception:
                pass

        labs: Dict[str, LabObservation] = {}
        diagnoses: List[DiagnosisRecord] = []
        meds: List[MedicationRecord] = []

        # eGFR
        egfr_match = re.search(r"eGFR[:\s=|,]+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if not egfr_match:
            egfr_match = re.search(r"eGFR\s*\n\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if egfr_match:
            labs["eGFR"] = LabObservation(
                loinc="33914-3",
                test_name="eGFR",
                value=float(egfr_match.group(1)),
                unit="mL/min/1.73m2",
                study_day_offset=-2
            )

        # HbA1c
        hba1c_match = re.search(r"HbA1c[:\s=|,]+(\d+(?:\.\d+)?)%?", text, re.IGNORECASE)
        if not hba1c_match:
            hba1c_match = re.search(r"HbA1c\s*\n\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if hba1c_match:
            labs["HbA1c"] = LabObservation(
                loinc="4548-4",
                test_name="HbA1c",
                value=float(hba1c_match.group(1)),
                unit="%",
                study_day_offset=-2
            )

        # ANC
        anc_match = re.search(r"ANC[:\s=|,]+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if not anc_match:
            anc_match = re.search(r"ANC\s*\n\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if anc_match:
            labs["ANC"] = LabObservation(
                loinc="26499-4",
                test_name="ANC",
                value=float(anc_match.group(1)),
                unit="/uL",
                study_day_offset=-2
            )

        # Platelets
        plt_match = re.search(r"(?:platelets?|plt)[:\s=|,]+(\d+)", text, re.IGNORECASE)
        if not plt_match:
            plt_match = re.search(r"(?:platelets?|plt)\s*\n\s*(\d+)", text, re.IGNORECASE)
        if plt_match:
            labs["Platelets"] = LabObservation(
                loinc="777-3",
                test_name="Platelets",
                value=float(plt_match.group(1)),
                unit="/uL",
                study_day_offset=-2
            )

        # Creatinine
        cr_match = re.search(r"(?:serum creatinine|creatinine|cr)[:\s=|,]+(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if not cr_match:
            cr_match = re.search(r"(?:serum creatinine|creatinine|cr)\s*\n\s*(\d+(?:\.\d+)?)", text, re.IGNORECASE)
        if cr_match:
            labs["Creatinine"] = LabObservation(
                loinc="2160-0",
                test_name="Creatinine",
                value=float(cr_match.group(1)),
                unit="mg/dL",
                study_day_offset=-2
            )

        # Diagnoses
        if "type 2 diabetes" in text.lower() or "t2d" in text.lower() or "diabetes mellitus" in text.lower():
            diagnoses.append(DiagnosisRecord(
                icd10="E11.9",
                condition_name="Type 2 Diabetes Mellitus",
                is_active=True,
                study_day_offset=-30
            ))

        if "lung cancer" in text.lower() or "nsclc" in text.lower():
            diagnoses.append(DiagnosisRecord(
                icd10="C34.90",
                condition_name="Non-Small Cell Lung Cancer",
                is_active=True,
                study_day_offset=-45
            ))

        if "ckd" in text.lower() or "chronic kidney disease" in text.lower():
            diagnoses.append(DiagnosisRecord(
                icd10="N18.3",
                condition_name="Chronic Kidney Disease Stage 3",
                is_active=True,
                study_day_offset=-60
            ))

        # Check for active malignancy
        if "active malignancy" in text.lower():
            if "no active malignancy" not in text.lower() and "active malignancy: none" not in text.lower():
                diagnoses.append(DiagnosisRecord(
                    icd10="C80.1",
                    condition_name="Active Malignancy",
                    is_active=True,
                    study_day_offset=-20
                ))

        # Medications Extraction from Table Lines
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if line_lower in ("current", "active"):
                prev_line = lines[i-1] if i > 0 else ""
                if len(prev_line) > 2 and not prev_line.lower().startswith(("field", "condition", "test", "status", "evidence")):
                    meds.append(MedicationRecord(
                        drug_name=prev_line,
                        is_active=True
                    ))
            elif line_lower in ("discontinued", "prior"):
                prev_line = lines[i-1] if i > 0 else ""
                next_line = lines[i+1] if i + 1 < len(lines) else ""
                offset = -35
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", next_line)
                if date_match and scr_date:
                    from datetime import datetime
                    d = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
                    offset = -abs((scr_date - d).days)
                if len(prev_line) > 2 and not prev_line.lower().startswith(("field", "condition", "test", "status", "evidence")):
                    meds.append(MedicationRecord(
                        drug_name=prev_line,
                        is_active=False,
                        last_taken_day_offset=offset
                    ))

        # Medications Extraction from Clinical Notes Phrases
        if "semaglutide" in text.lower() or "glp-1" in text.lower() or "ozempic" in text.lower():
            if not any("semaglutide" in m.drug_name.lower() or "glp-1" in m.drug_name.lower() for m in meds):
                meds.append(MedicationRecord(
                    rxnorm="1991302",
                    drug_name="Semaglutide (GLP-1)",
                    is_active=False,
                    last_taken_day_offset=-35
                ))

        if "pembrolizumab" in text.lower() or "keytruda" in text.lower():
            if not any("pembrolizumab" in m.drug_name.lower() for m in meds):
                meds.append(MedicationRecord(
                    rxnorm="1547545",
                    drug_name="Pembrolizumab",
                    is_active=False,
                    last_taken_day_offset=-40
                ))

        # Check for textual "last documented as used on YYYY-MM-DD"
        used_match = re.search(r"([A-Za-z0-9\s\-]+?)\s+was last (?:documented as )?used on (\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
        if used_match:
            d_name = used_match.group(1).strip()
            if not any(d_name.lower() in m.drug_name.lower() for m in meds):
                offset = -35
                if scr_date:
                    from datetime import datetime
                    d = datetime.strptime(used_match.group(2), "%Y-%m-%d").date()
                    offset = -abs((scr_date - d).days)
                meds.append(MedicationRecord(
                    drug_name=d_name,
                    is_active=False,
                    last_taken_day_offset=offset
                ))

        # Age
        age_match = re.search(r"(\d{1,3})\s*(?:yo|y/o|years old|years of age|year old|years)", text, re.IGNORECASE)
        if not age_match:
            age_match = re.search(r"(?:age|yo|years old)[:\s=]+(\d{2})", text, re.IGNORECASE)
        age = int(age_match.group(1)) if age_match else 55

        # Gender
        gender = "M"
        if re.search(r"\b(?:female|woman|f)\b", text, re.IGNORECASE):
            gender = "F"

        return RawSyntheticPatient(
            id=pat_id,
            raw_name=name or "Ingested Clinical Patient",
            raw_mrn=f"MRN-{pat_id}",
            raw_dob="1970-01-15",
            raw_phone="555-010-4491",
            raw_address="100 Clinical Way, Boston, MA",
            raw_doctor="Dr. Clinical Specialist, MD",
            age_years=age,
            gender=gender,
            labs=labs,
            diagnoses=diagnoses,
            medications=meds,
            clinical_notes=[text[:4000]]
        )
