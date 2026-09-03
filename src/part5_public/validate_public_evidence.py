from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate() -> list[tuple[str, bool]]:
    final = json.loads((ROOT / "assets/data/part5_final_summary.json").read_text(encoding="utf-8"))
    selection = json.loads((ROOT / "assets/data/part5_model_selection.json").read_text(encoding="utf-8"))
    calibration = json.loads((ROOT / "assets/data/part5_calibration.json").read_text(encoding="utf-8"))
    topk = json.loads((ROOT / "assets/data/part5_topk.json").read_text(encoding="utf-8"))
    checks = [
        ("locked status", final["status"] == "PART5_MODELING_LOCKED"),
        ("all C00-C10 pass", final["pipeline"]["all_blocks_pass"] and len(final["pipeline"]["completed_blocks"]) == 11),
        ("champion frozen", final["champion"]["version"] == "FRAUD_CHAMPION_v1" and final["champion"]["frozen"]),
        ("freeze before OOT labels", final["champion"]["frozen_before_oot_label_open"]),
        ("no OOT retuning", final["champion"]["oot_used_for_retuning"] is False),
        ("validation PR-AUC present", final["validation"]["metrics"]["pr_auc"] > 0),
        ("OOT metrics present", final["oot"]["metrics"]["pr_auc"] > 0 and final["oot"]["rows"] > 0),
        ("leaderboard present", len(selection["rows"]) >= 7 and selection["rows"][0]["model"] == "BlendTop3_Equal"),
        ("calibration summary present", calibration["metrics"]["brier"] > 0 and calibration["metrics"]["log_loss"] > 0),
        ("no synthetic calibration bins", calibration["bins"] == []),
        ("top-k present", len(topk["rows"]) == 5 and topk["rows"][1]["fraud_rows"] == 594),
        ("PR curve boundary explicit", final["governance"]["pr_curve_points"] == "NOT_RETAINED"),
        ("uncertainty caveat explicit", final["governance"]["ap_bootstrap_ci_published"] is False),
        ("no raw IDs in public JSON", all("raw_id" not in json.dumps(x).lower() for x in (final, selection, calibration, topk))),
    ]
    return checks


def main() -> int:
    checks = validate()
    failed = [name for name, ok in checks if not ok]
    print(f"Part 5 public validator: {len(checks) - len(failed)} PASS / {len(failed)} FAIL")
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
