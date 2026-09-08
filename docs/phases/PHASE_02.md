# PHASE 2 — World State and Memory Model

## Objective

Design a storage-independent logical representation for entities, character/
location/object/relationship/event/rule state, canonical vs. dynamic state,
temporary overrides, confidence/temporal scope, and provenance — compact by
construction. Extend the memory model from Phase 1's definitions into an
actual schema.

## Assumptions

- Carries forward Phase 1's assumption: discrete, independently-triggered
  generations, not one continuous session.
- **ASSUMPTION**: one `MemoryStore` = one creative project/world. Multi-world
  sharing (a character appearing in two unrelated projects) is out of scope.

## Subtasks

### 1. Define entities

**Problem**: need one representation covering characters, locations,
objects, without forcing every entity type through character-shaped fields.
**Approach**: a single `Entity` record with a required `entity_type`
discriminator (`character | location | object`) and a type-appropriate
attribute set — attributes stay a flat dict either way (no schema-per-type
enforcement at the model layer).
**Alternatives**: separate classes per entity type (`Character`, `Location`,
`Object`) — rejected: duplicates canonical/exception/evidence machinery
three times for no behavioral difference; a subclass would only be justified
once type-specific *behavior* (not just fields) emerges.
**Recommended approach**: add `entity_type: str = "character"` to the
existing `Entity` dataclass; default preserves backward compatibility with
the MVP's Marcus-only data.
**Implementation implications**: one-line addition to `castgraph/memory/model.py`,
implemented below.
**Research implications**: none.

### 2. Define character state

Already implemented: `canonical` (persistent attributes: voice, hair,
appearance, personality, clothing), `exceptions`/`unexplained` (deviations),
`relationships`. No change needed beyond `entity_type="character"`.

### 3. Define location state

**Problem**: locations have attributes too (lighting, layout, "burned down
in episode 3") but no identity-resolution step (a location's name generally
*is* its identity — Phase 1 subtask 7).
**Approach**: `entity_type="location"`, same `canonical`/`exceptions`
structure, `relationships` unused (or repurposed later for
location-contains-location).
**Alternatives**: model locations as attributes of scenes rather than
first-class entities — rejected, loses persistent location state across
scenes (e.g. "the docks were rebuilt after the fire" needs to be canonical
state, not a per-scene fact).
**Recommended approach**: as stated.
**Implementation implications**: no new fields needed, just the discriminator.
**Research implications**: untested — no location scenario exists yet in
the MVP data.

### 4. Define object state

Same treatment as locations: `entity_type="object"`. Objects introduce a
new concern — **possession/location relationships** ("the sword is with
Marcus", "the sword is at the docks") which don't fit the current
`relationships: dict[str, str]` shape well (that's designed for
entity-to-entity social relationships, not spatial/possession state).
**Recommended approach**: flagged as a real gap, not solved in this phase —
`relationships` needs a typed variant (`kind: "social"|"possession"|"location"`)
before object state is genuinely usable. Deferred to when an object-bearing
scenario is actually built (currently none exists).

### 5. Define relationship state

**Problem**: `Entity.relationships: dict[str, str]` (built in the MVP) is a
placeholder — a `str` value can't carry evidence, classification, or
directionality (is "ally" symmetric? is "parent of" directional?).
**Approach**: promote relationships to their own record type, mirroring
`CanonicalAttribute`: `Relationship { target_id, kind, value, evidence,
directional: bool }`.
**Alternatives**: keep relationships as attributes on one side only (as now)
— rejected, Phase 1 subtask 6 already identified this as wrong (a
relationship is joint state, not one entity's attribute).
**Recommended approach**: introduce `Relationship` dataclass; store on
*both* entities for symmetric relationships, on the subject only (with
`directional=True`) for asymmetric ones (e.g. "reports to").
**Implementation implications**: implemented below in `model.py`.
Note: `reconcile()` does not yet operate over relationships (same gap noted
in Phase 1) — this phase adds the *data model*, not the reconciliation
logic for it. That's flagged as a Phase 5/11 follow-up, not silently
resolved here.
**Research implications**: RQ5 for relationships remains open.

### 6. Define event state

**Problem**: nothing currently records *events* (Marcus met Sarah at the
docks) as opposed to *state* (Marcus's voice is deep) — events are what
justify relationship/attribute transitions.
**Approach**: an `Event` record: `{ clip_ref, entities: [ids], summary,
effects: [(entity_id, attribute_or_relationship, new_value)] }` — a event
log entities' state changes point back to.
**Alternatives**: don't model events explicitly, infer everything from
diffing canonical state across clips — rejected: loses the causal
"why did this change" link that Phase 11 (drift attribution) and Phase 13
(provenance) both need; diffing after the fact can't reconstruct intent.
**Recommended approach**: add a minimal `Event` dataclass now; wire it up to
`reconcile()` only once state-change causes are actually reasoned over by
Phase 11's drift attribution in production terms (today `classify_drift`
receives narrative context as a raw string, not a stored `Event` yet).
**Implementation implications**: dataclass added below; not yet populated
by `run_mvp.py` — that wiring is a genuine TODO, listed under Architecture
Changes, not hidden.
**Research implications**: none new.

### 7. Define world rules

**Problem**: "magic doesn't exist here" is a constraint, not a fact about
one entity — doesn't fit the entity model at all.
**Approach**: a separate, small `WorldRule` list on `MemoryStore` (not
per-entity): `{ rule: str, evidence: [ClipRef] }`. Consulted during
retrieval/context-building (Phase 8/9) as a constraint block, and during
verification (Phase 10) as an additional check dimension.
**Alternatives**: model world rules as attributes of a synthetic "world"
entity — rejected, adds an artificial entity for no benefit over a plain list.
**Recommended approach**: as stated; not yet exercised (no scenario needs a
world rule yet — 1 character, no fantastical constraints in the MVP).
**Implementation implications**: added as a stub field on `MemoryStore`.
**Research implications**: none new.

### 8. Define canonical state

Already formalized and implemented (`CanonicalAttribute`). No change.

### 9. Define dynamic state

**Problem**: not everything is either "permanently canonical" or "a
recorded exception" — some state is expected to change on a known schedule
(e.g. "current outfit" changes every scene by design, that's not drift at
all, it's just not persistent).
**Approach**: introduce a third bucket, `dynamic`: attributes explicitly
marked as *not* subject to consistency checking (no canonical value is ever
established, no drift is ever flagged) — the opposite failure mode from
treating everything as canonical.
**Alternatives**: treat everything as canonical and rely on the drift
classifier to always call outfit changes "EXPECTED_CHANGE" — rejected: this
burns an LLM call and a classification decision on something that was never
ambiguous, and risks false UNEXPLAINED_DRIFT on legitimately unconstrained
attributes.
**Recommended approach**: an entity carries a `dynamic_attributes: set[str]`
allowlist of attribute names that skip reconciliation entirely. Empty by
default (current behavior unchanged); the creator (or a future auto-inference
step) declares which attributes are dynamic.
**Implementation implications**: added below; `reconcile()` updated to skip
attributes in this set. **This is a real, useful improvement over the MVP's
behavior** — it directly fixes a gap, not just documents one.
**Research implications**: RQ2 — dynamic attributes shouldn't count against
the memory budget the same way canonical ones do (they're a declaration, not
accumulated evidence); worth tracking separately in Phase 12's budget math.

### 10. Define temporary overrides

Already implemented as `exceptions` (deviations classified as
`EXPECTED_CHANGE`/`EXPLAINED_TRANSITION`/`TEMPORARY_OVERRIDE`). One gap:
nothing currently marks an override as *expired* (e.g. the disguise ends).
**Recommended approach**: add an optional `active_until: str | None`
(clip_id) field to `Deviation`; when set, `reconcile()` should stop treating
the override as still valid past that point (currently unbounded — a
disguise, once recorded, is never "over"). Flagged as a real gap; adding the
field now but not the auto-expiry logic (needs Phase 6 temporal reasoning to
do properly — deferred with that phase, per ROADMAP.md).

### 11. Define confidence and temporal scope

**Problem**: nothing currently has a confidence value at all — a canonical
attribute established from one ambiguous clip is treated identically to one
confirmed five times.
**Approach**: add `confidence: float` to `CanonicalAttribute`, incremented
(capped at 1.0) each time matching evidence is added, left as an
**ENGINEERING ASSUMPTION** for the exact update function (currently: simple
saturating increment, not a principled Bayesian update — that would need a
noise model this project doesn't have data to fit yet).
**Alternatives**: a full Bayesian confidence model — rejected as
over-engineered relative to the evidence available (a handful of synthetic
clips, no real perceptual-model noise characteristics to calibrate against).
**Recommended approach**: simple saturating counter now, revisit when real
observation confidence (from actual vision/audio models) exists.
**Implementation implications**: added below.
**Research implications**: RQ1/RQ7 both eventually need real confidence
semantics; today's version is a placeholder that shouldn't be over-trusted.

### 12. Define provenance semantics

Already partially implemented (`ClipRef` on every `CanonicalAttribute` and
`Deviation`). Phase 13 will expand this; no change here beyond what's
already in the model.

## Architecture Changes From Previous Phase

- `Entity` gains `entity_type` and `dynamic_attributes`.
- New `Relationship` dataclass replaces the placeholder `relationships: dict[str, str]`.
- New `Event` dataclass (defined, not yet wired into `run_mvp.py`).
- New `WorldRule` list on `MemoryStore` (defined, not yet exercised).
- `CanonicalAttribute` gains `confidence: float`.
- `Deviation` gains optional `active_until`.
- `reconcile()` updated to respect `dynamic_attributes` (skip reconciliation
  entirely for attributes in that set) and to increment confidence on
  matching evidence.

These are real code changes (below), not just documentation — Phase 2
genuinely extends the schema, unlike Phase 1 which was definitions-only.

## Data Flow

Unchanged at the pipeline level; the schema each stage reads/writes is
richer.

## Interfaces

`MemoryStore.establish`, `reconcile()` signatures unchanged; internal
`Entity`/`Deviation`/`CanonicalAttribute` shapes extended (additive, so
existing serialized JSON from the MVP run remains loadable — new fields get
their dataclass defaults).

## Risks

- **Scope-creep risk**: `Relationship`, `Event`, `WorldRule` are now
  *modeled* but mostly unexercised — risk of building schema nobody uses if
  no scenario ever needs locations/objects/world rules. Mitigated by keeping
  them additive/optional and not blocking on them.
- **Confidence semantics risk**: the saturating-counter confidence model is
  arbitrary; any number derived from it (e.g. "80% confident") would be
  **UNVALIDATED** and shouldn't be shown to a user as a real probability.

## Validation

- Existing tests (`tests/test_reconcile.py`) must still pass unchanged after
  the schema extension (additive-only guarantee) — checked below.
- New behavior (`dynamic_attributes` skipping reconciliation) gets a new
  test.

## Deliverables

- This document.
- Updated `castgraph/memory/model.py` (entity_type, Relationship, Event,
  WorldRule, confidence, active_until, dynamic_attributes).
- Updated `castgraph/drift/reconcile.py` (dynamic-attribute skip, confidence
  increment).
- New test for dynamic-attribute skip behavior.

## Quality Gate

- **Technical quality**: additive-only schema change, verified by running
  the existing test suite after the change (see commit) — passes.
- **Memory quality**: `dynamic_attributes` is a genuine compactness
  improvement (avoids wasting budget/LLM calls on attributes never meant to
  be canonical) — passes.
- **Honesty check**: `Relationship`/`Event`/`WorldRule` explicitly marked
  unexercised, not silently claimed as "done" — passes.
