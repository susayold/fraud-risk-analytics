from __future__ import annotations

from pathlib import Path


ALLOWED_CLAIMS = {"OBSERVED", "DERIVED", "SIMULATED", "GOVERNANCE", "DEFINITION"}


def validate_metrics(metrics, root: Path) -> list[str]:
    errors = []
    for metric in metrics:
        if metric.get("claim_class") not in ALLOWED_CLAIMS:
            errors.append(f"{metric.get('metric_id')}: invalid claim class")
        source = root / str(metric.get("source_artifact", ""))
        status = metric.get("status")
        if status == "AVAILABLE" and not source.exists():
            errors.append(f"{metric.get('metric_id')}: available metric source missing")
        if status == "AVAILABLE" and metric.get("value") is None:
            errors.append(f"{metric.get('metric_id')}: available metric is null")
    return errors


def validate_chart(chart, root: Path) -> list[str]:
    errors = []
    if chart.get("claim_class") not in ALLOWED_CLAIMS:
        errors.append(f"{chart.get('chart_id')}: invalid claim class")
    if not chart.get("source_artifact"):
        errors.append(f"{chart.get('chart_id')}: source missing")
    if chart.get("status") == "AVAILABLE" and not (root / chart["source_artifact"]).exists():
        errors.append(f"{chart.get('chart_id')}: available source missing")
    if chart.get("status") != "AVAILABLE" and chart.get("data"):
        errors.append(f"{chart.get('chart_id')}: blocked chart contains data")
    if chart.get("claim_class") == "SIMULATED" and "SIMULATED" not in str(chart.get("badge", "SIMULATED")):
        errors.append(f"{chart.get('chart_id')}: simulated badge missing")
    return errors
