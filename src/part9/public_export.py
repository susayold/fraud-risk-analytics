from __future__ import annotations


FORBIDDEN_KEYS = {"source_row_id", "transaction_id", "transaction_timestamp", "risk_score", "fraud_label", "future_outcome", "future_dispute", "action", "candidate_action", "reason_codes", "card_id", "user_id", "merchant_id", "merchant_identifier", "raw_graph_edge", "graph_edge", "review_selected", "review_overflow", "review_priority", "review_rank"}


def validate_public_payload(value, path="$", allowlist=None) -> list[str]:
    errors = []
    allowlist = allowlist or set()
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_KEYS and normalized not in allowlist:
                errors.append(f"{path}.{key}")
            errors.extend(validate_public_payload(child, f"{path}.{key}", allowlist))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(validate_public_payload(child, f"{path}[{index}]", allowlist))
    return errors
