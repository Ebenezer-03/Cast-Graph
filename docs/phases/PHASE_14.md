# PHASE 14 — Production System Architecture

## Objective

Design (not build) what a production version would need: API, auth, async
processing, storage, caching, retries, observability, deployment — without
destroying the research abstractions built in Phases 1-13.

## Why this phase is design-only, explicitly

Per the grill-session decision recorded in `ROADMAP.md` and reaffirmed
across every phase doc so far: **there is no product, no user, no real
workload, and no generator integration.** Building auth, job queues, or a
deployed API against zero real traffic would produce code that looks
finished but has never been exercised against anything real — exactly the
failure mode Section 24 warns against (presenting unvalidated engineering
as if it were proven). This phase produces the design a real build would
follow, and stops there.

## Subtasks (design only — no implementation)

### 1. API architecture

A REST or RPC surface mirroring `castgraph`'s existing module boundaries:
`POST /projects/{id}/generate` (prompt in, triggers the full
generate→observe→reconcile loop), `GET /projects/{id}/entities/{eid}`,
`GET /projects/{id}/entities/{eid}/attributes/{attr}/explain` (Phase 13's
`explain()`, exposed), `POST /projects/{id}/reviews/{deviation_id}/resolve`
(Section 16's "restore/keep/mark intentional" UX). The module boundaries
already built (`memory`, `observation`, `identity`, `retrieval`, `drift`,
`temporal`, `compression`, `provenance`) map directly to service
responsibilities — this is the main argument for why building the research
version first, rather than an API shell first, was the right order.

### 2. Project isolation

One `MemoryStore` per project (already the model's scope — Phase 2
assumption). Production would need per-project storage keys/tenancy, not a
new logical model.

### 3. Authentication / 4. Authorization

Standard bearer-token auth at the API layer; authorization scoped to
project membership. Nothing in `castgraph`'s core logic needs to know about
users at all — kept that way deliberately (auth is a boundary concern, not
a memory-model concern).

### 5. Asynchronous processing / 6. Job queues

Generation (once a real generator exists) is almost certainly slow/async;
the reconciliation pipeline (`observe -> reconcile`) should run as a
background job triggered when the generator call completes, not inline in
an HTTP request. `castgraph`'s functions are already synchronous, pure(ish),
and side-effect-scoped to one `MemoryStore` — they can be wrapped in a job
handler without modification, which is the point of keeping I/O
(gateway calls) isolated to `castgraph/llm/gateway.py`.

### 7. Model abstraction

Already built: the `Reasoner` protocol (Phase 1/`castgraph/reasoning.py`)
*is* the model abstraction — swapping reasoning backends (or generator
adapters, Phase 9) doesn't touch the memory/retrieval/drift logic.

### 8. Storage abstraction

`MemoryStore.to_json()`/`save()` (decision 0001) is a placeholder, not the
production storage layer — a real deployment would replace JSON-file
persistence with a real datastore behind the same `MemoryStore` interface
(get_or_create, establish, record_exception, etc.), which is exactly why
those methods were kept as the boundary instead of exposing raw dict/JSON
access to callers.

### 9. Caching

Retrieval (Phase 8) is currently cheap enough not to need caching at MVP
scale; would matter once entity counts and evidence volume grow. No
specific caching strategy chosen — premature without real load data.

### 10. Retries/failure recovery

The one real integration point with external failure modes is
`castgraph/llm/gateway.py` (`GatewayError` already distinguishes gateway
failures from other errors) — production would add retry-with-backoff
there specifically, not throughout the codebase.

### 11. Observability

Every `reconcile()` call already returns a structured report (Phase 10) and
every deviation carries a classification/reasoning string — this *is* the
raw material for structured logging/metrics; production would emit these
as events rather than print statements, without changing what's computed.

### 12. Deployment/scaling

Not designed in detail — depends entirely on which real generator(s) get
integrated and their latency/cost profile, neither of which exists yet.

## Additional concerns (versioning, migration, idempotency, concurrency, rate limiting, security, privacy, cost, monitoring, DR)

Each of these depends on decisions (which datastore, which generator, how
many concurrent users) that don't exist yet in this project. Listing them
here without real constraints to design against would produce generic,
unfalsifiable boilerplate advice — exactly what Section 24 warns against
presenting as if it were a real design. **Deferred as a block, not
individually faked.**

## Architecture Changes From Previous Phase

None — this phase is documentation only, by design (see rationale above).

## Risks

- The biggest risk of *this specific phase* is scope creep into building
  speculative infrastructure. Explicitly resisted.

## Validation

N/A — no implementation to validate.

## Deliverables

- This document: a production design that a real build-out would follow,
  explicitly not built.

## Quality Gate

- **Product/systems quality**: the design leans on interfaces already
  proven out in Phases 1-13 (Reasoner, MemoryStore, generator adapters)
  rather than inventing new ones — passes.
- **Honesty check**: no code claims production-readiness; ROADMAP.md
  already states this is out of scope until a real workload exists —
  passes, consistent with the standing decision.
