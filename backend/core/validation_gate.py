from typing import List, Dict, Any
from app.models.protocol_models import (
    CriterionDefinition,
    ValidationGateResult,
    OperatorType,
    CriterionCategory
)

class ProtocolValidationGate:
    """
    Protocol Validation Gate: Anti-Hallucination Firewall.
    Validates LLM-extracted criteria before allowing them into the screening engine.
    Rejects malformed rules (e.g. missing bounds on ranges, missing citations, invalid operators).
    """

    ALLOWED_OPERATORS = {op.value for op in OperatorType}

    @classmethod
    def validate_criterion(cls, crit_dict: Dict[str, Any]) -> tuple[bool, str, CriterionDefinition | None]:
        cid = crit_dict.get("criterion_id", "UNKNOWN")

        # 1. Operator validation
        op = crit_dict.get("operator")
        if not op or op not in cls.ALLOWED_OPERATORS:
            return False, f"Criterion {cid}: Invalid or missing operator '{op}'. Must be one of {cls.ALLOWED_OPERATORS}.", None

        # 2. Category validation
        cat = crit_dict.get("category")
        try:
            CriterionCategory(cat)
        except Exception:
            return False, f"Criterion {cid}: Invalid category '{cat}'.", None

        # 3. Citation validation (FDA requirement)
        citation = crit_dict.get("protocol_citation", {})
        if not isinstance(citation, dict):
            return False, f"Criterion {cid}: Citation must be a valid structured object.", None
        if not citation.get("page") or citation.get("page") <= 0:
            return False, f"Criterion {cid}: Citation missing valid page number.", None
        if not citation.get("section") or not str(citation.get("section")).strip():
            return False, f"Criterion {cid}: Citation missing section title.", None

        # 4. Operator-specific threshold validations
        if op == OperatorType.BETWEEN.value:
            thresh = crit_dict.get("threshold")
            if not isinstance(thresh, (list, tuple)) or len(thresh) != 2:
                return False, f"Criterion {cid}: Operator BETWEEN requires 2 numeric bounds [lower, upper], received: {thresh}.", None
            try:
                lower = float(thresh[0])
                upper = float(thresh[1])
                if lower >= upper:
                    return False, f"Criterion {cid}: Lower bound ({lower}) must be strictly less than upper bound ({upper}).", None
            except (ValueError, TypeError):
                return False, f"Criterion {cid}: Bounds for BETWEEN must be numeric.", None

        elif op in {OperatorType.GREATER_THAN.value, OperatorType.GREATER_OR_EQUAL.value,
                   OperatorType.LESS_THAN.value, OperatorType.LESS_OR_EQUAL.value}:
            thresh = crit_dict.get("threshold")
            try:
                float(thresh)
            except (ValueError, TypeError):
                return False, f"Criterion {cid}: Operator '{op}' requires a numeric threshold, received: {thresh}.", None

        elif op == OperatorType.WASHOUT_DAYS.value:
            washout = crit_dict.get("washout_days") or crit_dict.get("threshold")
            try:
                w_val = int(washout)
                if w_val <= 0:
                    return False, f"Criterion {cid}: Washout duration must be > 0 days.", None
                crit_dict["washout_days"] = w_val
            except (ValueError, TypeError):
                return False, f"Criterion {cid}: Washout duration must be an integer, received: {washout}.", None

        # 5. Biomarker unit validation
        if cat == CriterionCategory.BIOMARKER.value and not crit_dict.get("unit"):
            return False, f"Criterion {cid}: Biomarker criteria must include a standardized unit.", None

        # Build validated Pydantic model
        try:
            criterion_obj = CriterionDefinition(**crit_dict)
            return True, "Valid", criterion_obj
        except Exception as e:
            return False, f"Criterion {cid}: Schema instantiation error: {str(e)}", None

    @classmethod
    def validate_protocol_criteria(cls, raw_criteria: List[Dict[str, Any]]) -> ValidationGateResult:
        validated = []
        rejected = []
        errors = []

        for crit in raw_criteria:
            is_valid, reason, obj = cls.validate_criterion(crit)
            if is_valid and obj:
                validated.append(obj)
            else:
                rejected.append(crit)
                errors.append(reason)

        return ValidationGateResult(
            is_valid=len(rejected) == 0,
            validated_criteria=validated,
            rejected_criteria=rejected,
            validation_errors=errors
        )
