from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports/portfolio_closure_validation.csv"


def check(name: str, passed: bool, evidence: str) -> dict:
    return {"gate": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def validate() -> list[dict]:
    read = lambda path: (ROOT / path).read_text(encoding="utf-8")
    root = read("index.html")
    p5 = read("part-5.html")
    p6 = read("part-6.html")
    p8 = read("part-8.html")
    p9 = read("part-9.html")
    summary = json.loads(read("assets/data/part6_summary.json"))
    status = json.loads(read("assets/data/project_status.json"))
    charts = json.loads(read("assets/data/part9_charts.json"))
    gates = [
        check("PV01 root opens final portfolio", "09 Deliver" in root and "FINAL PORTFOLIO" in root, "index.html"),
        check("PV02 root is not a Part 1 landing page", "Business Scope &amp; Project Governance" not in root[:1800], "index.html"),
        check("PV03 root canonical is portfolio URL", 'rel="canonical" href="https://susayold.github.io/fraud-risk-analytics/"' in root, "index.html"),
        check("PV04 root links GitHub evidence", "github.com/susayold/fraud-risk-analytics" in root, "index.html"),
        check("PV05 all nine part pages exist", all((ROOT / f"part-{i}.html").exists() for i in range(1, 10)), "part-1.html … part-9.html"),
        check("PV06 Part 6 is no longer placeholder", "scaffolded for the next implementation pass" not in p6 and "GRAPH_EVIDENCE_READY" in p6, "part-6.html"),
        check("PV07 Part 6 has graph contract", "POINT-IN-TIME RULE" in p6 and "no raw IDs or edges" in p6, "part-6.html"),
        check("PV08 Part 6 summary is locked", summary.get("status") == "LOCKED" and summary.get("technical_status") == "GRAPH_EVIDENCE_READY", "assets/data/part6_summary.json"),
        check("PV09 Part 6 summary is aggregate-only", summary.get("public_boundary", {}).get("aggregate_only") is True and not summary["public_boundary"].get("raw_ids_published"), "assets/data/part6_summary.json"),
        check("PV10 Part 6 network evidence exists", summary.get("graph", {}).get("total_nodes") == 106482 and summary["graph"].get("train_unique_edges") == 854007, "assets/data/part6_summary.json"),
        check("PV11 Part 6 temporal link evidence exists", summary.get("temporal_link_learning", {}).get("link_ap", 0) > 0.9 and summary["temporal_link_learning"].get("max_parameter_sync_diff") == 0, "assets/data/part6_summary.json"),
        check("PV12 Part 6 uplift caveat is visible", "not statistically robust" in p6 and "NON_ROBUST_OR_INCONCLUSIVE" in p6, "part-6.html"),
        check("PV13 Part 6 graph boundary is visible", "It cannot decide alone" in p6 and "Graph-only BLOCK" in p6, "part-6.html"),
        check("PV14 Part 5 full lifecycle is visible", all(x in p5 for x in ("Foundation", "Frontier challengers", "Champion freeze", "Final OOT")), "part-5.html"),
        check("PV15 Part 5 metrics stay source-driven", "METRICS SOURCE-DRIVEN" in p5 and "Metrics source-driven" in p5, "part-5.html"),
        check("PV16 Part 5 no stale P5.1-only hero", "PART 5 · P5.1" not in p5, "part-5.html"),
        check("PV17 Part 8 has no stale fallback counts", "data-p8-pass>16" not in p8 and "data-p8-blocked>56" not in p8 and "data-p8-fail>0" not in p8, "part-8.html"),
        check("PV18 Part 8 load failure is visible", "EVIDENCE LOAD ERROR" in read("js/part8.js"), "js/part8.js"),
        check("PV19 Part 9 concentration chart available", charts.get("P5", {}).get("status") == "AVAILABLE" and charts["P5"].get("source_artifact") == "reports/part3/top_entity_concentration.csv", "assets/data/part9_charts.json"),
        check("PV20 Part 9 graph charts available", all(charts.get(x, {}).get("status") == "AVAILABLE" for x in ("G1", "G2")), "assets/data/part9_charts.json"),
        check("PV21 project status registry exists", status.get("project_status") == "FINAL_PORTFOLIO_RELEASE_LOCKED" and len(status.get("layers", {})) == 9, "assets/data/project_status.json"),
        check("PV22 Part 7 remains input blocked", status["layers"]["part7"]["status"] == "INPUT_BLOCKED", "assets/data/project_status.json"),
        check("PV23 Part 8 remains input blocked", status["layers"]["part8"]["status"] == "INPUT_BLOCKED", "assets/data/project_status.json"),
        check("PV24 Part 6 status is locked", status["layers"]["part6"]["status"] == "LOCKED", "assets/data/project_status.json"),
        check("PV25 every part returns to final portfolio", all("href=\"index.html\"" in read(f"part-{i}.html") for i in range(1, 10)), "part-1.html … part-9.html"),
        check("PV26 no raw graph identifiers are public", all(token not in read("assets/data/part6_summary.json") for token in ("card_id", "merchant_id", "source_row_id", "edge_id")), "part6_summary.json"),
        check("PV27 no production overclaim in Part 6", "production" in p6.lower() and "not allowed" in p6.lower(), "part-6.html"),
        check("PV28 Part 9 source registry is rebuilt", (ROOT / "reports/part9/source_manifest.csv").exists() and "part6_summary" in read("reports/part9/source_manifest.csv"), "reports/part9/source_manifest.csv"),
        check("PV29 Part 9 chart registry is rebuilt", (ROOT / "reports/part9/part9_chart_registry.csv").exists() and "P5" in read("reports/part9/part9_chart_registry.csv"), "reports/part9/part9_chart_registry.csv"),
        check("PV30 final validator artifacts exist", (ROOT / "reports/part9/part9_validation_report.csv").exists() and (ROOT / "reports/part9/PART9_FINAL_RELEASE_AUDIT.md").exists(), "reports/part9/"),
    ]
    return gates


def main() -> int:
    gates = validate()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "status", "evidence"])
        writer.writeheader()
        writer.writerows(gates)
    passed = sum(row["status"] == "PASS" for row in gates)
    print(f"Public portfolio validator: {passed} PASS / {len(gates) - passed} FAIL")
    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
