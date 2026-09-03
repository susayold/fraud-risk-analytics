from __future__ import annotations

import numpy as np
from scipy.stats import chi2_contingency, ks_2samp, wasserstein_distance


EPSILON = 1e-12


def _finite(values) -> np.ndarray:
    value = np.asarray(values, dtype=float)
    return value[np.isfinite(value)]


def frozen_bins(reference, bins: int = 10) -> np.ndarray:
    values = _finite(reference)
    if values.size == 0:
        raise ValueError("Reference distribution is empty")
    edges = np.unique(np.quantile(values, np.linspace(0, 1, bins + 1)))
    if edges.size < 2:
        center = float(values[0])
        edges = np.array([center - 0.5, center + 0.5])
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges


def histogram_counts(values, bins) -> np.ndarray:
    finite = _finite(values)
    if finite.size == 0:
        return np.zeros(len(bins) - 1, dtype=float)
    return np.histogram(finite, bins=bins)[0].astype(float)


def _proportions(counts) -> np.ndarray:
    counts = np.asarray(counts, dtype=float)
    total = counts.sum()
    if total <= 0:
        return np.full_like(counts, np.nan, dtype=float)
    return (counts + EPSILON) / (total + EPSILON * len(counts))


def psi(reference, target, bins=None) -> float:
    ref = histogram_counts(reference, bins if bins is not None else frozen_bins(reference))
    cur = histogram_counts(target, bins if bins is not None else frozen_bins(reference))
    p, q = _proportions(ref), _proportions(cur)
    if np.isnan(p).any() or np.isnan(q).any():
        return float("nan")
    return float(np.sum((q - p) * np.log(q / p)))


def jensen_shannon(reference, target, bins=None) -> float:
    ref = histogram_counts(reference, bins if bins is not None else frozen_bins(reference))
    cur = histogram_counts(target, bins if bins is not None else frozen_bins(reference))
    p, q = _proportions(ref), _proportions(cur)
    if np.isnan(p).any() or np.isnan(q).any():
        return float("nan")
    midpoint = (p + q) / 2
    divergence = 0.5 * np.sum(p * np.log(p / midpoint)) + 0.5 * np.sum(q * np.log(q / midpoint))
    return float(np.sqrt(max(0.0, divergence)))


def normalized_wasserstein(reference, target) -> float:
    ref, cur = _finite(reference), _finite(target)
    if ref.size == 0 or cur.size == 0:
        return float("nan")
    scale = float(np.std(ref))
    if not np.isfinite(scale) or scale <= EPSILON:
        scale = max(float(np.ptp(ref)), 1.0)
    return float(wasserstein_distance(ref, cur) / scale)


def ks_statistic(reference, target) -> float:
    ref, cur = _finite(reference), _finite(target)
    if ref.size == 0 or cur.size == 0:
        return float("nan")
    return float(ks_2samp(ref, cur, method="auto").statistic)


def total_variation(reference_counts, target_counts) -> float:
    p, q = _proportions(reference_counts), _proportions(target_counts)
    if np.isnan(p).any() or np.isnan(q).any():
        return float("nan")
    return float(0.5 * np.abs(p - q).sum())


def psi_counts(reference_counts, target_counts) -> float:
    p, q = _proportions(reference_counts), _proportions(target_counts)
    if np.isnan(p).any() or np.isnan(q).any():
        return float("nan")
    return float(np.sum((q - p) * np.log(q / p)))


def jensen_shannon_counts(reference_counts, target_counts) -> float:
    p, q = _proportions(reference_counts), _proportions(target_counts)
    if np.isnan(p).any() or np.isnan(q).any():
        return float("nan")
    midpoint = (p + q) / 2
    divergence = 0.5 * np.sum(p * np.log(p / midpoint)) + 0.5 * np.sum(q * np.log(q / midpoint))
    return float(np.sqrt(max(0.0, divergence)))


def chi_squared_diagnostic(reference_counts, target_counts) -> float:
    ref, cur = np.asarray(reference_counts, dtype=float), np.asarray(target_counts, dtype=float)
    if ref.sum() <= 0 or cur.sum() <= 0:
        return float("nan")
    _, p_value, _, _ = chi2_contingency(np.vstack([ref + EPSILON, cur + EPSILON]))
    return float(p_value)
