"""In-memory Part 7 policy benchmark; it never writes row-level data."""
from __future__ import annotations

import argparse
import platform
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.part7.contracts import PolicyConfig
from src.part7.decision_runtime import decide
from src.part7.exposure import add_exposure_bases
from src.part7.io import write_json


def make_frame(rows: int) -> pd.DataFrame:
    rng = np.random.default_rng(20260903 + rows)
    dates = pd.date_range("2026-01-01", periods=14, freq="D", tz="UTC")
    return add_exposure_bases(pd.DataFrame({
        "source_row_id": np.arange(rows, dtype=np.int64),
        "transaction_timestamp": rng.choice(dates, size=rows),
        "risk_score": rng.random(rows),
        "amount": rng.lognormal(3.0, 1.0, rows),
        "pair_new": rng.random(rows) < .1,
        "cold_card": rng.random(rows) < .05,
        "new_merchant": rng.random(rows) < .08,
        "cross_community": rng.random(rows) < .03,
    }))


def benchmark(rows: int) -> dict:
    frame = make_frame(rows)
    config = PolicyConfig(f"BENCH_{rows}", .90, .99, .01, "SCORE_ONLY")
    tracemalloc.start(); start = time.perf_counter()
    actions = decide(frame, config, False, emit_reason_codes=False)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    return {"rows": rows, "runtime_seconds": round(elapsed, 4), "rows_per_second": round(rows / elapsed, 2), "peak_python_memory_mb": round(peak / 1024 / 1024, 2), "review_candidates": int(actions.candidate_action.eq("REVIEW").sum()), "review_selected": int(actions.action.eq("REVIEW").sum()), "claim": "offline single-policy benchmark; not a production latency SLA"}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--sizes", nargs="+", type=int, default=[100_000, 500_000, 1_000_000]); args = parser.parse_args()
    results = [benchmark(size) for size in args.sizes]
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "machine": {"platform": platform.platform(), "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}, "results": results, "candidate_search_estimate": "Current full Tune+Confirm grid is approximately 504 policy evaluations; multiply single-policy measurements cautiously because cache/memory effects differ."}
    out = ROOT / "reports" / "part7" / "P7_PERFORMANCE_BENCHMARK.json"
    write_json(out, report)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
