# 0005 — Add a `force_stub` test-only override to the API

**Context**: A full production-style end-to-end test against the live
deployment (`eval/live_production_test.py`) needs to exercise the real
deployment/Postgres/HTTP path repeatedly. The shared free-tier Gemini
quota (decision 0004) was still exhausted on retry, blocking every clip
with a real 429 regardless of pacing — the quota clearly hadn't reset in
the intervening time, and there's no way to know exactly when it will.

**Options considered**:
- Wait for the quota to reset (unknown timing) — the honest default, but
  blocks validating the deployment's own plumbing (routing, Postgres
  persistence, error handling, response shape) for an indefinite time for
  no good reason, since none of that is actually gated on Gemini.
- Get a different, unshared Gemini key — the real long-term fix (tracked
  in ROADMAP.md), not done this session (no fresh account available to
  hand to the agent, and creating one isn't something to do unprompted).
- Add a narrow, explicit, request-level override to force `StubReasoner`
  regardless of `GEMINI_API_KEY` — **chosen**. This is not a general
  feature; it exists specifically so the rest of the stack (Vercel routing,
  Postgres read/write, the HTTP contract, the pipeline's classification
  branching) can be validated end to end without depending on a third
  party's rate limit.

**Consequences**:
- Any test run using `force_stub: true` is **not** evidence that
  `GeminiReasoner` works against the live deployment — it proves the
  deployment/database/HTTP path, using the same deterministic reasoner
  already validated locally and in the Phase 15 benchmark. This must be
  stated every time such a result is reported, not left implicit.
- `force_stub` is a real, permanent field in the request schema now, not a
  temporary hack removed after use — documented in `api/generate.py`'s
  docstring so it doesn't surprise a future reader. It has no effect
  unless a caller explicitly sets it, so normal (real-LLM) usage is
  unaffected.

**Reversal condition**: none needed — this doesn't need reverting, but if
it's ever misused as "proof the LLM path works," that's a documentation
failure to fix, not a reason to remove the field.
