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
| 14. Production Architecture | [PHASE_14](docs/phases/PHASE_14.md) | design only | no product/workload exists — building it would be speculative |
| 15. Benchmarking & Validation | [PHASE_15](docs/phases/PHASE_15.md) | yes, narrow | real 28-clip synthetic benchmark + baselines + one ablation, run and checked in |

See [FINAL_SUMMARY.md](FINAL_SUMMARY.md) for the consolidated architecture,
findings, and honest limitations across all 15 phases.

## Correction from the original plan (still in effect)

The plan called for real LLM calls via the Vercel AI Gateway. No gateway/API
key turned out to be available in this environment (an earlier check
reporting one was present was a shell-quoting bug). The reasoning steps
(prompt understanding, observation extraction, drift classification) are
stubbed deterministically (`StubReasoner`) — see
`decisions/0002-stub-llm-reasoning-for-now.md`. **Every result in this
project, including the Phase 15 benchmark, tests the memory/reconciliation
architecture's plumbing, not whether the reasoning steps generalize to real,
varied language.** Swapping in `GatewayReasoner` (already written) once a
real key exists is a one-line change in each call site.

## What's still genuinely open (not busywork — real next steps)

1. Get a real `AI_GATEWAY_API_KEY`/`ANTHROPIC_API_KEY` working and exercise
   `GatewayReasoner` — this is the single highest-value next step; almost
   nothing about classification quality is validated until this happens.
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
6. Production architecture (Phase 14) — deferred indefinitely, revisit only
   if a real product/workload materializes.
