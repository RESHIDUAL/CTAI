from typing import List, Tuple
from app.models.protocol_models import (
    CriterionDefinition,
    CriterionType,
    CriterionCategory,
    OperatorType
)
from app.models.patient_models import DeidentifiedPatient
from app.models.dossier_models import (
    CriterionEvaluation,
    EvaluationStatus,
    EligibilityDecision,
    WhyNotEligibleSummary
)
from app.core.ontologies import resolve_biomarker

class DeterministicScreeningEngine:
    """
    Pure Deterministic Medical Screening Engine.
    Evaluates validated criteria mathematically and temporally.
    LLM NEVER decides eligibility or assigns arbitrary confidence numbers.
    """

    @classmethod
    def evaluate_criterion(cls, crit: CriterionDefinition, patient: DeidentifiedPatient) -> CriterionEvaluation:
        cid = crit.criterion_id
        ctype = crit.type.value
        op = crit.operator.value
        cat = crit.category.value
        cit_str = f"Page {crit.protocol_citation.page}, Section {crit.protocol_citation.section}"

        # -------------------------------------------------------------
        # 1. DEMOGRAPHIC EVALUATION (e.g. Age >= 18)
        # -------------------------------------------------------------
        if cat == CriterionCategory.DEMOGRAPHIC.value:
            if "age" in crit.concept_name.lower():
                patient_val = float(patient.age_years)
                thresh = float(crit.threshold)
                passed = cls._compare_numeric(patient_val, op, thresh)
                
                status = EvaluationStatus.PASS if (passed if ctype == "INCLUSION" else not passed) else EvaluationStatus.FAIL
                calc = f"{patient_val} {op} {thresh} -> {passed}"
                fail_reason = None if status == EvaluationStatus.PASS else f"Patient age ({patient_val}) violates requirement ({crit.description})."
                
                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name="Age",
                    rule_summary=f"Age {op} {thresh} years",
                    patient_value_str=f"{patient_val} years",
                    status=status,
                    calculation_trace=calc,
                    evidence_source="Patient Demographic Record",
                    protocol_citation=cit_str,
                    failure_reason=fail_reason
                )

        # -------------------------------------------------------------
        # 2. BIOMARKER EVALUATION (e.g. eGFR, HbA1c, ANC, Platelets)
        # -------------------------------------------------------------
        elif cat == CriterionCategory.BIOMARKER.value:
            canonical_name, ontology_meta = resolve_biomarker(crit.concept_name)
            
            # Find matching lab in patient observations
            matched_lab = None
            for key, lab in patient.labs.items():
                k_canon, _ = resolve_biomarker(key)
                if k_canon.lower() == canonical_name.lower() or (crit.concept_code and lab.loinc == crit.concept_code):
                    matched_lab = lab
                    break

            if not matched_lab or matched_lab.value is None:
                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name=crit.concept_name,
                    rule_summary=f"{crit.concept_name} {op} {crit.threshold} {crit.unit or ''}",
                    patient_value_str="[NOT RECORDED]",
                    status=EvaluationStatus.UNKNOWN,
                    calculation_trace="Observation missing from patient EHR -> UNKNOWN",
                    evidence_source="EHR Lab Panel",
                    protocol_citation=cit_str,
                    failure_reason="Required biomarker measurement is missing from records."
                )

            patient_val = float(matched_lab.value)
            passed = cls._compare_numeric(patient_val, op, crit.threshold)
            
            # Inclusion vs Exclusion logic
            status = EvaluationStatus.PASS if (passed if ctype == "INCLUSION" else not passed) else EvaluationStatus.FAIL
            
            if op == OperatorType.BETWEEN.value:
                calc = f"{crit.threshold[0]} <= {patient_val} <= {crit.threshold[1]} -> {passed}"
            else:
                calc = f"{patient_val} {op} {crit.threshold} -> {passed}"

            day_str = f"Study Day {matched_lab.study_day_offset}" if matched_lab.study_day_offset is not None else "Day 0"
            evidence = f"Lab Panel ({matched_lab.loinc or 'LOINC-Pending'}) collected {day_str}"
            
            fail_reason = None
            if status == EvaluationStatus.FAIL:
                if ctype == "INCLUSION":
                    fail_reason = f"Biomarker {crit.concept_name} ({patient_val} {matched_lab.unit}) does not meet inclusion threshold {crit.threshold}."
                else:
                    fail_reason = f"Biomarker {crit.concept_name} ({patient_val} {matched_lab.unit}) triggers exclusion threshold {crit.threshold}."

            return CriterionEvaluation(
                criterion_id=cid,
                criterion_type=ctype,
                category=cat,
                concept_name=crit.concept_name,
                rule_summary=f"{crit.concept_name} {op} {crit.threshold} {crit.unit or ''}",
                patient_value_str=f"{patient_val} {matched_lab.unit or ''}".strip(),
                status=status,
                calculation_trace=calc,
                evidence_source=evidence,
                protocol_citation=cit_str,
                failure_reason=fail_reason
            )

        # -------------------------------------------------------------
        # 3. DIAGNOSIS EVALUATION (e.g. Type 2 Diabetes, Brain Mets)
        # -------------------------------------------------------------
        elif cat == CriterionCategory.DIAGNOSIS.value:
            has_condition = False
            matched_diag_name = ""
            
            for d in patient.diagnoses:
                if d.is_active and (crit.concept_name.lower() in d.condition_name.lower() or 
                                   (crit.concept_code and crit.concept_code in d.icd10)):
                    has_condition = True
                    matched_diag_name = f"{d.condition_name} ({d.icd10})"
                    break

            if ctype == "INCLUSION":
                status = EvaluationStatus.PASS if has_condition else EvaluationStatus.FAIL
                calc = f"Active diagnosis present -> {has_condition}"
                fail_reason = None if has_condition else f"Mandatory diagnosis '{crit.concept_name}' not documented in patient record."
            else:  # EXCLUSION
                status = EvaluationStatus.FAIL if has_condition else EvaluationStatus.PASS
                calc = f"Exclusionary diagnosis present -> {has_condition}"
                fail_reason = f"Patient has documented exclusionary diagnosis: {matched_diag_name}" if has_condition else None

            val_str = matched_diag_name if has_condition else "No documented diagnosis"
            evidence = f"Problem List / Diagnosis Coding ({crit.concept_code or 'ICD-10'})"

            return CriterionEvaluation(
                criterion_id=cid,
                criterion_type=ctype,
                category=cat,
                concept_name=crit.concept_name,
                rule_summary=f"{'Requires' if ctype == 'INCLUSION' else 'Excludes'} diagnosis: {crit.concept_name}",
                patient_value_str=val_str,
                status=status,
                calculation_trace=calc,
                evidence_source=evidence,
                protocol_citation=cit_str,
                failure_reason=fail_reason
            )

        # -------------------------------------------------------------
        # 4. MEDICATION WASHOUT EVALUATION (e.g. GLP-1 washout >= 30 days)
        # -------------------------------------------------------------
        elif cat == CriterionCategory.MEDICATION_WASHOUT.value:
            req_washout = crit.washout_days or (int(crit.threshold) if crit.threshold else 30)
            
            # Find relevant medication
            med_found = None
            for m in patient.medications:
                m_name = m.drug_name.lower()
                c_name = crit.concept_name.lower()
                if (c_name in m_name or m_name in c_name) or (crit.concept_code and crit.concept_code in (m.rxnorm or "")):
                    med_found = m
                    break

            if not med_found:
                # Never took this restricted drug -> Washout satisfied!
                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name=crit.concept_name,
                    rule_summary=f"Discontinuation of {crit.concept_name} >= {req_washout} days prior to Day 1",
                    patient_value_str="No prior exposure recorded",
                    status=EvaluationStatus.PASS,
                    calculation_trace="No medication exposure detected -> PASS",
                    evidence_source="Medication Administration Record",
                    protocol_citation=cit_str,
                    failure_reason=None
                )

            # If patient is currently taking it or last taken is unknown
            if med_found.is_active:
                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name=crit.concept_name,
                    rule_summary=f"Washout >= {req_washout} days for {crit.concept_name}",
                    patient_value_str="Currently Active Therapy",
                    status=EvaluationStatus.FAIL,
                    calculation_trace=f"Active medication without washout -> FAIL",
                    evidence_source=f"Pharmacy Fill: {med_found.drug_name}",
                    protocol_citation=cit_str,
                    failure_reason=f"Medication {med_found.drug_name} is currently active. Protocol requires {req_washout}-day washout."
                )

            if med_found.last_taken_day_offset is None:
                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name=crit.concept_name,
                    rule_summary=f"Washout >= {req_washout} days for {crit.concept_name}",
                    patient_value_str="Discontinued, date unknown",
                    status=EvaluationStatus.UNKNOWN,
                    calculation_trace="Discontinuation date unavailable -> UNKNOWN",
                    evidence_source="Pharmacy Record",
                    protocol_citation=cit_str,
                    failure_reason="Discontinuation date is missing; cannot verify protocol washout window."
                )

            # Days since last dose = abs(last_taken_day_offset)
            days_elapsed = abs(med_found.last_taken_day_offset)
            passed = days_elapsed >= req_washout
            status = EvaluationStatus.PASS if passed else EvaluationStatus.FAIL
            calc = f"Elapsed days ({days_elapsed}) >= Required washout ({req_washout}) -> {passed}"
            fail_reason = None if passed else f"Only {days_elapsed} days elapsed since last dose of {med_found.drug_name}; {req_washout} days required."

            return CriterionEvaluation(
                criterion_id=cid,
                criterion_type=ctype,
                category=cat,
                concept_name=crit.concept_name,
                rule_summary=f"Washout >= {req_washout} days for {crit.concept_name}",
                patient_value_str=f"{days_elapsed} days elapsed (last dose Study Day {med_found.last_taken_day_offset})",
                status=status,
                calculation_trace=calc,
                evidence_source=f"Medication Record: {med_found.drug_name}",
                protocol_citation=cit_str,
                failure_reason=fail_reason
            )

        # -------------------------------------------------------------
        # 5. CLINICAL STATUS EVALUATION (e.g. Pregnancy, ECOG performance)
        # -------------------------------------------------------------
        elif cat == CriterionCategory.CLINICAL_STATUS.value:
            if "pregnan" in crit.concept_name.lower():
                notes_text = (" ".join(patient.clinical_notes)).lower()
                is_pregnant = "current pregnancy" in notes_text or "pregnant: yes" in notes_text or "positive pregnancy" in notes_text
                is_not_pregnant = "not pregnant" in notes_text or "pregnancy: negative" in notes_text or "pregnancy: no" in notes_text or patient.gender.upper() == "M"

                if is_not_pregnant:
                    status = EvaluationStatus.PASS if ctype == "EXCLUSION" else EvaluationStatus.FAIL
                    calc = "Confirmed not pregnant / male -> Exclusion PASS"
                    val_str = "Not pregnant / Negative"
                    fail_reason = None
                elif is_pregnant:
                    status = EvaluationStatus.FAIL if ctype == "EXCLUSION" else EvaluationStatus.PASS
                    calc = "Documented pregnancy -> Exclusion FAIL"
                    val_str = "Current Pregnancy Documented"
                    fail_reason = "Patient is currently pregnant (violates exclusion criterion)."
                else:
                    status = EvaluationStatus.UNKNOWN
                    calc = "Pregnancy status unconfirmed -> UNKNOWN"
                    val_str = "Unconfirmed status"
                    fail_reason = "Pregnancy status not documented; requires confirmatory assessment."

                return CriterionEvaluation(
                    criterion_id=cid,
                    criterion_type=ctype,
                    category=cat,
                    concept_name="Pregnancy",
                    rule_summary="Excludes current pregnancy" if ctype == "EXCLUSION" else "Requires confirmed status",
                    patient_value_str=val_str,
                    status=status,
                    calculation_trace=calc,
                    evidence_source="Clinical Assessment / Notes",
                    protocol_citation=cit_str,
                    failure_reason=fail_reason
                )

        # Fallback for unexpected categories
        return CriterionEvaluation(
            criterion_id=cid,
            criterion_type=ctype,
            category=cat,
            concept_name=crit.concept_name,
            rule_summary=crit.description,
            patient_value_str="Manual Assessment Required",
            status=EvaluationStatus.UNKNOWN,
            calculation_trace="Non-standard criteria type -> REQUIRES_HUMAN_REVIEW",
            evidence_source="Clinical Notes",
            protocol_citation=cit_str,
            failure_reason="Criteria requires coordinator clinical judgement."
        )

    @staticmethod
    def _compare_numeric(val: float, op: str, thresh: any) -> bool:
        if op == OperatorType.GREATER_THAN.value:
            return val > float(thresh)
        elif op == OperatorType.GREATER_OR_EQUAL.value:
            return val >= float(thresh)
        elif op == OperatorType.LESS_THAN.value:
            return val < float(thresh)
        elif op == OperatorType.LESS_OR_EQUAL.value:
            return val <= float(thresh)
        elif op == OperatorType.EQUAL.value:
            return abs(val - float(thresh)) < 1e-6
        elif op == OperatorType.BETWEEN.value:
            lower, upper = float(thresh[0]), float(thresh[1])
            return lower <= val <= upper
        return False

    @classmethod
    def screen_patient(cls, criteria: List[CriterionDefinition], patient: DeidentifiedPatient) -> Tuple[EligibilityDecision, str, List[CriterionEvaluation], WhyNotEligibleSummary]:
        evaluations: List[CriterionEvaluation] = []
        barriers: List[str] = []
        
        pass_count = 0
        fail_count = 0
        unknown_count = 0

        for crit in criteria:
            ev = cls.evaluate_criterion(crit, patient)
            evaluations.append(ev)
            if ev.status == EvaluationStatus.PASS:
                pass_count += 1
            elif ev.status == EvaluationStatus.FAIL:
                fail_count += 1
                barriers.append(f"[{ev.criterion_id}] {ev.failure_reason or ev.rule_summary}")
            elif ev.status == EvaluationStatus.UNKNOWN:
                unknown_count += 1
                barriers.append(f"[{ev.criterion_id} - UNKNOWN] {ev.failure_reason or 'Missing clinical observation'}")

        # Deterministic decision authority:
        if fail_count > 0:
            decision = EligibilityDecision.INELIGIBLE
            rationale = f"Patient is INELIGIBLE: {fail_count} criteria failed. Review barriers in the 'Why Not Eligible?' dossier."
        elif unknown_count > 0:
            decision = EligibilityDecision.REQUIRES_HUMAN_REVIEW
            rationale = f"Patient REQUIRES HUMAN REVIEW: {unknown_count} criteria could not be deterministically evaluated due to missing or ambiguous documentation."
        else:
            decision = EligibilityDecision.ELIGIBLE
            rationale = f"Patient is ELIGIBLE: All {pass_count} protocol criteria deterministically verified as satisfied."

        why_summary = WhyNotEligibleSummary(
            failed_criteria_count=fail_count,
            unknown_criteria_count=unknown_count,
            critical_barriers=barriers
        )

        return decision, rationale, evaluations, why_summary
