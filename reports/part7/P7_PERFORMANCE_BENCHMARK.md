# Part 7 policy performance benchmark

This is an offline, single-policy, in-memory benchmark. It is not a production latency or SLA claim, and it does not write row-level benchmark data.

## Environment

- Platform: Windows 10 (10.0.19045)
- Python: 3.14.2
- pandas: 2.3.3
- NumPy: 2.4.4
- Queue: UTC day bucket, 1% fraction capacity

## Results

| rows | runtime (s) | rows/s | peak Python memory (MB) |
|---:|---:|---:|---:|
| 100,000 | 3.4969 | 28,596.72 | 29.60 |
| 500,000 | 16.3884 | 30,509.38 | 149.19 |
| 1,000,000 | 32.2397 | 31,017.62 | 290.20 |

## Interpretation

The current implementation is suitable for a controlled offline single-policy pass, but the full Tune + Confirm grid is approximately 504 policy evaluations. Full-population execution should therefore be benchmarked on the target machine before ingesting the real score. If the full grid is too expensive, use the plan's two-stage search: shortlist with P0–P3, then run P4/P5 only in the shortlisted operational region.
