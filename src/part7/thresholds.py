from __future__ import annotations

import numpy as np
import pandas as pd


def quantile_thresholds(score: pd.Series, quantiles: list[float]) -> list[float]:
    values = pd.to_numeric(score, errors="raise").to_numpy(dtype=float)
    if len(values) == 0:
        return []
    return sorted({round(float(x), 10) for x in np.quantile(values, quantiles) if np.isfinite(x)})


def high_amount_cutoff(frame: pd.DataFrame) -> float:
    values = frame.positive_exposure.astype(float)
    return float(values.quantile(0.90)) if len(values) else 0.0
