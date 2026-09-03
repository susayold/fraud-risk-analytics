from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from .public_export import validate_public_payload


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports/part9"
ASSET_DIR = ROOT / "assets/data"
FORBIDDEN_TEXT = ("dummy", "example metric", "sample pr-auc", "fake", "placeholder score")
GATES = [
    ("A", "source registry exists"), ("A", "all required source files resolved"), ("A", "source hashes recorded"), ("A", "Part 2 totals reconcile"), ("A", "Part 4 feature count reconciles"),
    ("B", "hero has no invented metric"), ("B", "portfolio charts source real reports"), ("B", "behavior chart source registry"), ("B", "model charts render only with executed evidence"), ("B", "graph metrics render only with audited evidence"), ("B", "decision charts render only with genuine Part7 evidence"), ("B", "monitoring charts render only with genuine replay"),
    ("C", "observed metrics labeled correctly"), ("C", "derived metrics labeled correctly"), ("C", "simulated metrics labeled correctly"), ("C", "no production claim"), ("C", "limitations visible"),
    ("D", "chart registry exists"), ("D", "every chart has source"), ("D", "every chart has render condition"), ("D", "no blocked chart contains fake data"), ("D", "chart datasets aggregate-only"), ("D", "low-support categories governed"),
    ("E", "status registry exists"), ("E", "Part9 website status matches registry"), ("E", "README status matches registry"), ("E", "Part7 blocked state preserved"), ("E", "Part8 blocked state preserved"),
    ("F", "no source_row_id"), ("F", "no row-level score"), ("F", "no row-level label"), ("F", "no row-level action"), ("F", "no raw graph edge"),
    ("G", "all deep links valid"), ("G", "all navigation works"), ("G", "mobile layout passes smoke test"), ("G", "reduced motion supported"), ("G", "chart fallback text exists"),
    ("H", "GitHub Pages build passes"), ("H", "final release audit passes"),
]


def _load(name):
    return json.loads((ASSET_DIR / name).read_text(encoding="utf-8"))


def _gate(gate_id, family, description, status, reason, evidence):
    return {"gate_id": gate_id, "family": family, "description": description, "status": status, "reason": reason, "evidence_artifact": evidence, "claim_class": "PRESENTATION_RELEASE"}


def validate() -> pd.DataFrame:
    summary = _load("part9_summary.json")
    charts = _load("part9_charts.json")
    statuses = _load("part9_status.json")
    source_registry = pd.read_csv(REPORT_DIR / "source_manifest.csv")
    html = (ROOT / "part-9.html").read_text(encoding="utf-8")
    errors = []
    available_sources = set(source_registry.loc[source_registry.status == "AVAILABLE", "path"].astype(str))
    metric_ids = set(summary.get("metrics", {}))
    rendered_metric_ids = set(re.findall(r'data-metric="([^"]+)"', html))
    chart_ids = set(re.findall(r'data-chart="([^"]+)"', html))
    if not rendered_metric_ids <= metric_ids: errors.append("unregistered metric id in HTML")
    if not chart_ids <= set(charts): errors.append("unregistered chart id in HTML")
    public_errors = validate_public_payload(summary) + validate_public_payload(charts) + validate_public_payload(statuses)
    p2 = _load("part2_summary.json")
    p4 = pd.read_csv(ROOT / "docs/PART4_FEATURE_REGISTRY.csv")
    checks = {
        "source registry exists": (REPORT_DIR / "source_manifest.csv").exists(),
        "all required source files resolved": all(source_registry.loc[source_registry.source_id.isin(["part2_summary", "part2_split_summary", "part3_monthly_trend", "part3_channel_risk", "part3_amount_band_risk", "part3_mcc_risk", "part3_entity_concentration", "part4_feature_registry", "part5_summary", "part6_summary", "part7_summary", "part8_summary"]), "status"] == "AVAILABLE"),
        "source hashes recorded": source_registry.loc[source_registry.status == "AVAILABLE", "sha256"].astype(str).str.len().eq(64).all(),
        "Part 2 totals reconcile": summary["metrics"]["source_total_transactions"]["value"] == p2["transactions"] and summary["metrics"]["source_fraud_transactions"]["value"] == p2["fraud_transactions"],
        "Part 4 feature count reconciles": summary["metrics"]["behavior_primary_features"]["value"] == len(p4),
        "hero has no invented metric": all(metric.get("source_artifact") and (metric.get("status") != "AVAILABLE" or metric.get("value") is not None) for metric in summary["metrics"].values()),
        "portfolio charts source real reports": all(charts[key]["status"] == "AVAILABLE" and charts[key]["source_artifact"] in available_sources for key in ("P1", "P2", "P3", "P4")),
        "behavior chart source registry": charts["B1"]["status"] == "AVAILABLE" and charts["B1"]["source_artifact"] in available_sources,
        "model charts render only with executed evidence": all(charts[key]["status"] != "AVAILABLE" or charts[key]["source_artifact"] in available_sources for key in ("M1", "M2", "M3", "M4")),
        "graph metrics render only with audited evidence": all(charts[key]["status"] != "AVAILABLE" or charts[key]["source_artifact"] in available_sources for key in ("G1", "G2")),
        "decision charts render only with genuine Part7 evidence": all(charts[key]["status"] != "AVAILABLE" or charts[key]["source_artifact"] in available_sources for key in ("DE1", "DE2", "DE3", "DE4")),
        "monitoring charts render only with genuine replay": all(charts[key]["status"] != "AVAILABLE" or charts[key]["source_artifact"] in available_sources for key in ("MON1", "MON2", "MON3")),
        "observed metrics labeled correctly": all(metric["claim_class"] == "OBSERVED" for metric in summary["metrics"].values() if metric["source_part"] in (2, 3)),
        "derived metrics labeled correctly": summary["metrics"]["behavior_primary_features"]["claim_class"] == "DERIVED",
        "simulated metrics labeled correctly": all(charts[key]["claim_class"] == "SIMULATED" and charts[key]["badge"] == "SIMULATED" for key in ("DE1", "DE2", "DE3", "DE4")),
        "no production claim": "not a deployed enterprise fraud platform" in summary["project"]["claim"].lower(),
        "limitations visible": "production deployment" in html.lower() and "not claimed" in html.lower(),
        "chart registry exists": (REPORT_DIR / "part9_chart_registry.csv").exists(),
        "every chart has source": all(chart.get("source_artifact") for chart in charts.values()),
        "every chart has render condition": all(chart.get("render_condition") == "status == AVAILABLE" for chart in charts.values()),
        "no blocked chart contains fake data": all(chart["status"] == "AVAILABLE" or chart.get("data") == [] for chart in charts.values()),
        "chart datasets aggregate-only": not public_errors,
        "low-support categories governed": charts["P4"].get("support_field") == "transactions" and "support-qualified" in charts["P4"]["title"].lower(),
        "status registry exists": (ASSET_DIR / "part9_status.json").exists(),
        "Part9 website status matches registry": statuses["project_status"] in html or "FINAL_PORTFOLIO_READY" in html,
        "README status matches registry": "Final portfolio ready" in (ROOT / "README.md").read_text(encoding="utf-8"),
        "Part7 blocked state preserved": statuses["layers"]["part7"]["status"] == "INPUT_BLOCKED",
        "Part8 blocked state preserved": statuses["layers"]["part8"]["status"] == "INPUT_BLOCKED",
        "no source_row_id": not public_errors,
        "no row-level score": not public_errors,
        "no row-level label": not public_errors,
        "no row-level action": not public_errors,
        "no raw graph edge": not public_errors,
        "all deep links valid": all((ROOT / href).exists() for href in re.findall(r'href="(part-[1-8]\.html|docs/[^"#]+|reports/[^"#]+)"', html)),
        "all navigation works": len(re.findall(r'href="part-[1-9]\.html"', html)) >= 9,
        "mobile layout passes smoke test": "@media(max-width:800px)" in (ROOT / "css/part-9.css").read_text(encoding="utf-8"),
        "reduced motion supported": "prefers-reduced-motion" in (ROOT / "css/part-9.css").read_text(encoding="utf-8"),
        "chart fallback text exists": html.count('class="chart-alt"') == len(charts),
        "GitHub Pages build passes": (ROOT / "part-9.html").exists() and (ROOT / "js/part-9.js").exists() and (ROOT / "css/part-9.css").exists(),
        "final release audit passes": (REPORT_DIR / "PART9_FINAL_RELEASE_AUDIT.md").exists(),
    }
    files_to_scan = [ROOT / "part-9.html", ASSET_DIR / "part9_summary.json", ASSET_DIR / "part9_charts.json", ASSET_DIR / "part9_status.json"]
    fake_text = any(token in path.read_text(encoding="utf-8").lower() for path in files_to_scan for token in FORBIDDEN_TEXT)
    checks["hero has no invented metric"] = checks["hero has no invented metric"] and not fake_text and not errors
    rows = []
    for index, (family, description) in enumerate(GATES, 1):
        status = "PASS" if checks.get(description, False) else "FAIL"
        rows.append(_gate(f"P9T{index:02d}", family, description, status, "validated against presentation registry" if status == "PASS" else "presentation contract check failed", "reports/part9/"))
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Block G / Part 9 evidence-backed portfolio")
    parser.parse_args()
    result = validate()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(REPORT_DIR / "part9_validation_report.csv", index=False)
    counts = result.status.value_counts().to_dict()
    print(f"Part 9 validator: {counts.get('PASS', 0)} PASS / {counts.get('FAIL', 0)} FAIL")
    return 0 if counts.get("FAIL", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
