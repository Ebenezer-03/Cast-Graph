# PHASE 8 — Selective Memory Retrieval

## Objective

Build and, where honestly possible, start comparing retrieval strategies:
full history vs. naive vs. embedding vs. structured vs. hybrid vs. adaptive
— answering "what is the minimum memory necessary for this generation."

## Subtasks

### 1. Entity-based retrieval

**Already implemented** (`retrieve()`, Phase 7 wired it to prompt-extracted
entities instead of a hardcoded id). This phase adds `confidence` to the
returned canonical values (previously dropped on the floor between the
memory model and the context adapter), since Phase 2 already tracks it.

### 2. Semantic retrieval

**Status**: not implemented — Principle 3 (don't assume embeddings are the
answer) plus no scenario currently needs similarity search (entity names
are known and exact-matched; nothing is being searched *for*). Would matter
once retrieval needs to answer "which of many characters is relevant to
this vague prompt" rather than "the prompt names them."

### 3. Temporal retrieval

Partially available via Phase 6's `canonical_state_at` (retrieval *of a
past state*, on demand) but not wired into the main `retrieve()` path,
which always returns *current* canonical state. Deferred until a scenario
needs "what did Marcus look like as of episode 3" as part of a generation
request itself (today it's only used as a standalone query/audit tool).

### 4. Relationship retrieval

**Status**: not implemented — same standing gap as Phases 2/6/7
(`Relationship` has no reconciliation, so nothing to retrieve yet).

### 5. State retrieval / 6. Event retrieval

State retrieval = what `retrieve()` already does. Event retrieval: not
implemented, `Event` remains unpopulated (Phase 2/3/6 gap, unchanged).

### 7. Relevance scoring

**Status**: not implemented beyond binary inclusion (an entity is either
retrieved or not, no graded relevance score). With one character and exact
name matching, a score would be uninformative (always 1.0 or 0.0) — building
a scoring function now would be untestable against real gradation. Deferred
until a multi-entity scenario exists.

### 8. Redundancy elimination

Structurally already true: `canonical` is a dict keyed by attribute — by
construction there is exactly one current value per attribute, no
duplicate facts to eliminate. Real redundancy elimination would matter for
evidence lists (many clips reinforcing the same fact) — Phase 12
(compression) owns that, not retrieval.

### 9. Conflict handling

Not applicable at retrieval time under the current model — reconciliation
(Phase 5/11) already resolved any conflict *before* it reached canonical
state; retrieval only ever reads the single resolved value. This is a
deliberate design property (canonical state is conflict-free by
construction), not a gap.

### 10. Context budget allocation

**Status**: not implemented — `build_context` (Phase 9-in-brief-numbering)
currently includes everything retrieved, uncapped. Matters once retrieved
memory could exceed a real generator's prompt budget; with one character
and three attributes, nothing has come close. Deferred to whenever Phase 12
compression makes memory large enough for this to bite.

### 11. Retrieval confidence

**Implemented this phase**: `retrieve()`'s output now includes each
attribute's `confidence` (from `CanonicalAttribute.confidence`, Phase 2) —
so a consumer (the context adapter, or eventually a real generator prompt)
can see that a freshly-established fact is less certain than one reinforced
five times, instead of presenting all canonical facts as equally certain.

### 12. Retrieval evaluation — a small, real, honestly-scoped experiment

**Problem**: RQ3 ("can selective retrieval outperform full-history
context") needs *some* measurement, not just an architectural assertion.
**Approach**: implemented `compare_retrieval_strategies(store, entity_ids)`,
which measures serialized byte size of (a) full-history retrieval (the
entire `MemoryStore`, unfiltered) vs. (b) selective entity-based retrieval,
on the *actual* memory produced by running the MVP scenario.
**This is a real, reproducible measurement — not a fabricated one — but its
scope is tiny and should not be over-generalized**: with one character, the
"full history" and "selective" sizes are close by construction (there's
nothing else in the store to exclude). The measurement is honest about
being a proof that the *mechanism* works, not evidence that selective
retrieval wins at scale — that requires the Phase 15 experiment with a
multi-character, multi-clip dataset that doesn't exist yet.
**Recommended approach**: report both sizes and the ratio; label the result
plainly as scenario-specific in the printed output, not as a validated
finding.

## Architecture Changes From Previous Phase

- `retrieve()` output gains `confidence` per attribute.
- New `castgraph/retrieval/compare.py`: `compare_retrieval_strategies`.
- `run_mvp.py`'s final report section prints the comparison, clearly
  labeled as scenario-specific.

## Risks

- The retrieval-comparison "experiment" could be misread as evidence for
  RQ3 if the caveat is dropped — the printed output and this doc both state
  the limitation to prevent that.

## Validation

New test: `compare_retrieval_strategies` returns full_size >= selective_size
(should hold even in the degenerate single-character case, since selective
retrieval can only ever return a subset of what full history returns).

## Deliverables

- This document.
- `confidence`-carrying `retrieve()`.
- `compare_retrieval_strategies` + test.
- Updated `run_mvp.py` output.

## Quality Gate

- **Research quality**: the one new "experiment" is labeled with its actual,
  narrow scope rather than oversold as validating RQ3 — passes.
- **Honesty check**: 6 of 12 subtasks marked not implemented with reasons
  tied to missing scenarios/models, not hidden — passes.
