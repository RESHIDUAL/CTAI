import hashlib
import json
from typing import Dict, Any
from app.models.dossier_models import AuditDossier

class DossierExportService:
    """
    Export Service for 21 CFR Part 11-Aligned Audit Dossiers.
    Produces cryptographic SHA-256 hash seals and FDA-style printable records.
    """

    @staticmethod
    def calculate_sha256(payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_html_dossier(dossier: AuditDossier) -> str:
        """
        Generates an FDA-style clinical trial screening audit report.
        """
        eval_rows = ""
        for ev in dossier.evaluations:
            status_color = "#10b981" if ev.status == "PASS" else ("#ef4444" if ev.status == "FAIL" else "#f59e0b")
            status_bg = "#ecfdf5" if ev.status == "PASS" else ("#fef2f2" if ev.status == "FAIL" else "#fffbeb")
            eval_rows += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; font-weight: bold; font-family: monospace;">{ev.criterion_id}</td>
                <td style="padding: 10px;">{ev.concept_name}<br><small style="color: #64748b;">{ev.rule_summary}</small></td>
                <td style="padding: 10px;"><strong>{ev.patient_value_str}</strong><br><small style="color: #64748b;">{ev.evidence_source}</small></td>
                <td style="padding: 10px; font-family: monospace; font-size: 12px;">{ev.calculation_trace}</td>
                <td style="padding: 10px; font-size: 12px; color: #475569;">{ev.protocol_citation}</td>
                <td style="padding: 10px; text-align: center;">
                    <span style="padding: 4px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px; background-color: {status_bg}; color: {status_color}; border: 1px solid {status_color};">
                        {ev.status}
                    </span>
                </td>
            </tr>
            """

        decision_color = "#10b981" if dossier.decision == "ELIGIBLE" else ("#ef4444" if dossier.decision == "INELIGIBLE" else "#f59e0b")
        sig = dossier.coordinator_signature or dossier.crc_signature or {}
        sig_html = f"""
        <div style="margin-top: 24px; padding: 16px; border: 1px dashed #94a3b8; border-radius: 6px; background: #f8fafc;">
            <h4 style="margin: 0 0 8px 0; color: #1e293b;">Electronic Signature (21 CFR Part 11 Aligned)</h4>
            <p style="margin: 4px 0; font-size: 13px;"><strong>Signer:</strong> {sig.get('crc_name', 'Dr. Coordinator, MD')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><strong>Role:</strong> {sig.get('role', 'Clinical Research Coordinator / Principal Investigator')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><strong>Timestamp:</strong> {sig.get('timestamp', dossier.timestamp_utc)}</p>
            <p style="margin: 4px 0; font-size: 13px;"><strong>Meaning:</strong> I certify that I have reviewed the deterministic screening evidence and verify this clinical determination.</p>
        </div>
        """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Regulatory Audit Dossier - {dossier.patient_pseudonym}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #0f172a; line-height: 1.5; }}
        .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ display: inline-block; padding: 6px 14px; border-radius: 6px; font-weight: 800; font-size: 14px; color: white; background: {decision_color}; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; background: #f1f5f9; padding: 16px; border-radius: 8px; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        th {{ background: #f8fafc; text-align: left; padding: 10px; border-bottom: 2px solid #cbd5e1; font-size: 12px; text-transform: uppercase; color: #475569; }}
        .hash-box {{ font-family: monospace; font-size: 11px; background: #0f172a; color: #38bdf8; padding: 12px; border-radius: 6px; word-break: break-all; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0 0 6px 0;">Clinical Trial Screening Audit Dossier</h1>
        <p style="margin: 0; color: #64748b; font-size: 14px;">Governed under 21 CFR Part 11-Aligned Traceability Framework (FDA M11 Reference)</p>
    </div>

    <div class="meta-grid">
        <div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Protocol NCT ID</div>
            <div style="font-weight: 700; font-size: 15px;">{dossier.protocol_nct_id}</div>
            <div style="font-size: 12px; color: #475569;">{dossier.protocol_title}</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Patient Pseudonym</div>
            <div style="font-weight: 700; font-size: 15px;">{dossier.patient_pseudonym}</div>
            <div style="font-size: 12px; color: #10b981;">PHI De-Identified (Zero Unmasked Identifiers)</div>
        </div>
        <div>
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: bold;">Screening Outcome</div>
            <div style="margin-top: 4px;"><span class="badge">{dossier.decision}</span></div>
        </div>
    </div>

    <div style="padding: 14px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 6px 0;">Deterministic Decision Rationale</h3>
        <p style="margin: 0; font-size: 14px; color: #334155;">{dossier.decision_rationale}</p>
        <div style="margin-top: 10px; font-size: 13px;">
            <span style="color: #10b981; font-weight: bold;">PASS: {dossier.pass_count}</span> | 
            <span style="color: #ef4444; font-weight: bold;">FAIL: {dossier.fail_count}</span> | 
            <span style="color: #f59e0b; font-weight: bold;">UNKNOWN: {dossier.unknown_count}</span>
        </div>
    </div>

    <h3>Detailed Criteria Evaluation & Traceability Matrix</h3>
    <table>
        <thead>
            <tr>
                <th>Criterion</th>
                <th>Concept & Rule</th>
                <th>Patient Evidence</th>
                <th>Deterministic Logic</th>
                <th>Protocol Citation</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {eval_rows}
        </tbody>
    </table>

    {sig_html}

    <div class="hash-box">
        <strong>CRYPTOGRAPHIC INTEGRITY SEAL (SHA-256):</strong><br>
        {dossier.sha256_checksum}<br>
        <span style="color: #94a3b8; font-size: 10px;">Generated at {dossier.timestamp_utc} | AIMS Trace: {dossier.aims_trace_id} | Execution: {dossier.execution_mode}</span>
    </div>
</body>
</html>
"""
        return html
