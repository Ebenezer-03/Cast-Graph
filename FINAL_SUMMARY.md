# Final Summary — CastGraph, Phases 1-15

This consolidates the 15 phase docs (`docs/phases/PHASE_01.md`-`PHASE_15.md`)
into the brief's requested final-document shape, kept short by design:
detail lives in the phase docs and decision log, not duplicated here.

## Executive summary

CastGraph is a bounded, persistent memory layer for keeping characters and
world state consistent across independently generated AI video clips. This
project built the MVP version of that idea end-to-end — canonical state,
evidence, identity resolution, selective retrieval, drift classification,
promotion, compression, provenance, and a small honest benchmark — using
synthetic text clips in place of a real video generator (none is
integrated). Every phase from the original 15-phase brief has a formal doc;
roughly half include real, tested code, the rest are design-only with the
reason stated (no model, no scenario, or no product to validate against).

## Problem statement / research gap / novelty analysis

See `docs/phases/PHASE_01.md`. Short version: AI video generation drifts
character identity/attributes across independently generated clips with no
persistent memory. A real (if narrow) literature search found active,
similar work (Memento, VideoMemory, EntityBench, and several KV-cache/
latent-history compression systems) — all operating *inside* one
generator's session/pipeline. CastGraph's stated, **unvalidated**
positioning is being external to any single generator/session, structured
around canonical-state-with-exceptions rather than a similarity-retrieval
bank, and built around explicit intentional-vs-unexplained deviation
classification with provenance. Not benchmarked against those systems.

## System goals / non-goals

**Goals**: bounded memory, canonical state that isn't blindly overwritten,
selective retrieval, generator-agnostic context, explainable drift
classification, provenance. **Non-goals** (explicitly, per the grill-session
decisions and Phase 14): production readiness, multi-tenant deployment,
real-time performance, any specific generator integration.

## System architecture

See `docs/ARCHITECTURE.md` for the pipeline diagram. In one line: prompt ->
[understanding + selective retrieval] -> [generation, stubbed] -> [observe]
-> [identity resolve] -> [reconcile: verify + classify + promote] ->
persistent memory -> next prompt.

## Memory / observation / identity / temporal / retrieval / consistency /
## drift / consolidation / compression / provenance models

Each has its own phase doc (2, 3, 4, 6, 8, 10, 11, 12, 13 respectively) and
its own module (`castgraph/memory`, `observation`, `identity`, `temporal`,
`retrieval`, `consistency`, `drift`, `compression`, `provenance`). The
`Reasoner` protocol (`castgraph/reasoning.py`) is the one seam every
judgment call passes through — `StubReasoner` (deterministic, used
throughout this project) or `GatewayReasoner` (real, written, unexercised).

## Generation adapter

`castgraph/adapters/` — a generator-independent structured context, with
two renderers (text, JSON) proving the adapter boundary works, though
neither has been validated against a real generator (Phase 9).

## APIs / data contracts / module boundaries

No HTTP API exists (Phase 14, design-only). The Python module boundaries
*are* the current API — each `castgraph/<module>/__init__.py` exports the
stable surface; internals can change without touching call sites, which is
exactly the property Phase 14's future API design leans on.

## Deployment / security / observability / testing / evaluation

Deployment/security: not applicable, no deployment exists (Phase 14).
Testing: 32 tests across 10 test files, all passing, run via `pytest tests/`.
Evaluation: `eval/` — a 28-clip synthetic drift benchmark with 2 real
baselines and 1 ablation, run and checked into
`eval/results/benchmark_report.json` (Phase 15).

## Ablation plan / memory-budget experiments / long-horizon experiments

Ablation: promotion-enabled vs. promotion-disabled, run for real (Phase 15).
Memory-budget: mechanism (`enforce_budget`) built and tested (Phase 12),
not run as the full 10KB-10MB matrix (no data volume to make it meaningful).
Long-horizon: 28 clips is the long-horizon test that's actually buildable
right now; not the 100-500 clip points from the brief.

## Failure modes / limitations

The single biggest one, stated plainly: **no reasoning step has been
exercised against a real LLM.** Every classification, extraction, and
understanding result in this entire project comes from `StubReasoner`, a
keyword matcher fitted to one scenario's vocabulary. Everything built is
real *plumbing*; whether the *judgment calls* generalize is completely
unvalidated. Second: no real face/voice identity model exists, so the
project's own motivating example (a face changing while the name prompt
stays the same) is currently undetectable. Third: `Relationship` has no
reconciliation logic — only attribute-level consistency is actually
checked. Full list of open items: `ROADMAP.md`.

## Research contributions (unvalidated, stated as such)

A positioning claim, not a proven one (Phase 1): canonical-state-with-
exceptions plus explicit deviation classification and provenance, external
to any one generator's session. No benchmark against the related systems
found in Phase 1's literature search has been run.

## Cost model / scaling strategy

Not designed (Phase 14) — no real generator cost profile exists yet
(`StubReasoner` has zero marginal cost; `GatewayReasoner`'s real cost is
unmeasured, decision 0002).

## Implementation roadmap

See `ROADMAP.md`'s "What's still genuinely open" section — getting a real
LLM key working and exercising `GatewayReasoner` is the single highest-value
next step; almost nothing about classification quality is validated without it.
