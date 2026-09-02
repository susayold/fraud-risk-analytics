from __future__ import annotations

import numpy as np
import pandas as pd


def add_exposure_bases(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    amount = pd.to_numeric(result["amount"], errors="raise").to_numpy(dtype=float)
    result["signed_amount"] = amount
    result["positive_exposure"] = np.maximum(amount, 0.0)
    result["absolute_exposure"] = np.abs(amount)
    result["economic_exposure_proxy"] = result["positive_exposure"]
    return result


def exposure_column(basis: str) -> str:
    mapping = {"signed_amount": "signed_amount", "positive_exposure": "positive_exposure", "absolute_exposure": "absolute_exposure"}
    if basis not in mapping:
        raise ValueError(f"Unknown exposure basis: {basis}")
    return mapping[basis]
