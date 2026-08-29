/* Part 2 — Storage benchmark. Input: audit.storage_benchmark. Output: benchmark evidence. Grain: one row per storage layer. Claim: OBSERVED. */
SELECT * FROM audit.storage_benchmark ORDER BY layer;
