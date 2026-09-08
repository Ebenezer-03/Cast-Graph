# PHASE 4 — Multimodal Identity Resolution

## Objective

Solve "who is this entity" robustly: face, voice, name, coreference,
appearance similarity, contextual/relationship matching, multimodal fusion,
unknown-entity detection, confidence, conflict resolution, merge/split —
without relying on a single embedding.

## Assumptions

Same load-bearing assumption as Phase 3: no real face/voice models exist in
this project. This phase's *design* covers the full multimodal picture; its
*implementation* is limited to what's buildable and testable without those
models — name/alias matching, plus the structural seams for the rest.

## Subtasks

### 1. Face identity / 2. Voice identity / 5. Appearance similarity

**Problem**: match a detected face/voice/appearance to a known entity.
**Approach (real)**: embedding similarity (face/voice encoders) against
stored reference embeddings per entity, thresholded.
**Status**: **not implemented — no models available.** This is the single
biggest capability gap in the whole project relative to the original brief:
without this, identity resolution cannot catch "same character rendered
with a different face" (the brief's core Marcus example), only "same
character *named* the same thing." Naming this plainly rather than
building a fake embedding comparison that would look real but prove
nothing.

### 3. Name resolution / 4. Coreference

**Problem**: match "Marcus" / "he" / "the man" to the same entity.
**Approach (real)**: name matching + pronoun coreference resolution against
recent entity mentions.
**Implemented**: exact name matching, now extended with an alias registry
(subtask below) — coreference ("he"/"the man") is **not implemented**; the
MVP scenario always names the character explicitly, so there's been nothing
to test coreference resolution against.
**Recommended approach for aliases**: `Entity.aliases: set[str]`, checked
case-insensitively alongside the canonical name. This is a real,
incremental improvement over Phase 1-era name-only matching, and is
directly testable without any external model.

### 6. Contextual matching / 7. Relationship-based matching

**Problem**: use scene context (only one character named "the doctor" in
this world) or relationship structure (Sarah's talking to *someone* who
must be a known relation) to disambiguate when name matching alone is
ambiguous.
**Status**: **not implemented.** No scenario has more than one character
requiring disambiguation yet (`scenario/marcus_sarah.py` only fully models
Marcus; Sarah is mentioned but never independently resolved/observed).
Building disambiguation logic with nothing to disambiguate would be
speculative.

### 8. Multimodal fusion

**Problem**: combine face+voice+name+context signals into one resolution
decision with a combined confidence, rather than trusting one modality.
**Approach (real)**: weighted fusion or a small learned combiner over
per-modality similarity scores.
**Status**: moot until at least two real modalities exist (currently zero —
name matching is the only signal). Recorded as the eventual target
architecture: `resolve_identity` should return a confidence *and* a
breakdown of which modalities contributed, not just an id, so fusion has
something to fuse. Implementing the breakdown structure now (even with only
one real modality) is worthwhile since it's the seam future modalities plug
into.

### 9. Unknown-entity detection

**Problem**: decide when an observed character is genuinely new vs. a
mis-resolution of a known one.
**Approach (implemented)**: `resolve_identity` already creates a new entity
whenever no name/alias match is found — this correctly handles "genuinely
new" but has no way to catch "mis-resolution" (e.g. a typo'd name would
silently become a new entity rather than being flagged as a possible match
to an existing one). **Gap, named**: no fuzzy/edit-distance fallback exists;
a typo becomes a silent identity fragmentation, not an error.

### 10. Identity confidence

**Implemented as part of this phase's code change**: `resolve_identity` now
returns a result carrying `confidence` and `method` (`"exact_name"` |
`"alias"` | `"new"`), not just a bare id — see Architecture Changes.

### 11. Identity conflict resolution / 12. Identity merging/splitting

**Problem**: two different-looking observations turn out to be the same
entity (merge) or one entity turns out to have been two conflated ones
(split).
**Status**: **not implemented.** No conflict has occurred in any scenario
run yet (a precondition for designing this well is having a real case to
design against — speculative merge/split logic untested against a real
conflict would likely be wrong in ways that wouldn't surface until it's too
late). Flagged as a required capability before this project could honestly
claim RQ8 (generator-agnostic) or handle a multi-character scenario safely.

## Architecture Changes From Previous Phase

- `Entity` gains `aliases: set[str]`.
- `resolve_identity` now returns an `IdentityMatch` dataclass
  (`entity_id, confidence, method`) instead of a bare string — a real,
  backward-incompatible signature change (one call site, `run_mvp.py`,
  updated accordingly).
- No embedding-based, coreference, contextual, or merge/split logic added —
  all correctly identified above as blocked on missing models or missing
  test scenarios, not skipped out of laziness.

## Risks

- **Named-entity-only resolution is the project's weakest link relative to
  its own stated problem** (the brief's whole motivating example is a face
  changing while the name prompt stays the same — today's system cannot
  catch that at all, only a name mismatch). This should be the top priority
  for any future session with real model access.
- Alias matching introduces a new failure mode: an overly broad alias
  (e.g. "he") would silently merge unrelated characters. `aliases` is
  intentionally a manually-curated set, not auto-inferred, to avoid this
  for now.

## Validation

New test: alias match resolves to the same entity id as the canonical name;
an unrelated name creates a new entity with `method="new"`.

## Deliverables

- This document.
- `IdentityMatch` dataclass + alias-aware `resolve_identity`.
- Updated `run_mvp.py` call site.
- New identity resolution test.

## Quality Gate

- **Honesty check**: 8 of 12 subtasks explicitly marked not implemented,
  with the reason tied to a missing model or missing test scenario, not
  hand-waved — passes.
- **Technical quality**: the one implemented improvement (aliases +
  confidence) is small, testable, and doesn't pretend to solve modalities
  it can't — passes.
