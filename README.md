# Governed Clinical Trial Patient Screening and Regulatory Audit Platform

Screen patients against clinical trial protocols with PHI redaction, hallucination controls, and FDA-style audit dossiers using Lyzr Agent API, Safe AI, and AIMS Governance.

## Context

Clinical trial recruitment is a major bottleneck in clinical development, causing up to 40% of trial delays. Study coordinators manually parse 100+ page protocol documents against unstructured electronic health records (EHR) and laboratory reports.

Standard Large Language Models fail in this mission-critical clinical setting:
- Hallucinated biomarker thresholds can enroll ineligible patients, compromising patient safety and clinical trial integrity.
- Protected Health Information (PHI) can leak into LLM prompts, model weights, and unencrypted external provider logs.
- Regulatory bodies (FDA, EMA) require immutable, verifiable, step-by-step eligibility reasoning compliant with 21 CFR Part 11 electronic records regulations.

## Opportunity

This platform builds an autonomous multi-agent clinical screening infrastructure powered by Lyzr Agent API and Lyzr Safe AI. It ingests complex trial protocols and patient EHRs, enforces deterministic mathematical criteria matching, suppresses hallucinations, scrubs PHI pre-inference, and generates FDA-compliant audit dossiers with live event streaming to Lyzr AIMS.

## 5-Stage Governed Architecture

### 01 Ingestion
Ingests clinical trial protocol documents (PDF, JSON, text) and patient EHR records (JSON, text, PDF, and HL7 FHIR R4 Bundles) into a governed Lyzr environment.

### 02 Protocol Criteria Agent
Extracts inclusion and exclusion rules into structured JSON conditions (e.g. eGFR ranges, HbA1c thresholds, medication washout windows, platelet counts, and active diagnoses) with exact citations back to protocol page and section.

### 03 PHI Scrubbing (Lyzr Safe AI)
Lyzr Safe AI intercepts all patient data before inference. It redacts and normalizes all 18 HIPAA Safe Harbor identifiers (patient names, MRNs, phone numbers, addresses, emails, doctor names, and calendar dates shifted to relative study day offsets). Zero unmasked identifiers enter agent prompts or server logs.

### 04 Screening and Medical Safety
Combines a deterministic biomarker/history matcher with a medical safety agent validated against clinical ontologies (SNOMED-CT, ICD-10, LOINC, and RxNorm). Evaluates strict mathematical boundaries (e.g. eGFR 59.9 vs 60.0 vs 60.1) with 0% tolerance for numerical hallucination.

### 05 Regulatory Audit
The audit agent synthesizes step-by-step decision paths, cross-references protocol citations, computes cryptographic SHA-256 canonical hash seals, supports FDA 21 CFR Part 11 electronic signatures, and streams governance telemetry to Lyzr AIMS.

## Repository Structure

```
your-repo/
|-- agents/
|   |-- __init__.py
|   |-- configs.py                  # Lyzr agent configs, system prompts, schemas
|   |-- protocol_criteria_agent.py  # Agent 1: Protocol criteria extraction
|   |-- medical_safety_agent.py     # Agent 2: Ontology validation (SNOMED, ICD-10, LOINC)
|   |-- regulatory_audit_agent.py   # Agent 3: 21 CFR Part 11 dossier synthesis
|   +-- orchestrator.py             # Multi-agent coordinator, Lyzr triad, HITL pause
|
|-- backend/
|   |-- __init__.py
|   |-- main.py                     # FastAPI application endpoints
|   |-- config.py                   # Environment settings
|   |-- core/                       # Safe AI scrubber, deterministic engine, ontologies, AIMS
|   |-- models/                     # Protocol, patient, dossier, and FHIR Pydantic models
|   |-- services/                   # Screening, ingestion, FHIR generator, HITL, export
|   +-- data/                       # Protocols, synthetic patients, adversarial test suite
|
|-- frontend/
|   |-- index.html                  # Clinical coordinator user interface
|   |-- app.js                      # Client controller, API client, local engine fallback
|   |-- styles.css                  # Professional clinical dashboard theme
|   +-- data/                       # Static dataset fallbacks
|
|-- Dockerfile                      # Production container build
|-- docker-compose.yml              # Local multi-service orchestrator
|-- .env.example                    # Environment keys template (no secrets)
|-- README.md                       # Architecture, setup, and compliance notes
+-- tests/                          # 30 unit, integration, and adversarial tests
```

## MVP Capabilities

- Multi-format ingestion: Clinical protocol documents (PDF, text, JSON) and synthetic EHR records (JSON, text, PDF, FHIR).
- Lyzr triad: Explicit Environment (env_id), Agent (agent_id), and Inference (session-bound) separation.
- Lyzr Safe AI: Automated pre-inference scrubbing of HIPAA identifiers with zero leak verification.
- Deterministic eligibility: ELIGIBLE, INELIGIBLE, or REQUIRES_HUMAN_REVIEW with mathematically grounded confidence scores.
- Audit dossier export: Downloadable FDA-style dossiers in JSON and printable HTML/PDF formats with citations for every evaluated criterion.

## Stretch Goals Implemented

- Human-in-the-Loop (HITL) Webhook Pause: When certainty drops below 90% (due to missing observations or borderline criteria), autonomous processing halts, webhook alerts dispatch to coordinators, and execution waits for an electronic signature override.
- Synthetic FHIR R4 Generator: Generates valid HL7 FHIR R4 Bundles (Patient, Observation, Condition, MedicationStatement) for borderline scenarios (e.g. eGFR 59.9 vs 60.1, Washout 29d vs 31d, missing labs) with one-click load and screen testing.
- Lyzr AIMS Live Dashboard: Real-time governance telemetry tracking decision paths, token usage, latency, and 100% policy compliance.

## Quickstart

### Prerequisites
- Python 3.11 or 3.12
- pip

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone <repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

### 2. Environment Setup
Copy the environment template:
```bash
cp .env.example .env
```
To connect to live Lyzr Cloud endpoints, configure `LYZR_API_KEY` in `.env`. If left empty, the system automatically uses the zero-cost Demo Fallback Engine for offline testing.

### 3. Running the Server
Start the FastAPI server:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at `http://localhost:8000` to access the Clinical Coordinator interface.

### 4. Running with Docker
Build and launch using Docker Compose:
```bash
docker-compose up --build
```

## Automated Testing

Run the test suite:
```bash
pytest
```
The test suite validates:
- Multi-agent orchestration and Lyzr triad separation
- Safe AI PHI scrubbing and zero identifier leakage
- Deterministic mathematical evaluation on inclusive/exclusive thresholds
- Synthetic FHIR R4 Bundle generation
- HITL webhook pause triggers on sub-90% confidence
- SHA-256 tamper-evident integrity seals
- Multi-format document ingestion
- Anti-hallucination adversarial attack resilience

## Regulatory Alignment

- FDA 21 CFR Part 11: Electronic records integrity through canonical JSON serialization, SHA-256 hash sealing, and digital coordinator signatures.
- Predicate FDA M11 Concepts: Protocol representation aligned with standardized structured criteria definitions.
- HIPAA Safe Harbor: 18 protected identifier categories redacted prior to inference.
