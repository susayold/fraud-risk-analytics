from __future__ import annotations

import numpy as np
import pandas as pd

from .economics import EconomicAssumptions


_METRICS = (
    "delta_cost",
    "delta_capture",
    "delta_exposure_capture",
    "delta_legitimate_block_rate",
    "delta_review_rate",
    "delta_legitimate_intervention",
)


def _policy_week_stats(
    frame: pd.DataFrame,
    actions: pd.DataFrame,
    assumptions: EconomicAssumptions,
    block_codes: np.ndarray,
    block_count: int,
) -> np.ndarray:
    """Aggregate sufficient statistics used by the economics metrics once per week."""
    y = frame.fraud_label.astype(np.int8).to_numpy()
    if "positive_exposure" in actions:
        x = actions.positive_exposure.astype(float).to_numpy()
    else:
        x = frame.positive_exposure.astype(float).to_numpy()
    action = actions.action.astype(str).to_numpy()

    fraud = y == 1
    legit = ~fraud
    allow = action == "ALLOW"
    review = action == "REVIEW"
    block = action == "BLOCK"

    missed = x * assumptions.fraud_loss_fraction
    allow_cost = np.where(allow & fraud, missed, 0.0)
    block_cost = (
        np.where(block & fraud, missed * (1 - assumptions.block_effectiveness), 0.0)
        + np.where(
            block & legit,
            assumptions.false_block_fixed_friction_cost
            + x * assumptions.false_block_amount_friction_rate,
            0.0,
        )
    )
    review_cost = np.where(
        review,
        assumptions.review_cost_per_case + assumptions.review_delay_cost,
        0.0,
    )
    review_cost += np.where(
        review & fraud,
        missed * (1 - assumptions.review_fraud_detection_rate),
        0.0,
    )
    review_cost += np.where(
        review & legit,
        assumptions.review_legitimate_false_reject_rate
        * (
            assumptions.false_block_fixed_friction_cost
            + x * assumptions.false_block_amount_friction_rate
        ),
        0.0,
    )

    row_stats = np.column_stack(
        [
            np.ones(len(frame), dtype=np.float64),
            fraud.astype(np.float64),
            legit.astype(np.float64),
            allow_cost + block_cost + review_cost,
            (allow & fraud).astype(np.float64),
            np.where(allow & fraud, x, 0.0),
            np.where(fraud, x, 0.0),
            ((review | block) & legit).astype(np.float64),
            (block & legit).astype(np.float64),
            review.astype(np.float64),
        ]
    )

    out = np.empty((block_count, row_stats.shape[1]), dtype=np.float64)
    for col in range(row_stats.shape[1]):
        out[:, col] = np.bincount(
            block_codes,
            weights=row_stats[:, col],
            minlength=block_count,
        )
    return out


def _draw_metrics(aggregated: np.ndarray) -> tuple[np.ndarray, ...]:
    n = aggregated[:, 0]
    fraud_n = aggregated[:, 1]
    legit_n = aggregated[:, 2]
    total_cost = aggregated[:, 3]
    fraud_allowed_n = aggregated[:, 4]
    allowed_fraud_exposure = aggregated[:, 5]
    fraud_exposure = aggregated[:, 6]
    legit_intervention_n = aggregated[:, 7]
    legit_block_n = aggregated[:, 8]
    review_n = aggregated[:, 9]

    fraud_capture = np.divide(
        fraud_n - fraud_allowed_n,
        fraud_n,
        out=np.zeros_like(fraud_n),
        where=fraud_n != 0,
    )
    fraud_exposure_capture = np.divide(
        fraud_exposure - allowed_fraud_exposure,
        fraud_exposure,
        out=np.zeros_like(fraud_exposure),
        where=fraud_exposure != 0,
    )
    legitimate_intervention_rate = np.divide(
        legit_intervention_n,
        n,
        out=np.zeros_like(n),
        where=n != 0,
    )
    legitimate_block_rate = np.divide(
        legit_block_n,
        legit_n,
        out=np.zeros_like(legit_n),
        where=legit_n != 0,
    )
    review_rate = np.divide(
        review_n,
        n,
        out=np.zeros_like(n),
        where=n != 0,
    )

    return (
        total_cost,
        fraud_capture,
        fraud_exposure_capture,
        legitimate_intervention_rate,
        legitimate_block_rate,
        review_rate,
    )


def weekly_paired_bootstrap(
    frame: pd.DataFrame,
    champion: pd.DataFrame,
    challenger: pd.DataFrame,
    assumptions: EconomicAssumptions,
    draws: int = 1000,
    seed: int = 20260903,
) -> pd.DataFrame:
    """Exact weekly paired block bootstrap using week-level sufficient statistics.

    Statistical design is unchanged from the original implementation: the same
    weekly blocks are sampled with replacement using the same seed. The execution
    optimization aggregates each row once instead of repeatedly copying the full
    row-level frame for every draw.
    """
    if draws < 500:
        raise ValueError("Final weekly paired bootstrap requires at least 500 draws")
    if len(frame) == 0:
        return pd.DataFrame()

    dates = (
        pd.to_datetime(frame.transaction_timestamp, utc=True)
        .dt.tz_convert(None)
        .dt.to_period("W")
        .astype(str)
    )
    blocks = sorted(dates.unique())
    block_to_code = {block: i for i, block in enumerate(blocks)}
    block_codes = np.fromiter(
        (block_to_code[value] for value in dates.to_numpy()),
        dtype=np.int32,
        count=len(dates),
    )
    n_blocks = len(blocks)

    champion_stats = _policy_week_stats(frame, champion, assumptions, block_codes, n_blocks)
    challenger_stats = _policy_week_stats(frame, challenger, assumptions, block_codes, n_blocks)

    rng = np.random.default_rng(seed)
    counts = np.zeros((draws, n_blocks), dtype=np.int16)
    block_ids = np.arange(n_blocks)
    for draw in range(draws):
        selected = rng.choice(block_ids, size=n_blocks, replace=True)
        counts[draw] = np.bincount(selected, minlength=n_blocks)

    champion_draws = counts @ champion_stats
    challenger_draws = counts @ challenger_stats
    c = _draw_metrics(champion_draws)
    h = _draw_metrics(challenger_draws)

    result = pd.DataFrame(
        {
            "draw": np.arange(draws),
            "delta_cost": h[0] - c[0],
            "delta_capture": h[1] - c[1],
            "delta_exposure_capture": h[2] - c[2],
            "delta_legitimate_intervention": h[3] - c[3],
            "delta_legitimate_block_rate": h[4] - c[4],
            "delta_review_rate": h[5] - c[5],
        }
    )

    rows = []
    for metric in _METRICS:
        rows.append(
            {
                "metric": metric,
                "draws": len(result),
                "estimate": float(result[metric].mean()),
                "ci_lower": float(result[metric].quantile(0.025)),
                "ci_upper": float(result[metric].quantile(0.975)),
                "method": "weekly_paired_block_bootstrap",
                "seed": seed,
                "status": "PASS",
            }
        )
    return pd.DataFrame(rows)
