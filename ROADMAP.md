# Roadmap

Maps the 15-phase master plan to what's actually done. All 15 phases now
have a formal doc under `docs/phases/PHASE_XX.md` (objective, subtasks,
alternatives considered, architecture changes, risks, validation, quality
gate — the full format the original brief required). This file is the
shared-understanding summary; the phase docs are the source of truth for
what each phase actually decided.

## All 15 phases: status

Every phase below has a complete `docs/phases/PHASE_XX.md`. "Real code"
means implemented and tested this session; "design only" means the phase
doc exists but building it would be speculative (no scenario/model/product
to validate against) and was explicitly not faked.

| Phase | Doc | Real code | Note |
|---|---|---|---|
| 1. Research Formalization | [PHASE_01](docs/phases/PHASE_01.md) | no (definitions only) | includes a real, grounded novelty search (Memento, VideoMemory, EntityBench, etc.) |
| 2. World State & Memory Model | [PHASE_02](docs/phases/PHASE_02.md) | yes | relationships/events/world-rules modeled, mostly unexercised |
| 3. Multimodal Observation Engine | [PHASE_03](docs/phases/PHASE_03.md) | text-only | no real video/audio models exist |
| 4. Identity Resolution | [PHASE_04](docs/phases/PHASE_04.md) | name/alias only | no face/voice embeddings exist |
| 5. Canonical State Formation | [PHASE_05](docs/phases/PHASE_05.md) | yes | promotion mechanism (sustained drift -> new canonical) |
| 6. Temporal World-State Engine | [PHASE_06](docs/phases/PHASE_06.md) | yes, narrow | `canonical_state_at` reconstruction; no flashbacks/intervals |
| 7. Prompt Understanding | [PHASE_07](docs/phases/PHASE_07.md) | yes, narrow | keyword/regex location + transformation-cue extraction |
| 8. Selective Memory Retrieval | [PHASE_08](docs/phases/PHASE_08.md) | yes | entity-based only; a small real retrieval-size comparison |
| 9. Generation Context Adapter | [PHASE_09](docs/phases/PHASE_09.md) | yes | structured context + two renderers (text, JSON) |
| 10. Consistency Verification | [PHASE_10](docs/phases/PHASE_10.md) | yes | per-attribute rates + explicitly-caveated naive aggregate |
| 11. Drift Attribution | [PHASE_11](docs/phases/PHASE_11.md) | yes | all 6 classifications now reachable, incl. AMBIGUOUS |
| 12. Consolidation & Compression | [PHASE_12](docs/phases/PHASE_12.md) | yes | evidence-capping + budget enforcement, tested |
| 13. Provenance & Auditability | [PHASE_13](docs/phases/PHASE_13.md) | yes | plain-language `explain()` audit function |
| 14. Production Architecture | [PHASE_14](docs/phases/PHASE_14.md) | **yes, real** | see "Real deployment" below — most of the design doc's speculative caveats are now overtaken by an actual deployment |
| 15. Benchmarking & Validation | [PHASE_15](docs/phases/PHASE_15.md) | yes, narrow | real 28-clip synthetic benchmark + baselines + one ablation, run and checked in |

See [FINAL_SUMMARY.md](FINAL_SUMMARY.md) for the consolidated architecture,
findings, and honest limitations across all 15 phases.

## Real deployment (supersedes the "correction" below for what it covers)

After the phases above were completed, the user asked for a real,
production-grade end-to-end test. This actually happened:

- **Real LLM**: `GeminiReasoner` (`castgraph/reasoning.py`) calls Google
  Gemini directly — decision 0003 explains why Gemini rather than the
  originally-planned Vercel AI Gateway (both Vercel's and Neon's AI
  Gateways require billing info on file; a free Gemini key does not).
  This is the first reasoner in the project ever exercised against a real
  LLM, and it surfaced a real gap Phase 3 had predicted: raw LLM output
  needs normalized-categorical prompting to match canonical string values
  at all (see decision 0003 and `castgraph/reasoning.py`).
- **Real database**: Neon Postgres via the Vercel Marketplace
  (`castgraph/memory/postgres_store.py`), replacing the local-JSON-file
  approach for anything beyond `run_mvp.py`'s own demo run. Required
  adding `MemoryStore.from_dict`/`from_json` — a real, previously-hidden
  gap (serialization was write-only until this).
- **Real deployment**: a live Vercel Python function at
  `https://cast-graph.vercel.app` (`api/generate.py`), backed by the real
  Postgres instance, using `GeminiReasoner` when `GEMINI_API_KEY` is set.
  Verified with a real HTTP request against the live URL: real Gemini
  reasoning, real Postgres persistence, confirmed by reading the row back
  directly from the database.
- **Real, honest limitation hit in the process** (decision 0004): the free
  Gemini key shares quota with the rest of its Google Cloud project and
  was exhausted mid-testing. The system's response to that was itself a
  real, useful proof: the retry logic genuinely retried for ~215s against
  the server's real suggested delay, then returned a clean `500` with the
  actual upstream error — no hang, no crash, and (verified directly) no
  partial/corrupted write to Postgres, because `save_store()` only runs
  after a clip fully succeeds.
- `GatewayReasoner` (Vercel AI Gateway) remains written but unexercised —
  no card was added to Vercel/Neon this session (the user chose the free
  Gemini path instead when asked directly).

## What's still genuinely open (not busywork — real next steps)

1. A dedicated (not shared/reused) Gemini key, or a paid Vercel/Neon AI
   Gateway credential, to get past the free-tier quota constraint (decision
   0004) and run a full multi-request real-LLM consistency+drift test
   against the live deployment (only partially done this session — one
   successful request, one quota-exhausted request, both informative).
2. A real face/voice identity model — the project's biggest capability gap
   relative to its own motivating example (a face changing while the name
   stays the same is currently undetectable).
3. A second character / relationship scenario — `Relationship` (Phase 2)
   has no reconciliation logic yet because nothing has ever needed it.
4. Fix the Phase 15 benchmark's labeling artifact (documented in
   `docs/phases/PHASE_15.md` subtask 10): "consistent" labels need to
   account for legitimate promotion, not just the original value.
5. A real video generator integration, whenever one is chosen — everything
   built so far is designed to plug in behind `castgraph/adapters/` and
   `castgraph/observation/` without changing the memory/drift/retrieval
   core.
6. The rest of Phase 14's design surface (auth, multi-tenant isolation,
   job queues, observability) — still genuinely deferred; one endpoint
   with no auth is a real deployment, not a finished product.
