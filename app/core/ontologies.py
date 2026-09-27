"""
Medical Ontologies Reference Mapping: LOINC, ICD-10, SNOMED CT, RxNorm
Standardizes protocol criteria and patient records to avoid semantic mismatch.
"""

LOINC_ONTOLOGY = {
    "eGFR": {
        "code": "LOINC: 33914-3",
        "long_name": "Glomerular filtration rate/1.73 sq M.predicted [Volume Rate/Area] in Serum, Plasma or Blood",
        "standard_unit": "mL/min/1.73m2",
        "aliases": ["egfr", "estimated gfr", "gfr", "egfr_ckd_epi"]
    },
    "HbA1c": {
        "code": "LOINC: 4548-4",
        "long_name": "Hemoglobin A1c/Hemoglobin.total in Blood",
        "standard_unit": "%",
        "aliases": ["hba1c", "a1c", "glycated hemoglobin", "hemoglobin a1c"]
    },
    "ANC": {
        "code": "LOINC: 26464-8",
        "long_name": "Leukocytes.neutrophils [#/volume] in Blood",
        "standard_unit": "/uL",
        "aliases": ["anc", "absolute neutrophil count", "neutrophils"]
    },
    "Platelets": {
        "code": "LOINC: 777-3",
        "long_name": "Platelets [#/volume] in Blood",
        "standard_unit": "/uL",
        "aliases": ["platelets", "platelet count", "plt"]
    },
    "NT-proBNP": {
        "code": "LOINC: 33762-6",
        "long_name": "Natriuretic peptide.B prohormone N-Terminal [Mass/volume] in Serum or Plasma",
        "standard_unit": "pg/mL",
        "aliases": ["nt-probnp", "bnp", "pro-bnp", "n-terminal pro-bnp"]
    },
    "LVEF": {
        "code": "LOINC: 88062-5",
        "long_name": "Left ventricular ejection fraction by Echocardiography",
        "standard_unit": "%",
        "aliases": ["lvef", "ejection fraction", "ef"]
    },
    "SystolicBP": {
        "code": "LOINC: 8480-6",
        "long_name": "Systolic blood pressure",
        "standard_unit": "mmHg",
        "aliases": ["sbp", "systolic", "systolic bp"]
    },
    "ALT": {
        "code": "LOINC: 1742-6",
        "long_name": "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma",
        "standard_unit": "U/L",
        "aliases": ["alt", "sgpt"]
    },
    "HeartRate": {
        "code": "LOINC: 8867-4",
        "long_name": "Heart rate [#/time]",
        "standard_unit": "bpm",
        "aliases": ["heart rate", "pulse", "hr"]
    },
    "MMSE": {
        "code": "LOINC: 72106-8",
        "long_name": "Mini-Mental State Examination total score",
        "standard_unit": "points",
        "aliases": ["mmse", "mini-mental", "cognitive score"]
    },
    "ECOG": {
        "code": "LOINC: 89247-1",
        "long_name": "ECOG Performance Status score",
        "standard_unit": "score",
        "aliases": ["ecog", "performance status", "ecog ps"]
    }
}

SNOMED_ONTOLOGY = {
    "Type 2 Diabetes": {"code": "SNOMED: 44054006", "concept": "Diabetes mellitus type 2 (disorder)"},
    "Non-Small Cell Lung Cancer": {"code": "SNOMED: 254637007", "concept": "Non-small cell lung cancer (disorder)"},
    "Brain Metastases": {"code": "SNOMED: 94225005", "concept": "Secondary malignant neoplasm of brain (disorder)"},
    "Heart Failure": {"code": "SNOMED: 84114007", "concept": "Heart failure (disorder)"},
    "Early Alzheimer Disease": {"code": "SNOMED: 26929004", "concept": "Alzheimer's disease (disorder)"}
}

ICD10_ONTOLOGY = {
    "Type 2 Diabetes": {"code": "ICD-10: E11.9", "description": "Type 2 diabetes mellitus without complications"},
    "Non-Small Cell Lung Cancer": {"code": "ICD-10: C34.90", "description": "Malignant neoplasm of unsp part of unsp bronchus or lung"},
    "Brain Metastases": {"code": "ICD-10: C79.31", "description": "Secondary malignant neoplasm of brain"},
    "Heart Failure": {"code": "ICD-10: I50.9", "description": "Heart failure, unspecified"},
    "Chronic Kidney Disease": {"code": "ICD-10: N18.30", "description": "Chronic kidney disease, stage 3 unspecified"},
    "Diabetic Ketoacidosis": {"code": "ICD-10: E11.10", "description": "Type 2 diabetes with ketoacidosis without coma"},
    "Early Alzheimer Disease": {"code": "ICD-10: G30.0", "description": "Alzheimer's disease with early onset"}
}

RXNORM_ONTOLOGY = {
    "GLP-1 Receptor Agonist": {
        "code": "RxNorm: 1358983",
        "class_name": "Glucagon-like peptide-1 receptor agonists",
        "substances": ["semaglutide", "liraglutide", "dulaglutide", "exenatide", "ozempic", "wegovy", "mounjaro"]
    },
    "EGFR-TKI": {
        "code": "RxNorm: 1658189",
        "class_name": "Epidermal growth factor receptor tyrosine kinase inhibitors",
        "substances": ["osimertinib", "erlotinib", "gefitinib", "afatinib", "tagrisso"]
    }
}

def resolve_biomarker(name: str):
    name_clean = name.strip().lower()
    for key, data in LOINC_ONTOLOGY.items():
        if key.lower() == name_clean or name_clean in [a.lower() for a in data["aliases"]]:
            return key, data
    return name, {"code": "CUSTOM", "standard_unit": "", "long_name": name}
