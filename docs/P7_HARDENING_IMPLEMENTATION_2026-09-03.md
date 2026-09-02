# Block E / Part 7 — Hardening implementation

## Scope

This update implements the research-grounded hardening plan dated 2026-09-03. The attached plan is an implementation specification; it is not evidence that a frozen Part 5 score exists or that a final policy has been locked.

## Implemented

- Causal review queue with UTC day buckets, local bucket capacity, deterministic priority/tie-breaks, explicit overflow and no carryover.
- `src/part7/decision_runtime.py` and `src/part7/evaluation_runtime.py` with a physical label/outcome boundary.
- Validation-only calibration audit. Part 7 never fits a calibrator.
- Formal action precedence and temporal scope contracts in `config/part7/`.
- Private input-lineage and opt-in row-level decision-trace schemas. The trace remains git-ignored because it can be large.
- Aggregate queue diagnostics: capacity, utilization, overflow and SLA proxy reports.
- Expanded freeze fields: full config bundle hash, code-tree hash, score hash/version, graph hash/version and mutation flag.
- Final bootstrap default is 1,000 weekly paired draws; fewer than 500 draws is rejected.
- Evidence-backed 64-gate validator. Every gate records an artifact, artifact hash, expected condition and observed value. Lifecycle status cannot auto-pass evidence gates.
- Causal queue, future-invariance, label-firewall, runtime-boundary and 64-gate tests.

## Current evidence boundary

The exact frozen Part 5 row-level score artifact is still absent from the repository. Therefore the executable status remains:

```text
INPUT_BLOCKED
```

This is intentional. Policy search, freeze, final OOT replay and `DECISION_POLICY_LOCKED` are not valid until the approved score artifact and its lineage are supplied.

## Validation

```text
13 Part 7 tests: PASS
64 evidence gates: 27 PASS / 37 BLOCKED / 0 FAIL while upstream input is missing
```

The 27 passing gates cover code/config governance that can be verified without row-level data. The blocked gates require the frozen score, execution artifacts, freeze record or final replay outputs.

## Data boundary

No raw transactions, row-level predictions, model files or private parquet artifacts are committed. Public reports remain aggregate-only. Use `--emit-private-trace` only when an approved private handoff destination is available.
