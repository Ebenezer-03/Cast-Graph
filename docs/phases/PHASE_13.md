# PHASE 13 — Provenance, Evidence and Auditability

## Objective

Make canonical state explainable: for any attribute, show what it is, why
it's believed, and what (if anything) was overridden or promoted along the
way — evidence references, not raw media (Principle 1).

## Subtasks

### 1. Fact provenance / 2. Observation provenance / 3. Temporal provenance / 4. Source references

**Already implemented** across earlier phases: every `CanonicalAttribute`
and `Deviation` carries `ClipRef`s (clip id + short excerpt); Phase 6 adds
sequence-based temporal provenance (`clip_sequence`). No change needed.

### 5. Evidence confidence

Already implemented (`CanonicalAttribute.confidence`, Phase 2/5) and now
surfaced through retrieval (Phase 8) and (optionally) deviations (Phase 11).

### 6. Conflict provenance

Every classified deviation already records its own `reasoning` and
`clip_ref` (Phase 1/11) — a conflict's provenance *is* its `Deviation`
record. No separate structure needed.

### 7. Canonical-state justification / 8. Correction explanation / 9. User-facing evidence — the real deliverable this phase

**Problem**: the pieces above exist but are scattered across `canonical`,
`exceptions`, `unexplained` with no single function that answers "why do
we believe this, in plain terms" for a person, not a developer reading
JSON.
**Approach**: `explain(store, entity_id, attribute) -> str` — assembles the
current canonical value, its confidence and evidence count, the promotion
history if any (old value -> new value, and why), and any still-open
unexplained deviations for that attribute — into one readable block. This
is the exact shape the brief's UX section describes (Section 16's
"Established evidence / New evidence / Reason" mockup), built as a plain
function rather than a UI, since there's no UI in this project.
**Alternatives considered**: return structured data only, leave formatting
to a caller — rejected for this phase since there is no caller yet other
than `run_mvp.py`/a human reading terminal output; a structured-data
version can be split out later if a real UI consumer needs it (the current
implementation keeps the assembly logic separate from the print statement
so that split is cheap).
**Recommended approach**: as implemented.

### 10. Audit history

Partially covered: `explain()` reads the currently-stored history
(exceptions/unexplained/promotions); there's no separate append-only audit
log distinct from the memory model itself. Given the model already
preserves promoted-away values (Phase 5) rather than overwriting them, the
memory model *is* a partial audit log by construction — a fully separate
audit log would matter once compression (Phase 12) starts actually
discarding evidence in a real run, at which point `evidence_dropped`
(Phase 12) is the only surviving signal that something was lost. Recorded
as a known limitation: **once evidence is compressed, `explain()` cannot
show the dropped entries, only that some number were dropped.**

### 11. Privacy considerations

**Status**: not addressed — no real personal data exists in a synthetic
text scenario. Would matter the moment real video/faces are involved (a
real system would need to consider whether storing face/voice embeddings
of real people requires consent/retention policies) — noted as a real,
unaddressed concern for any future session that adds real biometric
observation (Phase 3/4), not something this phase can respons‌ibly design
in the abstract.

### 12. Provenance compression

Already handled by Phase 12's `evidence_dropped` counter — provenance
compression *is* evidence compression in this model; no separate mechanism
needed.

## Architecture Changes From Previous Phase

- New module `castgraph/provenance/audit.py`: `explain(store, entity_id,
  attribute) -> str`.

## Risks

- `explain()`'s output quality is only as good as `Deviation.reasoning`
  strings, which for `StubReasoner` are themselves templated, not
  genuinely explanatory of nuance a real LLM might surface.
- The stated limitation (can't show dropped evidence) is a real,
  un-worked-around gap — flagged, not solved.

## Validation

New test: `explain()` on an attribute that was promoted once returns text
mentioning both the old and new values and the promotion reasoning; on an
attribute with no history, returns a plain statement of the current value
and evidence count.

## Deliverables

- This document.
- `castgraph/provenance/audit.py` + test.

## Quality Gate

- **Product quality**: `explain()`'s output shape matches the brief's own
  UX mockup (Section 16) almost directly — passes.
- **Honesty check**: the evidence-compression blind spot (subtask 10) is
  named, not silently left for someone to discover later — passes.
