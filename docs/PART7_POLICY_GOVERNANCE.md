# Part 7 policy governance

Execution modes are `BACKTEST`, `SHADOW`, and `FROZEN_REPLAY`. `ACTIVE` is future architecture only and is never claimed by this project.

The chronology is: discover and audit input → build decision mart → label firewall → probability gate → tune → confirm → freeze → final replay. Once `PART7_POLICY_FREEZE.json` exists, thresholds, capacity, assumptions, graph routing, and profile cannot change for the final replay. Every public artifact receives a SHA-256 manifest entry.

The final status can be `DECISION_POLICY_LOCKED` only if all 64 mandatory gates pass. Missing upstream evidence results in `INPUT_BLOCKED`.
