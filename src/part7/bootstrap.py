from __future__ import annotations

import numpy as np
import pandas as pd

from .economics import EconomicAssumptions, evaluate_economics


def weekly_paired_bootstrap(frame: pd.DataFrame, champion: pd.DataFrame, challenger: pd.DataFrame, assumptions: EconomicAssumptions, draws: int = 200, seed: int = 20260903) -> pd.DataFrame:
    if len(frame) == 0:
        return pd.DataFrame()
    dates = pd.to_datetime(frame.transaction_timestamp).dt.to_period("W").astype(str)
    blocks = sorted(dates.unique())
    rng = np.random.default_rng(seed)
    values = []
    for draw in range(draws):
        selected = rng.choice(blocks, size=len(blocks), replace=True)
        indices = np.concatenate([np.flatnonzero(dates.to_numpy() == block) for block in selected])
        base = frame.iloc[indices].copy(); c = champion.iloc[indices].copy(); h = challenger.iloc[indices].copy()
        m_c = evaluate_economics(c.assign(fraud_label=base.fraud_label.to_numpy()), assumptions)
        m_h = evaluate_economics(h.assign(fraud_label=base.fraud_label.to_numpy()), assumptions)
        values.append({"draw": draw, "delta_cost": m_h["simulated_total_cost"] - m_c["simulated_total_cost"], "delta_capture": (m_h["fraud_capture"] or 0) - (m_c["fraud_capture"] or 0), "delta_exposure_capture": (m_h["fraud_exposure_capture"] or 0) - (m_c["fraud_exposure_capture"] or 0), "delta_legitimate_intervention": m_h["legitimate_intervention_rate"] - m_c["legitimate_intervention_rate"]})
    result = pd.DataFrame(values)
    rows = []
    for metric in ["delta_cost", "delta_capture", "delta_exposure_capture", "delta_legitimate_intervention"]:
        rows.append({"metric": metric, "draws": len(result), "estimate": float(result[metric].mean()), "ci_lower": float(result[metric].quantile(0.025)), "ci_upper": float(result[metric].quantile(0.975)), "method": "weekly_paired_block_bootstrap", "seed": seed, "status": "PASS"})
    return pd.DataFrame(rows)
