from __future__ import annotations

from pathlib import Path

import pandas as pd


GRAPH_FIELDS = ("pair_new", "cold_card", "new_merchant", "cross_community")


def graph_weights_from_config(config: dict) -> dict[str, float]:
    """Parse the sole source of graph review-priority weights."""
    override = config.get("automatic_block_override", {})
    if bool(override.get("enabled", False)):
        raise ValueError("Graph automatic block override must remain disabled")
    priority = config.get("review_priority")
    if not isinstance(priority, dict) or not priority:
        raise ValueError("Graph review_priority configuration is required")
    unknown = sorted(set(priority) - set(GRAPH_FIELDS))
    if unknown:
        raise ValueError(f"Unknown graph review-priority field(s): {unknown}")
    weights: dict[str, float] = {}
    for field, spec in priority.items():
        if not isinstance(spec, dict) or "enabled" not in spec:
            raise ValueError(f"Graph field {field} must declare enabled and weight")
        if "weight" not in spec:
            raise ValueError(f"Graph field {field} is missing weight")
        weight = float(spec["weight"])
        if weight <= 0:
            raise ValueError(f"Graph field {field} weight must be > 0")
        if bool(spec["enabled"]):
            weights[field] = weight
    return weights


def load_graph_weights(path: Path) -> dict[str, float]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required for graph routing configuration") from exc
    return graph_weights_from_config(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def graph_overlay_priority(frame: pd.DataFrame, base_priority: pd.Series, weights: dict[str, float]) -> pd.Series:
    """Apply only to REVIEW priority; never to BLOCK eligibility."""
    unknown = sorted(set(weights) - set(GRAPH_FIELDS))
    if unknown:
        raise ValueError(f"Unknown graph review-priority field(s): {unknown}")
    if any(float(weight) <= 0 for weight in weights.values()):
        raise ValueError("Graph review-priority weights must be > 0")
    factor = pd.Series(1.0, index=frame.index, dtype=float)
    for field, weight in weights.items():
        if field in frame:
            factor = factor.where(~frame[field].fillna(False).astype(bool), factor * float(weight))
    return base_priority * factor
