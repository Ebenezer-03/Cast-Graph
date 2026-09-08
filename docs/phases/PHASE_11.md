# PHASE 11 — Context-Aware Drift Attribution

## Objective

The brief's core research phase: classify deviations using narrative
context, not just detect that a value changed. Already substantially built
in earlier phases (this doc formalizes what exists and closes one real gap:
the `AMBIGUOUS` classification path, never exercised until now).

## Subtasks 1-11 (detect / classify / search-for-explanation / inspect intent / temporal / event / temporary overrides / transformations / ambiguity / confidence / explanations)

**Already implemented** across earlier phases: `classify_drift` (Phase 1)
detects a deviation (value mismatch), searches for a narrative explanation
via `extract_transformation_cues` (Phase 7, shared with prompt
understanding), and returns one of the six required classifications with a
`reasoning` string. Confidence (subtask 10) is not currently part of
`classify_drift`'s return value — **named gap**: `StubReasoner` has no
principled way to express "I'm 60% sure this is a disguise" (it's a keyword
match, binary by construction); a real `GatewayReasoner` could return a
confidence, and the `Deviation` model already has room to carry one (it
doesn't yet — see Architecture Changes).

### 9. Distinguish ambiguity — the one real gap closed this phase

**Problem**: `StubReasoner.classify_drift` has never returned `AMBIGUOUS` —
its only three outcomes are `TEMPORARY_OVERRIDE`, `EXPLAINED_TRANSITION`, or
`UNEXPLAINED_DRIFT`, decided by simple keyword presence. There's no case
where the stub itself is *unsure*.
**Approach**: add one such case — when the narrative context contains
*both* a disguise cue and an injury cue (a genuinely ambiguous, conflicting
signal a keyword matcher can't resolve any better than admitting it can't),
return `AMBIGUOUS` instead of picking one arbitrarily.
**Alternatives considered**: return `AMBIGUOUS` whenever confidence is
generically "low" — not possible without a real confidence signal (the
keyword matcher only ever has 100% confidence in what it matched, 0% in
resolving conflicts between matches). The conflicting-cues case is the one
place the stub can honestly claim uncertainty.
**Recommended approach**: implemented; keeps the stub's behavior
unchanged for the (non-conflicting) cases that were already tested.
**Research implications**: this is a narrow, artificial trigger for
`AMBIGUOUS` — real ambiguity (genuinely unclear whether a change is
explained) requires real judgment a keyword matcher can't approximate.
`GatewayReasoner`, once exercised, is expected to hit `AMBIGUOUS` far more
often and in more genuinely uncertain cases — this is flagged as a known
limitation of testing against the stub, not a claim that ambiguity is
"solved."

### 12. Decide whether memory should change

Already the entire point of `reconcile()`'s classification-dependent
branching (Phase 5) — explicit vs. implicit change is the canonical/
exception/unexplained/promoted split.

## Architecture Changes From Previous Phase

- `StubReasoner.classify_drift` returns `AMBIGUOUS` when both disguise and
  injury cues are present in the narrative context (a new, narrow rule).
- `Deviation` (Phase 2) gains an optional `confidence: float | None = None`
  field — populated only when a reasoner actually provides one (not
  currently `StubReasoner`; ready for `GatewayReasoner`).

## Risks

- The `AMBIGUOUS` trigger condition is artificial (chosen because it's the
  only place the stub can honestly claim confusion) — real ambiguity
  detection remains unvalidated.

## Validation

New test: narrative context with both a disguise and an injury cue ->
`AMBIGUOUS` classification, recorded in `unexplained` (not `exceptions`,
per Phase 5's existing branch logic — ambiguous cases are surfaced for
review, not silently treated as explained).

## Deliverables

- This document.
- `AMBIGUOUS` path in `StubReasoner.classify_drift`.
- `Deviation.confidence` field.
- New test.

## Quality Gate

- **Honesty check**: the ambiguity trigger's artificiality is stated
  directly rather than presented as "ambiguity detection works" — passes.
