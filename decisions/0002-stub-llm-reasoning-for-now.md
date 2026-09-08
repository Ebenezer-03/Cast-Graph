# 0002 — Stub the reasoning-step LLM calls until a real key exists

**Context**: The plan called for real LLM calls (via Vercel AI Gateway) for
prompt understanding, observation extraction, and drift classification.
No `AI_GATEWAY_API_KEY` / `ANTHROPIC_API_KEY` is actually available in this
environment (an earlier check reported one was present — that was a shell
quoting bug, corrected after a failed smoke test against the real gateway).

**Options considered**:
- Block until a key is provided — rejected: no reason the memory/reconciliation
  logic itself can't be built and demonstrated now.
- Link a Vercel project and pull env — deferred, not refused; can be done
  later without changing the code, only which `Reasoner` implementation is
  selected.
- Stub reasoning steps behind an interface, swap in the real client later —
  **chosen**.

**Chosen approach**: `castgraph/reasoning.py` defines a `Reasoner` protocol
(`extract_observation`, `understand_prompt`, `classify_drift`). Two
implementations exist:
- `StubReasoner` — deterministic, rule-based, used by default right now.
- `GatewayReasoner` — calls `castgraph.llm.gateway.complete_json`, ready to
  use the moment a key exists; not exercised yet.

Every call site takes a `Reasoner` as a parameter (no hidden global), so
swapping is a one-line change in `run_mvp.py`, not a rewrite.

**Consequences**: today's demo proves the *memory/reconciliation* architecture
works end-to-end, but does **not** prove the reasoning steps (identity
matching nuance, drift classification nuance) work on real model output —
that remains unvalidated until `GatewayReasoner` is actually exercised.
This is a real limitation, not a cosmetic one: `StubReasoner`'s rules were
written to fit the demo scenario and should not be read as evidence the
approach generalizes.

**Reversal condition**: swap `StubReasoner` -> `GatewayReasoner` in
`run_mvp.py` as soon as a real key is available. No other file should need
to change.
