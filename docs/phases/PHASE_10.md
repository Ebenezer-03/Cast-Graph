# PHASE 10 — Consistency Verification Engine

## Objective

After generation, determine whether new content remains consistent —
per-dimension, not hidden behind one aggregate score (the brief's explicit
warning). Aggregate only as a clearly-labeled derived convenience, never as
the primary signal.

## Subtasks

### 1. Identity verification

Covered structurally by Phase 4's `IdentityMatch.confidence` (per
resolution event) — not yet aggregated across a run because the MVP
scenario only resolves identity once (one character, resolved before the
loop). Nothing to aggregate yet; would matter the moment a scenario
resolves identity per-clip (e.g. from real face/voice matches per
observation) rather than once up front.

### 2. Face consistency / 3. Voice consistency / 4. Appearance consistency / 5. Clothing consistency / 6. Personality consistency / 7. Speech-style consistency

All fall under the same generic mechanism today: `reconcile()`'s per-attribute
status already *is* the per-dimension consistency check for whichever
attributes happen to be named `face`/`voice`/`hair`/`personality`/etc. — the
mechanism doesn't special-case any one dimension (arguably a feature: adding
a new attribute name, e.g. `clothing`, doesn't require new code). This
phase's contribution is **aggregating those per-clip statuses across the
whole run into a per-attribute rate**, which didn't exist before (each
`reconcile()` call only reported on its own clip, with nothing accumulating
history across clips).

### 8. Relationship consistency

**Status**: not measurable — no relationship reconciliation exists (Phase 2/
5/6/7 standing gap). The report format has a slot for it; it's empty until
`Relationship` reconciliation is built.

### 9. Object consistency / 10. World-rule consistency

Same standing gap as locations/objects/world rules generally (Phase 2).
Not measurable yet.

### 11. Temporal consistency

Partially checkable via Phase 6's `canonical_state_at`, but not
incorporated into the aggregate report (it answers "what was true when," not
"was the new generation consistent with what was true then" — that would
require re-running reconciliation against a reconstructed past state, which
no scenario has needed yet since there's no flashback case). Deferred.

### 12. Aggregate consistency scoring — implemented, with the brief's own warning heeded

**Problem**: some single number is eventually useful for a dashboard/report,
but must not be presented as if it were validated or as if it captured
everything.
**Approach**: `consistency_report(entity, history)` computes, per attribute,
`rate = count(status in {CONSISTENT, EXPECTED_CHANGE, EXPLAINED_TRANSITION,
TEMPORARY_OVERRIDE, PROMOTED}) / count(status not in {ESTABLISHED, DYNAMIC})`
— i.e., of the times this attribute was actually checked against an
existing canonical value (excluding first-time establishment and
dynamic/unchecked attributes), how often was the result something other
than unexplained/ambiguous drift. An **aggregate** is also computed as a
plain unweighted mean across attributes with at least one checked
observation — labeled explicitly, in both code comment and printed output,
as "an unweighted mean across attributes that happened to be observed, not
a validated or calibrated score."
**Alternatives considered**: a weighted aggregate (e.g. weight identity
consistency higher than clothing) — rejected for now: no basis exists yet
to justify any particular weighting (would be an arbitrary number dressed
up as a decision); an unweighted mean is at least transparent about being
naive.
**Recommended approach**: as implemented; report per-attribute rates
*first*, the aggregate *last and clearly labeled*, matching the brief's
instruction not to hide weaknesses behind one score.

## Architecture Changes From Previous Phase

- New module `castgraph/consistency/report.py`: `consistency_report(entity,
  history: list[list[dict]]) -> dict` — takes the list of per-clip
  `reconcile()` reports accumulated over a run.
- `run_mvp.py` collects each clip's report into a `history` list and prints
  the final consistency report (per-attribute rates + labeled aggregate)
  alongside the existing final-state output.

## Risks

- The aggregate, however clearly labeled, is exactly the kind of number
  that's easy to quote out of context later. Labeling it in the printed
  output itself (not just in this doc) is the mitigation.
- With only 4 clips and 1 unexplained + 1 disguise case, the computed rates
  are based on very few samples per attribute — stated in the printed
  output as a caveat, not hidden.

## Validation

New test: given a known sequence of statuses for one attribute (e.g.
`[CONSISTENT, CONSISTENT, UNEXPLAINED_DRIFT]`), the computed rate matches
the expected fraction (2/3), and `ESTABLISHED`/`DYNAMIC` entries are
excluded from the denominator correctly.

## Deliverables

- This document.
- `castgraph/consistency/report.py` + test.
- Updated `run_mvp.py` to accumulate and print the report.

## Quality Gate

- **Research quality**: aggregate scoring implemented but explicitly
  distrusted in its own output — passes the brief's Phase 10 instruction
  directly.
- **Honesty check**: 5 of 12 dimensions marked not measurable, with the
  standing reason (no reconciliation/scenario yet) restated rather than
  quietly dropped — passes.
