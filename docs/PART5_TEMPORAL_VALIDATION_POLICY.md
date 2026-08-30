# Part 5 temporal validation policy

Official chronological splits remain Development, Validation and
Out-of-Time (OOT). Hyperparameter tuning uses three expanding temporal folds
inside Development only. Every fold enforces `max(train_timestamp) <
min(validation_timestamp)`.

The resource-safe evaluation window is the final 365 calendar days of
Validation and the final 365 calendar days of OOT. Validation is split
chronologically into calibration and selection periods when enough rows exist.
OOT is not accessed during the first P5.1 sprint and cannot be used for tuning.
