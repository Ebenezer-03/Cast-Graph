# PHASE 7 — Prompt Understanding and Context Extraction

## Objective

Before generation, extract what the creator prompt actually needs from
memory: entities, actions, events, locations, temporal cues, relationship
cues, transformation cues, negative constraints, and a first pass at which
memory is relevant — so retrieval (Phase 8) doesn't have to guess.

## Subtasks

### 1. Entity extraction

**Implemented already** (`Reasoner.understand_prompt`'s `entities` list),
carried forward. This phase promotes it out of ad-hoc use in `run_mvp.py`
into its own module (`castgraph/prompt/`), matching the brief's pipeline
diagram (prompt understanding is its own stage, not folded into the
adapter).

### 2. Action extraction / 3. Event extraction

**Status**: not implemented. `understand_prompt` returns the whole prompt as
`narrative_context` (a string), not a parsed action/event structure. A real
implementation would extract e.g. `{"action": "talks_to", "participants":
["marcus", "sarah"]}` — deferred: nothing downstream currently consumes a
structured action (drift classification takes the raw narrative string
directly), so building a parser with no consumer would be speculative.
Flagged as the natural next step once `Event` (Phase 2) is actually
populated.

### 4. Location extraction — implemented this phase

**Problem**: "at the docks" / "outside the hospital" should be pulled out,
not left buried in the narrative string, so retrieval could (eventually)
fetch location-entity state (Phase 2 subtask 3) alongside character state.
**Approach**: a simple pattern match (`"at|outside|in|near the <noun
phrase>"`) — an **ENGINEERING ASSUMPTION**, not a real parser; will miss
locations phrased differently ("the docks, where Marcus..."). Chosen because
building a real location parser has no location-entity consumer yet either
(no location scenario exists — Phase 2 gap) — this is a minimal, honestly
-labeled placeholder, not a claim of general NL location extraction.
**Recommended approach**: implemented as `extract_location`, isolated in its
own function so it can be swapped for a real parser or LLM call later
without touching call sites.

### 5. Temporal cues

**Status**: not implemented — same reasoning as subtasks 2/3: no consumer
exists yet (Phase 6's temporal engine reconstructs from clip order, not
from prompt-stated cues like "later that day"). Deferred.

### 6. Relationship cues

**Status**: not implemented — `Relationship` (Phase 2) has no reconciliation
logic yet, so extracting relationship cues from the prompt has nothing to
feed. Deferred, consistent with the standing Phase 2/6 gap.

### 7. Transformation cues — implemented this phase

**Problem**: `classify_drift` (Phase 1/`StubReasoner`) already scans
narrative context for disguise/injury keywords, duplicating logic that
prompt understanding should own.
**Approach**: expose the same keyword lists as a shared, named function
(`extract_transformation_cues`) called both by prompt understanding (so a
creator/future UI could see "this prompt signals: disguise" before
generation even happens) and available for `classify_drift` to reuse
instead of re-scanning text independently.
**Recommended approach**: implemented as a shared list in
`castgraph/prompt/extract.py`, imported by `castgraph/reasoning.py` rather
than duplicated — removes a real (small) duplication, doesn't change
`StubReasoner`'s classification behavior (tests still pass unchanged).

### 8. Negative constraints

**Problem**: "Marcus without his usual sarcasm" — an explicit *exclusion*,
different from a positive transformation cue.
**Status**: not implemented. `StubReasoner`'s keyword approach has no
negation handling at all (would misread "not disguising" as a disguise
cue). Named as a real weakness of the keyword approach specifically —
motivates why `GatewayReasoner` (real LLM) will be necessary before this is
trustworthy, not just a nice-to-have.

### 9. Intentional-change detection

This is `extract_transformation_cues`'s purpose from the prompt-side; the
actual *decision* still happens in `classify_drift` (Phase 11), which also
has access to the canonical/observed values, not just the prompt. Kept
separate deliberately — prompt understanding surfaces signal, drift
attribution makes the call, per Phase 1's definitional split.

### 10. Context requirements / 11. Memory relevance estimation

**Implemented already, minimally**: `retrieve()` (Phase 8, pre-dates this
phase) takes an explicit entity-id list. This phase's contribution: that
list should come from `understand_prompt`'s extracted entities, not be
hand-passed by the caller — wired in `run_mvp.py` this phase (previously it
was already using `entity_id` directly since there was only one character;
now genuinely reads from extracted entities, which matters the moment a
second character exists).

### 12. Generation-context planning

Already covered by `castgraph/adapters/build_context` (Phase 9, pre-dates
this phase in build order though not in the brief's numbering) — this phase
adds the extracted location into that context block.

## Architecture Changes From Previous Phase

- New module `castgraph/prompt/extract.py`: `extract_location(prompt)`,
  `extract_transformation_cues(text)`.
- `castgraph/reasoning.py`'s `StubReasoner.classify_drift` now imports and
  reuses `extract_transformation_cues` instead of its own inline keyword
  tuples (behavior-preserving refactor — existing tests must still pass).
- `run_mvp.py` updated to extract and display location, and to derive the
  retrieval entity list from `understanding["entities"]` rather than a
  hardcoded single id.

## Risks

- The location/transformation-cue extractors are simple keyword/regex
  matchers, not real NLU — false negatives on rephrased prompts are
  expected and not yet measured (no benchmark exists — Phase 15).

## Validation

- Existing `tests/test_reconcile.py` drift-classification tests must still
  pass after the refactor (behavior-preserving check).
- New tests for `extract_location` and `extract_transformation_cues`.

## Deliverables

- This document.
- `castgraph/prompt/extract.py`.
- Refactored `castgraph/reasoning.py` (no behavior change).
- Updated `run_mvp.py`.
- New tests.

## Quality Gate

- **Technical quality**: refactor removes real duplication without
  changing behavior, verified by the pre-existing test suite passing
  unchanged — passes.
- **Honesty check**: 6 of 12 subtasks marked not implemented with a named
  reason (no consumer / no scenario), not silently skipped — passes.
