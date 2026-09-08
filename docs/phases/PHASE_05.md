# PHASE 5 — Canonical State Formation

## Objective

Decide what becomes persistent truth: aggregation, conflict handling,
promotion/demotion, anomaly detection, versioning — without ever letting a
single new observation silently overwrite canonical state (Principle 5).

## Subtasks

### 1. Observation aggregation / 2. Repeated evidence consolidation

**Implemented** (Phase 2/reconcile): matching observations append to
`CanonicalAttribute.evidence` and reinforce `confidence`. No change needed.

### 3. Canonical attribute selection

Already decided in Phase 1/2: first observation of a never-seen attribute
establishes it as canonical baseline. **Known weakness, stated plainly**: if
the *first* clip happens to be wrong/atypical (e.g. a one-off flashback
observed before any "normal" scene), it becomes canonical and every correct
subsequent observation would look like a deviation. No mitigation exists for
this yet — flagged as a real limitation, not solved by this phase.

### 4. Confidence aggregation

Implemented in Phase 2 (`reinforce()`), with the caveat already recorded
there (saturating counter, not calibrated).

### 5. Conflicting observation handling

Implemented via `classify_drift` + exception/unexplained split.

### 6. Persistent vs. temporary classification

Implemented: `exceptions` (temporary/explained) vs. `canonical` (persistent)
vs. `unexplained` (neither — surfaced, not applied).

### 7. Stable vs. dynamic attribute detection

Implemented in Phase 2 (`dynamic_attributes`), though currently
**manually declared**, not auto-detected. Auto-detection (e.g. "this
attribute has taken 5 different values across 5 clips with no drift
classification ever agreeing — it's probably meant to vary") is a
reasonable future heuristic but would need real usage volume to tune
without just guessing a threshold. Deferred.

### 8. Anomaly detection

**Problem**: a single implausible observation (e.g. attribute value nobody
would classify as anything but nonsense) shouldn't need a full LLM
drift-classification round-trip.
**Status**: not implemented — no real anomaly has occurred in the MVP
scenario to design a detector against; would be speculative.

### 9. Canonical state versioning

**Problem**: nothing currently records *when* canonical state actually
changed (only original establishment) — if canonical state is ever promoted
to a new value (see subtask 11), there's no history of the old value.
**Status**: not implemented this phase. Deferred to whenever versioning is
actually exercised (i.e., once promotion, subtask 11, is), so it isn't
built against a hypothetical.

### 10. Evidence weighting

**Problem**: should older evidence count less than recent evidence?
**Status**: not implemented — no scenario has evidence old enough (in clip
count) to make recency weighting meaningful yet; the entire MVP scenario is
4 clips. Deferred, not solved.

### 11. State promotion/demotion — the one real gap this phase closes

**Problem**: per Principle 6, a change can be intentional and *permanent*
(not a "temporary override" but a genuine, lasting update to canonical
truth — e.g. a haircut that's meant to stick from here on). Today's
`reconcile()` has no path for this: everything that isn't a canonical match
either becomes a temporary exception or gets stuck in `unexplained` forever,
even if the same new value keeps recurring and is never re-classified as
matching the old canonical value again.
**Approach**: if the *same* observed value for an attribute has been
recorded as `UNEXPLAINED_DRIFT` (or `AMBIGUOUS`) at least `N` times in a
row (an **ENGINEERING ASSUMPTION**: `N=2` chosen as the smallest number that
distinguishes "one-off drift" from "a real, sustained new normal," not
validated against real data), promote it: the new value becomes canonical,
the old canonical value is archived, and the promotion event itself is
recorded so it's auditable (Phase 13) rather than silent.
**Alternatives considered**: promote on the *first* repeated match
regardless of classification (too aggressive — would let one classification
mistake permanently corrupt canonical state); never auto-promote, require a
human decision every time (safest, but contradicts Principle 9 — automatic
operation — for a case that should often be safe to automate); a decaying
vote/majority scheme over a sliding window (more principled, rejected as
over-engineered for a threshold that isn't validated against real data
anyway — a fixed small N is no less arbitrary and much simpler to reason
about and to change later).
**Recommended approach**: fixed small N, implemented and tested below,
explicitly labeled as an unvalidated threshold.
**Implementation implications**: `reconcile()` now tracks consecutive
matching unexplained observations per attribute and promotes on threshold.
**Research implications**: this is exactly the kind of policy RQ5/RQ6
should eventually validate against a real drift benchmark (Phase 15) — is
N=2 too eager (promotes real drift as if intentional) or too conservative
(leaves real permanent changes stuck as "unexplained" too long)? Unknown.

### 12. Canonical state validation

**Problem**: is there any check that canonical state is internally
sane (e.g. no attribute with two different "canonical" values at once)?
**Approach**: this is structurally impossible given the current model
(`canonical: dict[str, CanonicalAttribute]` — one value per key by
construction), so no separate validation pass is needed *for this
invariant*. Other invariants (e.g. "an attribute cannot be both `dynamic`
and have a canonical value") are not currently enforced — recorded as a
gap; `reconcile()`'s dynamic-check happens first so in practice a dynamic
attribute never gets a canonical entry through normal flow, but nothing
stops direct misuse of the `MemoryStore` API from creating that
inconsistency. Not fixed this phase — would need an explicit invariant
-checking method, better done once more invariants exist to check together
rather than one at a time.

## Architecture Changes From Previous Phase

- `Entity` (or a per-attribute tracking structure) needs to remember
  "how many consecutive times has value X been observed since it stopped
  matching canonical" — implemented as a small `_pending: dict[str, tuple[value, count]]`
  tracking dict on `Entity`, not persisted as a first-class model concept
  (it's working state, not truth — deliberately excluded from
  `to_json()`'s output to keep memory compact, per Principle 1).
- `reconcile()` updated: after recording an `UNEXPLAINED_DRIFT`/`AMBIGUOUS`
  deviation, check whether this is the Nth consecutive matching one; if so,
  promote — archive old canonical value into `exceptions` (classified
  `"PROMOTED_FROM_PREVIOUS"`, a new, project-defined classification distinct
  from the reasoner's six), set new canonical, reset the pending counter.

## Risks

- The promotion threshold is unvalidated (stated above).
- Promotion could interact badly with future auto-expiring temporary
  overrides (Phase 2/6) — e.g. a disguise that happens to recur across
  several clips could be wrongly promoted to permanent canonical state if
  it's ever misclassified as unexplained rather than a recognized
  recurring disguise. Not a problem yet (no scenario recurs a disguise),
  flagged for whoever builds Phase 6 properly.

## Validation

New test: an attribute observed twice in a row with the same new
(previously-unexplained) value gets promoted; canonical updates; the old
value is archived with the new classification; `unexplained` does not
retain the promoted-away entries as still-open (they're archived, not
lost — provenance preserved per Principle 1/Phase 13).

## Deliverables

- This document.
- Promotion logic in `castgraph/drift/reconcile.py` + a `_pending` field on
  `Entity`.
- New test.

## Quality Gate

- **Research quality**: threshold explicitly labeled as an engineering
  assumption, tied to an open RQ rather than presented as settled — passes.
- **Memory quality**: promotion bookkeeping (`_pending`) deliberately kept
  out of serialized memory — passes Principle 1/4 (bounded, compact).
