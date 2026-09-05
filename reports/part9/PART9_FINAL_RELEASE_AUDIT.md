# Part 9 Evidence, Methodology & Audit Release

`PRESENTATION_READY` means the recruiter-facing evidence room, registries, claim boundaries and release checks are complete. It does not mean every upstream technical execution has completed.

## Current release interpretation

- Presentation release gates: `40 / 40 PASS`.
- Part 2 foundation, Part 3 portfolio, Part 4 behavioral registry, Part 5 model aggregate evidence and Part 6 graph aggregate evidence are available from their governed public artifacts.
- Part 5 PR-curve coordinates remain `NOT_RETAINED`; the page does not reconstruct them.
- Part 7 source file is available, but its execution status remains `INPUT_BLOCKED` (`30 / 64 PASS`).
- Part 8 source file is available, but its execution status remains `INPUT_BLOCKED` (`20 / 72 PASS`).
- Part 7/8 are not converted into zero, green or locked outcomes when evidence is unavailable.
- All chart containers and audit views expose status, source, claim class and accessible fallback text.

## Public boundary

Only aggregate counts, metrics, versions, hashes, methodology and status evidence are published. Row-level transaction data, scores, labels, decisions, raw graph edges, embeddings, model binaries and private decision marts remain outside the public repository.
- Public JSON is aggregate-only; no raw transaction or graph rows are shipped.
- Desktop, tablet and mobile layouts are covered by responsive CSS, and reduced motion is supported.

The website is intentionally evidence-rich for available layers and explicit about blocked dependencies for conditional layers.
