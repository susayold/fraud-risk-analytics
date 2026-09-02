from __future__ import annotations

import pandas as pd

from .contracts import PolicyConfig
from .economics import EconomicAssumptions, evaluate_economics
from .policy_engine import run_policy


def evaluate_variants(frame: pd.DataFrame, thresholds: list[float], capacities: list[float], assumptions: EconomicAssumptions, calibrated_probability: bool, high_amount_cutoff: float, max_threshold_pairs: int = 6) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows: list[dict] = []
    actions: dict[str, pd.DataFrame] = {}
    pairs = [(review, block) for review in thresholds for block in thresholds if review < block < 1]
    if len(pairs) > max_threshold_pairs:
        positions = pd.Series(range(len(pairs))).sample(n=max_threshold_pairs, random_state=20260903).sort_values().tolist()
        pairs = [pairs[i] for i in positions]
    for review_threshold, block_threshold in pairs:
            for capacity in capacities:
                tasks = [("P2", "SCORE_ONLY", 1.0), ("P3", "SCORE_ONLY", capacity), ("P4", "EXPOSURE_WEIGHTED_PROBABILITY" if calibrated_probability else "EXPOSURE_WEIGHTED_RANK", capacity), ("P4", "SCORE_ONLY", capacity), ("P5", "GRAPH_NOVELTY", capacity), ("P5", "AMOUNT_GRAPH", capacity)]
                for variant, method, task_capacity in tasks:
                        if variant == "P2":
                            config = PolicyConfig(f"PART7_{variant}_{review_threshold:.6f}_{block_threshold:.6f}", review_threshold, block_threshold, task_capacity, method)
                        elif variant == "P3":
                            config = PolicyConfig(f"PART7_{variant}_{review_threshold:.6f}_{block_threshold:.6f}_{capacity:.4f}", review_threshold, block_threshold, task_capacity, method)
                        elif variant == "P4":
                            config = PolicyConfig(f"PART7_{variant}_{review_threshold:.6f}_{block_threshold:.6f}_{capacity:.4f}_{method}", review_threshold, block_threshold, task_capacity, method)
                        else:
                            config = PolicyConfig(f"PART7_{variant}_{review_threshold:.6f}_{block_threshold:.6f}_{capacity:.4f}_{method}", review_threshold, block_threshold, task_capacity, method)
                        action_frame, metrics = run_policy(frame, config, assumptions, calibrated_probability, emit_reason_codes=False)
                        metrics["variant"] = variant
                        metrics["high_amount_cutoff"] = high_amount_cutoff
                        key = config.policy_version
                        if len(frame) <= 100_000:
                            actions[key] = action_frame
                        rows.append(metrics)
    # P0 has no thresholds and is the transparent no-intervention comparator.
    p0 = frame.copy()
    p0["action"] = "ALLOW"; p0["candidate_action"] = "ALLOW"; p0["review_priority"] = 0.0; p0["reason_codes"] = ""
    p0_metrics = evaluate_economics(p0, assumptions)
    p0_metrics.update({"policy_version": "PART7_P0_ALLOW_ALL", "priority_method": "SCORE_ONLY", "review_threshold": None, "block_threshold": None, "review_capacity": 0.0, "variant": "P0", "feasible": True, "high_amount_cutoff": high_amount_cutoff})
    rows.insert(0, p0_metrics); actions["PART7_P0_ALLOW_ALL"] = p0
    return pd.DataFrame(rows), actions


def select_policy(candidates: pd.DataFrame, profile: dict, objective: str) -> pd.Series | None:
    if candidates.empty:
        return None
    frame = candidates.copy()
    frame["feasible"] = (frame.review_rate <= float(profile["max_review_rate"])) & (frame.block_rate <= float(profile["max_block_rate"])) & (frame.legitimate_block_rate <= float(profile["max_legitimate_block_rate"]))
    frame = frame[frame.feasible]
    if frame.empty:
        return None
    if objective == "minimize_friction":
        return frame.sort_values(["legitimate_intervention_rate", "simulated_total_cost", "review_rate", "block_rate"], kind="mergesort").iloc[0]
    if objective == "maximize_protection_subject_to_constraints":
        return frame.sort_values(["fraud_exposure_capture", "fraud_capture", "simulated_total_cost"], ascending=[False, False, True], kind="mergesort").iloc[0]
    return frame.sort_values(["simulated_total_cost", "legitimate_block_rate", "review_rate", "fraud_exposure_capture"], ascending=[True, True, True, False], kind="mergesort").iloc[0]
