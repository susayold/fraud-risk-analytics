from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import duckdb
import pandas as pd

from common import REPORT_DIR, SEED, sha256_file, write_csv

SCOPE_FIELDS = ["scope", "date_start", "date_end", "rows", "fraud_rows", "legitimate_rows", "natural_prevalence", "sampling_method", "sample_ratio", "weighted"]


def relation_exists(db: duckdb.DuckDBPyConnection, name: str) -> bool:
    schema, table = name.split(".", 1)
    return bool(db.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=? AND table_name=?", [schema, table]).fetchone()[0]) or bool(db.execute("SELECT COUNT(*) FROM information_schema.views WHERE table_schema=? AND table_name=?", [schema, table]).fetchone()[0])


def build_population(db_path: Path, private_dir: Path, report_dir: Path = REPORT_DIR, seed: int = SEED) -> dict:
    private_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(db_path), read_only=True)
    try:
        if not relation_exists(db, "analytics.part4_evaluation_v1"):
            raise RuntimeError("analytics.part4_evaluation_v1 is unavailable; run the locked Part 4 PIT build first")
        db.execute("""
        CREATE OR REPLACE TEMP VIEW p5_source AS
        SELECT source_row_id, transaction_timestamp, split_name, fraud_label
        FROM analytics.part4_evaluation_v1
        """)
        db.execute(f"""
        CREATE OR REPLACE TEMP VIEW p5_target_scope AS
        WITH quarter_counts AS (
          SELECT date_trunc('quarter', transaction_timestamp) AS quarter_start,
                 COUNT(*) FILTER (WHERE fraud_label=1) AS fraud_rows
          FROM p5_source WHERE split_name='DEVELOPMENT' GROUP BY 1
        ), ranked_negatives AS (
          SELECT s.source_row_id,
                 ROW_NUMBER() OVER (
                   PARTITION BY date_trunc('quarter', s.transaction_timestamp)
                   ORDER BY md5(CAST(s.source_row_id AS VARCHAR) || ':{seed}')
                 ) AS hash_rank,
                 q.fraud_rows
          FROM p5_source s
          JOIN quarter_counts q ON q.quarter_start=date_trunc('quarter', s.transaction_timestamp)
          WHERE s.split_name='DEVELOPMENT' AND s.fraud_label=0
        ), development_train AS (
          SELECT source_row_id, 'DEVELOPMENT_TRAIN' AS modeling_scope
          FROM p5_source WHERE split_name='DEVELOPMENT' AND fraud_label=1
          UNION ALL
          SELECT source_row_id, 'DEVELOPMENT_TRAIN' AS modeling_scope
          FROM ranked_negatives WHERE hash_rank <= 20 * GREATEST(fraud_rows, 1)
        ), validation_window AS (
          SELECT source_row_id,
                 CASE WHEN transaction_timestamp < (SELECT MIN(transaction_timestamp) + INTERVAL '182 days' FROM p5_source WHERE split_name='VALIDATION')
                      THEN 'VALIDATION_CALIBRATION' ELSE 'VALIDATION_SELECTION' END AS modeling_scope
          FROM p5_source
          WHERE split_name='VALIDATION'
            AND transaction_timestamp >= (SELECT MAX(transaction_timestamp) - INTERVAL '365 days' FROM p5_source WHERE split_name='VALIDATION')
        ), oot_window AS (
          SELECT source_row_id, 'OOT_EVALUATION_WINDOW' AS modeling_scope
          FROM p5_source
          WHERE split_name='OUT_OF_TIME_OOT'
            AND transaction_timestamp >= (SELECT MAX(transaction_timestamp) - INTERVAL '365 days' FROM p5_source WHERE split_name='OUT_OF_TIME_OOT')
        )
        SELECT * FROM development_train
        UNION ALL SELECT * FROM validation_window
        UNION ALL SELECT * FROM oot_window
        """)
        manifest = db.execute("""
        SELECT t.source_row_id, t.modeling_scope, s.transaction_timestamp, s.split_name, s.fraud_label
        FROM p5_target_scope t JOIN p5_source s USING(source_row_id)
        ORDER BY s.transaction_timestamp, t.source_row_id
        """).df()
        private_manifest = private_dir / "target_manifest.csv"
        manifest.to_csv(private_manifest, index=False)
        manifest_hash = sha256_file(private_manifest)
        (private_dir / "target_manifest.sha256").write_text(manifest_hash + "\n", encoding="utf-8")
        agg = []
        for scope, group in manifest.groupby("modeling_scope", sort=True):
            agg.append({"scope": scope, "date_start": group.transaction_timestamp.min(), "date_end": group.transaction_timestamp.max(), "rows": len(group), "fraud_rows": int(group.fraud_label.sum()), "legitimate_rows": int((group.fraud_label == 0).sum()), "natural_prevalence": float(group.fraud_label.mean()), "sampling_method": "all_fraud_plus_deterministic_quarter_hash_20_to_1" if scope == "DEVELOPMENT_TRAIN" else "fixed_calendar_window_natural_prevalence", "sample_ratio": 20 if scope == "DEVELOPMENT_TRAIN" else None, "weighted": scope == "DEVELOPMENT_TRAIN"})
        write_csv(report_dir / "modeling_scope.csv", agg, SCOPE_FIELDS)
        full_dev_legit = int(db.execute("SELECT COUNT(*) FROM p5_source WHERE split_name='DEVELOPMENT' AND fraud_label=0").fetchone()[0])
        sampled_dev_legit = int((manifest.modeling_scope == "DEVELOPMENT_TRAIN").sum() - (manifest.loc[manifest.modeling_scope == "DEVELOPMENT_TRAIN", "fraud_label"] == 1).sum())
        meta = {"manifest_path": str(private_manifest), "manifest_sha256": manifest_hash, "full_development_legitimate_rows": full_dev_legit, "sampled_development_legitimate_rows": sampled_dev_legit, "rows": len(manifest)}
        return meta
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    args = parser.parse_args()
    print(build_population(args.database, args.private_dir))


if __name__ == "__main__":
    main()
