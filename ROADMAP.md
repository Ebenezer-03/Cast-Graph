# Roadmap

Maps the 15-phase master plan to what's actually done, and to rough future
sessions. This file is the shared-understanding anchor for the project —
update it whenever scope is added, cut, or deferred.

## Done (this session)

- Phase 1 (Research Formalization) — informal only: problem statement lives
  in `docs/ARCHITECTURE.md`, not a standalone formal doc.
- Phase 2 (World State & Memory Model) — minimal version in `castgraph/memory/`:
  canonical attributes, evidence, exceptions/overrides. No confidence decay,
  no versioning yet.
- Phase 3 (Observation Engine) — text-only: `castgraph/observation/` extracts
  structured attributes from a synthetic clip description via LLM. No real
  video/audio ingestion (no generator exists to ingest from).
- Phase 4 (Identity Resolution) — reduced to name-based matching in
  `castgraph/identity/`. Documented as a known limitation: no face/voice
  embeddings exist in a text-only MVP.
- Phase 5 (Canonical State Formation) — basic reconciliation: canonical
  attributes are not overwritten by a single new observation; repeated
  evidence is what promotes a value.
- Phase 7 (Prompt Understanding) — minimal entity/intent extraction via LLM
  in `castgraph/adapters/` (folded in, not a separate module yet).
- Phase 8 (Selective Retrieval) — basic entity-based retrieval in
  `castgraph/retrieval/`, no semantic/embedding retrieval yet.
- Phase 9 (Generation Context Adapter) — a single generator-agnostic text
  context block; no multi-generator adapters yet (nothing to adapt to).
- Phase 10 (Consistency Verification) — per-attribute comparison, no
  aggregate scoring formula yet.
- Phase 11 (Drift Attribution) — the core reasoning step: LLM classifies
  deviations into CONSISTENT / EXPECTED_CHANGE / EXPLAINED_TRANSITION /
  TEMPORARY_OVERRIDE / UNEXPLAINED_DRIFT / AMBIGUOUS given narrative context.

## Explicitly deferred (not built, not faked)

- **Phase 6 (Temporal World-State Engine)** — `castgraph/temporal/` is a stub.
  Needs real event ordering across more than a handful of clips to be worth
  designing properly.
- **Phase 12 (Consolidation/Compression)** — only trivial evidence dedup
  exists. Real compression-vs-consistency tradeoffs need more memory volume
  than a 4-clip MVP produces.
- **Phase 13 (Provenance/Auditability)** — evidence references (clip id +
  span) are stored, but no audit UI, no correction workflow.
- **Phase 14 (Production Architecture)** — out of scope indefinitely. No
  product, no real workload, no users. Revisit only if that changes.
- **Phase 15 (Benchmarking/Validation)**, the ablation studies, the
  memory-budget matrix, and the long-horizon experiment — all require either
  a real video generator or a much larger synthetic dataset to produce
  numbers that mean anything. Doing them now would be theater. Needs a
  dedicated session with a real dataset design first.
- **Novelty/literature analysis** — needs real web/paper research, not
  memorized citations. Dedicated research-pass session, not this one.
- **Full 20-doc engineering doc set** — collapsed into this README +
  `ROADMAP.md` + `docs/ARCHITECTURE.md` + `decisions/`. Will split out
  individual docs only if/when a section outgrows a shared file.

## Rough future sessions

1. Temporal world-state engine (Phase 6) + versioned canonical state (extend Phase 5).
2. Real selective retrieval with a relevance-scoring comparison (full history vs
   naive vs structured), still against synthetic clips.
3. Consolidation/compression experiment once there's enough synthetic memory
   volume to compress meaningfully.
4. Dedicated research pass: literature/novelty analysis with real citations.
5. Benchmark dataset design + drift-injection scenarios (Phase 15 prerequisite).
6. Only after 1-5: revisit whether production architecture is warranted.
