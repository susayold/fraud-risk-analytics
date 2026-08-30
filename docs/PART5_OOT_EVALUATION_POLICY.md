# Part 5 OOT evaluation policy

OOT is a final frozen assessment, not a development set. Before OOT access,
freeze the feature set, preprocessing, model hyperparameters, calibration
method and champion-selection rule. Record each access in
`reports/part5/oot_access_log.csv` with timestamp, code commit, model version,
reason and action.

The website must label resource-safe results as an **OOT evaluation window**,
not as the entire OOT split. A rerun is permitted only for a documented
technical defect and must not become post-OOT tuning.
