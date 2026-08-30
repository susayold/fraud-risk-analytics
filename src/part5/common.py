from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "reports" / "part5"
SUMMARY_PATH = ROOT / "assets" / "data" / "part5_summary.json"
CONFIG_PATH = ROOT / "config" / "part5_modeling.yml"
MODEL_CONTRACT_VERSION = "PART5_v1.0"
CALIBRATION_CONTRACT_VERSION = "P5_CALIBRATION_v1.0"
FRONTEND_CONTRACT_VERSION = "P5_FRONTEND_v1.0"
SEED = 20260830

CURRENT_FEATURES = ["amount", "use_chip", "merchant_category_code", "state_missing_flag"]
FORBIDDEN_FEATURE_TOKENS = (
    "fraud_label", "source_row_id", "user_id", "card_key", "merchant_id_raw",
    "split_name", "chargeback", "investigation", "post_event", "future_",
)
TOP_K = (0.005, 0.01, 0.02, 0.05, 0.10)


def load_behavioral_features() -> list[str]:
    registry = pd.read_csv(ROOT / "docs" / "PART4_FEATURE_REGISTRY.csv")
    return registry["feature_name"].astype(str).tolist()


def feature_sets() -> dict[str, list[str]]:
    behavioral = load_behavioral_features()
    return {
        "F0": CURRENT_FEATURES,
        "F1": behavioral,
        "F2": CURRENT_FEATURES + [x for x in behavioral if x not in CURRENT_FEATURES],
    }


def json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    raise TypeError(f"Cannot serialize {type(value)!r}")


def write_csv(path: Path, rows: Iterable[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(list(rows))
    if fields:
        frame = frame.reindex(columns=fields)
    frame.to_csv(path, index=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_preprocessor(frame: pd.DataFrame, features: list[str]) -> ColumnTransformer:
    categorical = [x for x in features if x in {"use_chip", "merchant_category_code"}]
    numeric = [x for x in features if x not in categorical]
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # scikit-learn < 1.2
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", encoder),
    ])
    transformers = []
    if numeric:
        transformers.append(("numeric", numeric_pipe, numeric))
    if categorical:
        transformers.append(("categorical", categorical_pipe, categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def assert_feature_contract(frame: pd.DataFrame, features: list[str]) -> None:
    missing = sorted(set(features) - set(frame.columns))
    if missing:
        raise ValueError(f"Feature columns missing from Part 4 evaluation view: {missing}")
    forbidden = sorted({feature for feature in features for token in FORBIDDEN_FEATURE_TOKENS if token in feature.lower()})
    if forbidden:
        raise ValueError(f"Forbidden model inputs detected: {forbidden}")


def sample_weights(y: pd.Series, full_legitimate: int, sampled_legitimate: int) -> np.ndarray:
    if sampled_legitimate <= 0 or full_legitimate < sampled_legitimate:
        raise ValueError("Invalid Development legitimate counts for sample weighting")
    weight = max(1.0, full_legitimate / sampled_legitimate)
    return np.where(y.to_numpy(dtype=int) == 0, weight, 1.0)


def temporal_fold_masks(frame: pd.DataFrame, folds: int = 3) -> list[tuple[np.ndarray, np.ndarray, dict]]:
    timestamps = pd.to_datetime(frame["transaction_timestamp"], utc=False)
    unique_dates = np.array(sorted(timestamps.dt.normalize().dropna().unique()))
    if len(unique_dates) < folds + 1:
        raise ValueError("Not enough distinct Development dates for temporal CV")
    result = []
    for fold in range(folds):
        train_end_idx = max(0, int(round(len(unique_dates) * (0.50 + fold * 0.15))) - 1)
        valid_start_idx = train_end_idx + 1
        valid_end_idx = len(unique_dates) - 1 if fold == folds - 1 else max(valid_start_idx, int(round(len(unique_dates) * (0.65 + fold * 0.15))) - 1)
        train_end = pd.Timestamp(unique_dates[train_end_idx])
        valid_start = pd.Timestamp(unique_dates[valid_start_idx])
        valid_end = pd.Timestamp(unique_dates[valid_end_idx])
        train_mask = (timestamps.dt.normalize() <= train_end).to_numpy()
        valid_mask = ((timestamps.dt.normalize() >= valid_start) & (timestamps.dt.normalize() <= valid_end)).to_numpy()
        result.append((train_mask, valid_mask, {
            "fold": fold + 1,
            "train_end": train_end.date().isoformat(),
            "validation_start": valid_start.date().isoformat(),
            "validation_end": valid_end.date().isoformat(),
            "chronology_pass": train_end < valid_start,
        }))
    return result


def safe_binary_metrics(y: np.ndarray, score: np.ndarray, probability: np.ndarray | None = None) -> dict:
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    result = {"rows": int(len(y)), "fraud_rows": int(y.sum()), "pr_auc": None, "roc_auc": None, "ks": None, "brier": None, "log_loss": None}
    if len(np.unique(y)) < 2:
        return result
    result["pr_auc"] = float(average_precision_score(y, score))
    result["roc_auc"] = float(roc_auc_score(y, score))
    positives = np.sort(score[y == 1]); negatives = np.sort(score[y == 0])
    values = np.unique(score)
    result["ks"] = float(max(abs((positives[:, None] <= values).mean(axis=0) - (negatives[:, None] <= values).mean(axis=0))))
    if probability is not None:
        probability = np.clip(np.asarray(probability, dtype=float), 1e-9, 1 - 1e-9)
        result["brier"] = float(np.mean((probability - y) ** 2))
        result["log_loss"] = float(log_loss(y, probability, labels=[0, 1]))
    return result


def topk_rows(y: np.ndarray, score: np.ndarray, top_k: tuple[float, ...] = TOP_K) -> list[dict]:
    y = np.asarray(y, dtype=int); score = np.asarray(score, dtype=float)
    order = np.argsort(-score, kind="mergesort")
    total_fraud = int(y.sum())
    rows = []
    for fraction in top_k:
        selected = max(1, int(np.ceil(len(y) * fraction))) if len(y) else 0
        chosen = y[order[:selected]] if selected else np.array([], dtype=int)
        fraud_captured = int(chosen.sum())
        rows.append({"top_k": fraction, "selected_rows": selected, "fraud_captured": fraud_captured,
                     "fraud_capture_rate": (fraud_captured / total_fraud) if total_fraud else None,
                     "precision": (fraud_captured / selected) if selected else None,
                     "lift": ((fraud_captured / selected) / (total_fraud / len(y))) if total_fraud and len(y) else None})
    return rows


def calibration_bins(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> list[dict]:
    frame = pd.DataFrame({"y": y, "probability": probability})
    frame["bin"] = pd.qcut(frame["probability"].rank(method="first"), q=min(bins, len(frame)), labels=False, duplicates="drop")
    result = []
    for key, group in frame.groupby("bin", dropna=False):
        result.append({"bin": int(key), "rows": int(len(group)), "mean_predicted_probability": float(group.probability.mean()), "observed_fraud_rate": float(group.y.mean())})
    return result
