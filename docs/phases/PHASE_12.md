# PHASE 12 — Memory Consolidation and Compression

## Objective

Investigate bounded memory for real: redundancy detection, deduplication,
importance scoring, budget enforcement, and a real (if narrow) measurement
of the size-vs-information tradeoff, rather than assuming any budget number
from the brief is sufficient.

## Assumptions

- **ASSUMPTION, stated in ROADMAP.md and repeated here**: the full
  memory-budget experiment matrix (10KB-10MB across many characters/clips)
  needs far more data than this project's 4-6 clip scenario produces to
  mean anything — not run this phase, deferred to Phase 15 prerequisites.
  What *is* buildable now is the compression *mechanism* and a test of it
  against synthetic, artificially-inflated evidence (to have something to
  compress at all).

## Subtasks

### 1. Redundancy detection

**Status**: structurally minimal already — `MemoryStore._note_clip`
(Phase 6) already prevents duplicate clip-sequence entries; canonical
state is one-value-per-attribute by construction (Phase 1 subtask 12).
The only place real redundancy accumulates is **evidence lists** (every
clip that reinforces an already-established fact appends another
`ClipRef`, unboundedly) — that's what this phase targets.

### 2. Observation deduplication

Not separately implemented — observations are transient (Phase 3), never
stored beyond what `reconcile()` writes into evidence/exceptions, so
there's nothing pre-memory to deduplicate.

### 3. State consolidation

Already the point of canonical/exception/promotion (Phases 2/5) — no
change needed.

### 4. Exception extraction

Already implemented (`exceptions`/`unexplained` lists).

### 5. Temporal compression

**Status**: not implemented — would mean collapsing old temporal
breakpoints (Phase 6) once they're old enough not to matter for future
reconstruction queries. No scenario has enough promotion events to make
this meaningful yet (the MVP scenario has at most one promotion chain in
its tests). Deferred.

### 6. Evidence compression — the real deliverable this phase

**Problem**: `CanonicalAttribute.evidence` grows by one `ClipRef` per
reinforcing clip, forever — the brief explicitly warns this can't be
allowed to grow unboundedly (Principle 4).
**Approach**: `compress_evidence(entity, max_evidence)` caps each
attribute's evidence list at `max_evidence` entries, keeping the
*first* (original establishment, for provenance of when this became true)
and the most recent `max_evidence - 1` (freshest confirming evidence) —
dropping the middle. The number of dropped entries is recorded on the
attribute (`evidence_dropped`, new field) rather than silently lost, so the
information-loss cost of compression stays visible (Phase 13 concern).
**Alternatives considered**: keep only the most recent N (simpler, but
loses "when did this attribute first get established," which matters for
provenance/audit); keep a random sample (no clear benefit over
first+recent for this use case); summarize dropped evidence into a count
only (chosen) vs. into some kind of compressed digest of what was dropped
(rejected as needless complexity — a plain count is honest about there
being no way to reconstruct the dropped entries, rather than implying a
lossy summary is nearly as good as the original).
**Recommended approach**: as implemented.

### 7. Importance scoring

**Status**: not implemented — evidence entries currently have no
distinguishing importance beyond position (first vs. most recent). A real
importance score (e.g. this clip was also where a promotion happened, so
keep it regardless of recency) is a reasonable future refinement, deferred
until compression is exercised against real, larger data where the
simple first+recent heuristic visibly falls short.

### 8. Information-loss estimation

**Implemented**: `evidence_dropped` count per attribute (subtask 6). No
deeper loss metric (e.g. "how much would consistency verification have
suffered from this dropped evidence") is computed — that requires a
larger benchmark (Phase 15) to measure meaningfully.

### 9. Memory-budget enforcement

**Implemented**: `enforce_budget(store, budget_bytes)` repeatedly shrinks
`max_evidence` (starting at a generous cap, halving) and re-measures
`store.size_bytes()` until under budget or a floor (`max_evidence=1`) is
hit — at which point it reports that the budget could not be met by
evidence-compression alone (a real, honest failure mode: some budgets are
just too small for the number of *attributes*, regardless of evidence
compression, since even one evidence entry per attribute has a floor cost).

### 10. Compression strategies

Only evidence-capping is implemented (subtask 6). The brief's other
strategies (e.g. summarizing many past deviations into one statistical
statement) aren't built — no scenario produces enough deviations to need
it (the MVP's `unexplained`/`exceptions` lists are single-digit length).

### 11. Reconstruction testing

**Implemented as a test**: after compression, the canonical *value* and
*confidence* are unchanged (compression only touches evidence provenance,
never truth) — verified directly, since this is the property that matters
most (a lossy compression that silently changed a canonical value would be
a serious bug, not an acceptable tradeoff).

### 12. Consistency-versus-size evaluation

**Not run this phase** — meaningfully evaluating "does compression hurt
consistency" requires re-running reconciliation *after* compressing
evidence and checking whether outcomes differ, across enough clips that
evidence-list depth could plausibly matter. The MVP scenario doesn't
generate enough evidence per attribute (at most 2-3 real reinforcing clips)
for compression to ever actually trigger in `run_mvp.py` as it exists
today. Recorded as an open item for Phase 15's real dataset, not
faked here with an inflated synthetic case built solely to make this box
checkable.

## Architecture Changes From Previous Phase

- `CanonicalAttribute` gains `evidence_dropped: int = 0`.
- New module `castgraph/compression/compress.py`: `compress_evidence`,
  `enforce_budget`.

## Risks

- The "keep first + most recent" heuristic is unvalidated against any real
  measure of which evidence actually matters for future consistency
  decisions.
- `enforce_budget`'s halving-search is a coarse mechanism; it doesn't
  optimize, it satisfices — fine for now, not a claim of an optimal
  compression policy.

## Validation

New tests: (a) compressing evidence beyond the cap drops the correct
(middle) entries and increments `evidence_dropped` correctly; (b) canonical
value/confidence are unchanged by compression; (c) `enforce_budget` reduces
size when evidence exceeds the cap, and reports failure honestly when even
`max_evidence=1` doesn't fit the budget.

## Deliverables

- This document.
- `castgraph/compression/compress.py` + tests.

## Quality Gate

- **Memory quality**: compression is real (measurably shrinks a store with
  enough evidence to compress) and preserves canonical truth exactly —
  passes.
- **Honesty check**: subtask 12 (the actual consistency-vs-size question)
  is explicitly not run, with the reason (no real dataset) restated rather
  than filled in with a synthetic case engineered just to produce a
  positive result — passes Section 24's rule.
