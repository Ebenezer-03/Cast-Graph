# PHASE 9 — Generation Context Adapter

## Objective

Create the abstraction between memory and video generators: a
generator-independent context representation, with per-generator adapters
rendering it into whatever format that generator actually expects — proving
(to the extent possible without a real generator) that the memory layer
doesn't need to know generator internals.

## Subtasks

### 1. Define generator-independent context

**Problem**: `build_context` (built earlier, pre-Phase-9-formalization) went
straight from retrieved memory to a text string — there was no
intermediate structured representation, so "generator independence" wasn't
actually tested, just asserted.
**Approach**: split into `build_context_data(retrieved, narrative_context,
location, constraints) -> dict` (the generator-independent structured
form) and separate render functions per generator format.
**Recommended approach**: implemented below.

### 2-7. Canonical identity / appearance / voice / relationship / temporal / world context

All currently folded into the single `canonical` dict per entity (no
per-dimension separation in the structured context yet — mirrors the
memory model's own flat attribute dict, Phase 2). Relationship/temporal/
world context are empty in practice today (no relationship reconciliation,
Phase 6 not wired into context-building, no world rules populated) — the
structured form has slots for them (so adding real content later doesn't
require another format change) but they're empty, not fabricated.

### 8. Constraints / 9. Negative constraints

**Status**: a `constraints: list[str]` slot exists in the structured context
now, but nothing currently populates it (no world rules exist yet — Phase 2
gap). Negative constraints (Phase 7 subtask 8, also unimplemented) would
also land here. Structural placeholder, not a working feature.

### 10. Generator adapters — the real deliverable this phase

**Problem**: with a literal zero real generators integrated, "prove
generator independence" can only be tested by having *at least two*
different rendering targets and confirming the same context data serves
both without the memory/retrieval layers changing.
**Approach**: implemented two renderers: `render_text(context_data)` (the
existing plain-text block, used by `run_mvp.py`) and `render_json(context_data)`
(a structured JSON string, standing in for a hypothetical generator that
takes structured conditioning input rather than a text prompt).
**This is a real, if modest, test of the adapter boundary** — not a claim
that either renderer matches any actual video generator's real input
format (neither has been validated against one, because none exists in
this project).

### 11. Context serialization

`render_json` doubles as this — plain `json.dumps` of the structured
context. No compression/truncation yet (Phase 8 subtask 10 / Phase 12).

### 12. Test generator independence

**Implemented**: a test constructs one `context_data` and asserts both
renderers succeed and each contains the same underlying facts (e.g.
Marcus's canonical voice value appears in both a text block and inside a
JSON structure), demonstrating the memory/retrieval code path is unchanged
regardless of which renderer is chosen downstream.

## Architecture Changes From Previous Phase

- `castgraph/adapters/context.py`: `build_context_data` (structured, new),
  `render_text` (renamed/refactored from the old `build_context`),
  `render_json` (new).
- `run_mvp.py` updated to call `build_context_data` + `render_text`
  (behavior-preserving for its printed output).

## Risks

- Two renderers of one made-up structured format is a weak proxy for real
  generator independence — the actual test (does this work against two
  *real* generator APIs) can't happen without real integrations. Stated
  plainly so this isn't oversold.

## Validation

New test: same `context_data` renders successfully via both `render_text`
and `render_json`, each preserving the same canonical facts.

## Deliverables

- This document.
- Refactored `castgraph/adapters/context.py`.
- Updated `run_mvp.py` call site.
- New test.

## Quality Gate

- **Honesty check**: the "generator independence" claim is scoped to "two
  made-up renderers of one structure," not "validated against real
  generators" — passes, matches Section 24's rule against inventing
  results.
