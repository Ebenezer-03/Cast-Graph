# PHASE 6 — Temporal World-State Engine

## Objective

Introduce time: answer "what was true at clip X" and "what changed between
X and Y", not just "what is true now." Previously deferred entirely (see
ROADMAP.md); this phase upgrades it from a stub to a real, minimal
implementation, because Phase 5's promotion mechanism turned out to
*already produce* the data a temporal reconstruction needs (a chronological
chain of canonical-value changes) — so building this now is no longer
speculative, unlike when the stub note was written.

## Assumptions

- **ASSUMPTION**: "time" for this MVP = clip processing order, not
  real-world/story timestamps. No scenario has flashbacks or out-of-order
  narrative time yet, so only in-order reconstruction is built. Flashback/
  time-jump semantics remain deferred (still speculative without a scenario
  to design against).

## Subtasks

### 1. Temporal intervals

**Status**: not modeled as intervals — clip order is a total order (a
single sequence index per clip), not interval ranges. Sufficient for the
current scenario (no overlapping/parallel timelines); a real interval model
would be needed for flashbacks or parallel storylines. Deferred.

### 2. State transitions

**Implemented**: Phase 5's promotion mechanism *is* a state transition
record (`PROMOTED_FROM_PREVIOUS` exceptions carry old value, new value, and
the clip where the transition happened). This phase adds the query that
reads that chain back out: `canonical_state_at`.

### 3. Event ordering

**Implemented**: `MemoryStore.clip_sequence: list[str]`, appended to
automatically the first time a clip_id is seen by `establish`/
`record_exception`/`record_unexplained`/`promote`. Gives every clip a
stable sequence index without requiring the caller to track it separately.

### 4. Relationship evolution / 5. Character state evolution

Character *attribute* evolution is what subtask 2's promotion-chain query
answers. Relationship evolution is not implemented — `Relationship` (Phase
2) has no promotion/transition mechanism yet, since no scenario has a
relationship that actually changes. Deferred, consistent with Phase 2's own
note.

### 6. Object state evolution / 7. Location state

Not implemented — no object/location scenario exists (Phase 2 subtask 3/4
gap, unchanged).

### 8. Temporary conditions

Partially addressed by `Deviation.active_until` (Phase 2) — still unused
(nothing sets it), so temporary conditions are not yet auto-expired. Stated
plainly rather than building auto-expiry against a scenario that never
exercises it.

### 9. Flashbacks / 10. Time jumps

**Status**: not modeled. Both require a temporal model where clip sequence
order and *story* chronological order diverge — the MVP scenario is
strictly linear in both, so there is nothing to validate a flashback/
time-jump implementation against yet. Explicitly deferred, not faked.

### 11. Causal transitions

Partially present: `Event` (Phase 2) is designed to link a clip to the
entities/effects it caused, but is still unpopulated (same gap noted in
Phase 2/3). Not fixed this phase.

### 12. State reconstruction at arbitrary time — the one real deliverable

**Problem**: given everything above, can the system actually answer "what
was Marcus's canonical voice as of clip ep3" (i.e., before whatever happened
in ep4/ep5)?
**Approach**: reconstruct the promotion chain for an attribute: the first
value (recoverable from the oldest `PROMOTED_FROM_PREVIOUS` exception's
`canonical_value`, or the current canonical value if it was never
promoted), followed by each promotion's new value at its clip's sequence
index. `canonical_state_at(store, entity_id, attribute, at_clip_id)` walks
this chain and returns whichever value was in effect at or before the
given clip's sequence index.
**Alternatives considered**: store a full value-history log on every
`CanonicalAttribute` from the start (simpler to query, more memory —
duplicates what the promotion-chain reconstruction already gets for free
from existing data) — rejected for now to keep memory bounded (Principle 4);
worth revisiting if reconstruction cost becomes a real concern at scale.
**Recommended approach**: promotion-chain reconstruction, as implemented.
**Known limitation**: only reconstructs *canonical* truth over time, not
what was actively true including temporary overrides at that moment (that
would need subtask 8's active-window tracking, which isn't built) — stated,
not hidden.

## Architecture Changes From Previous Phase

- `MemoryStore.clip_sequence: list[str]` — new, auto-populated.
- New module `castgraph/temporal/engine.py`: `canonical_state_at(store,
  entity_id, attribute, at_clip_id) -> Any | None`.
- `castgraph/temporal/README.md` updated to reflect that this is no longer
  a pure stub.

## Data Flow

New read-only query path: `MemoryStore` (populated by `reconcile()`) ->
`temporal.canonical_state_at()` -> a value. Doesn't sit in the main
generate/observe/reconcile loop; it's an on-demand query a creator or a
future audit UI (Phase 13) would call.

## Risks

- Reconstruction assumes clip processing order == story chronological
  order — false the moment a flashback scenario exists. Calling this out
  explicitly so nobody mistakes today's `canonical_state_at` for real
  temporal reasoning.
- Reconstruction is O(number of promotions), fine at MVP scale, unexamined
  at real scale (ties into Phase 12's compression concerns).

## Validation

New test: after a promotion (as in Phase 5's test), `canonical_state_at`
for the clip *before* the promotion returns the old value; for the clip *at
or after* the promotion, returns the new value.

## Deliverables

- This document.
- `castgraph/temporal/engine.py` + `clip_sequence` tracking in
  `MemoryStore`.
- New test.

## Quality Gate

- **Honesty check**: subtasks 1, 4 (relationships), 6, 7, 9, 10, 11 are
  explicitly marked not implemented, with a scenario-based reason, not
  hidden behind the one real deliverable (subtask 12) — passes.
- **Technical quality**: the implemented query reuses data already produced
  by Phase 5, adding no new memory overhead (Principle 4) — passes.
