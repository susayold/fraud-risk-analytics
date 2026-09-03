# Block F / Part 8 — Final Hardening Audit

Status: `FRAMEWORK_HARDENED`, genuine runtime evidence: `INPUT_BLOCKED` until the governed Part 7 decision mart is supplied.

## Implemented controls

- One governed CSV/Parquet loader validates the monitoring contract before baseline, calibration, or replay.
- The two-clock boundary is preserved: `OPERATIONS_NOW` is label-free; `OUTCOMES_MATURED` is retrospective only.
- Final replay reads frozen feature and score sufficient statistics, and never rebuilds a reference from the final OOT input.
- Threshold candidates are generated only from pre-OOT rows. Final alert values remain null until an explicit review/freeze change.
- Freeze verification checks baseline artifacts, reference hashes, threshold/config hashes, code tree, commit, lineage fields, and post-freeze mutation.
- The Part 7 adapter maps `bucket_selected → review_selected`, `overflow → review_overflow`, and `capacity_bucket → review_capacity_bucket`, with bucket-level reconciliation.
- The 72-gate validator records gate class, mandatory flag, evidence field, observed value, expected value, and blocking dependency. Lifecycle text cannot manufacture PASS.
- Public exports use an exact recursive row-level key denylist; aggregate text is allowed.
- CI includes Part 7 source/config paths because those artifacts are upstream dependencies of Part 8.

## Verification

- Part 8 test suite: 43 tests, 0 failures, 0 errors.
- Protected artifact mutation check: 0.
- Current repository validation: 20 static/framework PASS, 52 execution BLOCKED, 0 FAIL.
- No raw transaction rows, private marts, model binaries, or large data files were added to the public repository.

The remaining `BLOCKED` state is intentional and means the software is ready to consume genuine upstream evidence, not that a synthetic fixture has been promoted to production evidence.
