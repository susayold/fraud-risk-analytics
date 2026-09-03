from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate() -> list[tuple[str, bool]]:
    d = json.loads((ROOT / "assets/data/part6_summary.json").read_text(encoding="utf-8"))
    checks = [
        ("locked status", d["status"] == "LOCKED"),
        ("foundation scope present", d["foundation_graph"]["lifetime_unique_pairs"] == 978288),
        ("TRAIN graph scope present", d["train_network"]["train_unique_edges"] == 854007),
        ("scopes not conflated", d["foundation_graph"]["lifetime_unique_pairs"] != d["train_network"]["train_unique_edges"]),
        ("temporal link evidence", d["temporal_link_learning"]["link_ap"] > 0.9),
        ("zero sync diff", d["temporal_link_learning"]["max_parameter_sync_diff"] == 0),
        ("three candidate models", len(d["model_comparison"]["test_warm"]) == 3),
        ("validation champion C", d["model_comparison"]["validation_champion"] == "C_EDGE_PLUS_GNN"),
        ("test does not override", d["model_comparison"]["test_selection_override"] is False),
        ("uncertainty includes C-A", any(x["comparison"] == "C_MINUS_A" for x in d["pairwise_uncertainty"])),
        ("monthly evidence present", len(d["monthly_stability"]["rows"]) == 10),
        ("community labels posthoc", d["graph"]["community_construction_uses_fraud_label"] is False and d["graph"]["validation_test_labels_used_only_for_posthoc_diagnostics"]),
        ("aggregate boundary", d["public_boundary"]["aggregate_only"] and not d["public_boundary"]["raw_ids_published"]),
        ("graph-only block forbidden", d["public_boundary"]["graph_auto_block_allowed"] is False),
    ]
    return checks


def main() -> int:
    checks = validate()
    failed = [name for name, ok in checks if not ok]
    print(f"Part 6 public validator: {len(checks) - len(failed)} PASS / {len(failed)} FAIL")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
