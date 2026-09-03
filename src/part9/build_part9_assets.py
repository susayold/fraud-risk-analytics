from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from .chart_builder import build_charts
from .claim_boundary import validate_chart, validate_metrics
from .metric_registry import build_metric_registry
from .public_export import validate_public_payload
from .source_registry import build_source_registry
from .status_reconciliation import build_status_registry


ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "assets/data"
REPORT_DIR = ROOT / "reports/part9"


def _write_json(path: Path, value) -> None:
    def clean(item):
        if isinstance(item, dict): return {str(k): clean(v) for k, v in item.items()}
        if isinstance(item, list): return [clean(v) for v in item]
        try:
            if pd.isna(item): return None
        except (TypeError, ValueError): pass
        return item.item() if hasattr(item, "item") else item
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(value), indent=2, ensure_ascii=False, default=str, allow_nan=False) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    sources = build_source_registry(ROOT)
    metrics = build_metric_registry(ROOT)
    statuses = build_status_registry(ROOT)
    charts = build_charts(ROOT)
    source_errors = [f"{row.source_id}: missing" for row in sources.itertuples() if row.status == "NOT_AVAILABLE" and row.source_id in {"part2_summary", "part2_split_summary", "part3_monthly_trend", "part3_channel_risk", "part3_amount_band_risk", "part3_mcc_risk", "part4_feature_registry", "part5_summary", "part7_summary", "part8_summary"}]
    metric_errors = validate_metrics(metrics.to_dict("records"), ROOT)
    chart_errors = [error for chart in charts.values() for error in validate_chart(chart, ROOT)]
    summary = {"project": {"name": "Fraud Risk Analytics", "part": 9, "title": "Final Product & Portfolio Delivery", "status": "FINAL_PORTFOLIO_READY", "claim": "End-to-end evidence-backed fraud-risk analytics portfolio; not a deployed enterprise fraud platform."}, "hero": {"headline": "Financial Fraud Risk Analytics & Transaction Decisioning", "subheadline": "A recruiter-ready case study connecting audited transaction data to portfolio intelligence, point-in-time behavior, risk scoring, graph context, decision policy and monitoring governance."}, "metrics": {row.metric_id: {k: v for k, v in row._asdict().items() if k != "Index"} for row in metrics.itertuples()}, "business": {"success_criteria": ["Capture fraud", "Control false positives", "Protect customer experience", "Respect review capacity"], "kpi_note": "KPI cards in this section are definitions unless an executed source artifact makes a result available."}, "architecture": {"nodes": ["IBM Synthetic Transactions", "Data Audit / SQL / DuckDB", "Portfolio Analytics", "PIT Feature Engine", "Fraud Scoring", "Graph Intelligence", "Decision Policy", "ALLOW / REVIEW / BLOCK", "Monitoring & Governance"], "rails": ["Chronology", "Leakage Control", "Claim Boundary", "Versioning"]}, "governance": {"observed": "Directly measured source and portfolio aggregates", "derived": "Features, scores, graph context and model outputs only where executed", "simulated": "Policy economics and interventions when explicitly labeled", "prohibited": ["production deployment", "actual bank losses prevented", "actual customer impact", "regulatory validation", "live operational monitoring"]}, "engineering": {"stack": ["Python", "SQL", "DuckDB", "Pandas", "Scikit-learn / model stack", "NetworkX", "GitHub Actions", "HTML / CSS / JavaScript"], "reproducibility": ["versioned configs", "report manifests", "SHA256 source hashing", "public boundary validation"]}, "statuses": statuses, "source_reconciliation": {"status": "PASS" if not source_errors and not metric_errors else "FAIL", "errors": source_errors + metric_errors, "notes": "Conditional upstream sources may remain INPUT_BLOCKED; they are not replaced with fabricated metrics."}}
    # Keep chart data in its own payload so the browser can lazy-load/initialize it.
    summary["charts"] = {chart_id: {key: value for key, value in chart.items() if key != "data"} for chart_id, chart in charts.items()}
    summary["evidence"] = {"source_registry": "reports/part9/source_manifest.csv", "metric_registry": "reports/part9/part9_metric_registry.csv", "chart_registry": "reports/part9/part9_chart_registry.csv", "status_registry": "reports/part9/part9_status_registry.csv"}
    public_errors = validate_public_payload(summary) + [error for chart in charts.values() for error in validate_public_payload(chart)]
    if public_errors:
        raise ValueError(f"Part 9 public boundary failed: {public_errors[:5]}")
    sources.to_csv(REPORT_DIR / "source_manifest.csv", index=False)
    sources.to_csv(REPORT_DIR / "part9_source_registry.csv", index=False)
    metrics.to_csv(REPORT_DIR / "part9_metric_registry.csv", index=False)
    pd.DataFrame([{"layer": key, "label": value.get("label"), "status": value.get("status"), "technical_status": value.get("technical_status"), "execution_status": value.get("execution_status", ""), "deep_link": value.get("deep_link")} for key, value in statuses["layers"].items()]).to_csv(REPORT_DIR / "part9_status_registry.csv", index=False)
    chart_rows = []
    for chart in charts.values():
        chart_rows.append({key: chart.get(key, "") for key in ("chart_id", "section", "title", "chart_type", "source_artifact", "x_field", "y_field", "support_field", "claim_class", "render_condition", "status")})
    pd.DataFrame(chart_rows).to_csv(REPORT_DIR / "part9_chart_registry.csv", index=False)
    _write_json(ASSET_DIR / "part9_summary.json", summary)
    _write_json(ASSET_DIR / "part9_charts.json", charts)
    _write_json(ASSET_DIR / "part9_status.json", statuses)
    _write_json(ASSET_DIR / "part9_evidence_registry.json", {"sources": sources.to_dict("records"), "metrics": metrics.to_dict("records"), "charts": summary["charts"]})
    _write_json(REPORT_DIR / "PART9_SOURCE_RECONCILIATION.json", summary["source_reconciliation"])
    _write_json(REPORT_DIR / "PART9_FINAL_SUMMARY.json", {"status": "FINAL_PORTFOLIO_READY", "upstream_execution_boundary": "Part 5/6/7/8 conditional views remain source-driven", "available_charts": [key for key, value in charts.items() if value["status"] == "AVAILABLE"], "blocked_charts": [key for key, value in charts.items() if value["status"] != "AVAILABLE"], "public_boundary": "PASS", "source_count": len(sources), "metric_count": len(metrics), "chart_count": len(charts)})
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip() or "UNKNOWN"
    manifest = {"build_timestamp": pd.Timestamp.utcnow().isoformat(), "code_commit": commit, "source_registry_hash": _sha(REPORT_DIR / "source_manifest.csv"), "summary_hash": _sha(ASSET_DIR / "part9_summary.json"), "charts_hash": _sha(ASSET_DIR / "part9_charts.json"), "status_hash": _sha(ASSET_DIR / "part9_status.json")}
    _write_json(ASSET_DIR / "part9_manifest.json", manifest)
    report_rows = []
    for path in sorted(REPORT_DIR.iterdir()):
        if path.is_file() and path.name != "report_manifest.csv":
            report_rows.append({"relative_path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": _sha(path), "claim_class": "PUBLIC_EVIDENCE"})
    pd.DataFrame(report_rows).to_csv(REPORT_DIR / "report_manifest.csv", index=False)
    return {"summary": summary, "charts": charts, "sources": sources, "metrics": metrics, "statuses": statuses, "errors": chart_errors}


if __name__ == "__main__":
    result = build()
    print(f"Part 9 assets: {len(result['metrics'])} metrics, {len(result['charts'])} charts, {len(result['sources'])} sources")
