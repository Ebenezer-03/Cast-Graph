# 0004 — Gemini free-tier quota is a real, external, shared constraint

**Context**: After deploying the real production API (Postgres + Gemini,
decision 0003) and confirming one fully real end-to-end request succeeds
live (`POST https://cast-graph.vercel.app/`, real Gemini reasoning, real
Neon Postgres persistence), a second request against the same deployment
failed with a real `429 RESOURCE_EXHAUSTED` from Gemini: *"Quota exceeded
for metric: generate_content_free_tier_requests, limit: 20"*.

**What this is, concretely**: the reused API key belongs to a shared
Google Cloud project (`gen-lang-client-0558694446`) that already had
several other API keys and, per Google's quota model, free-tier quota is
scoped to the *project*, not the individual key — so this session's own
earlier local smoke-testing (and possibly unrelated prior use of that
project by the account owner) had already consumed most of the day's
allowance before the live deployment was even tested.

**What worked correctly despite this**:
- The retry-with-backoff logic (decision 0003's addition) genuinely
  retried against the real server-provided delay for ~215 seconds before
  giving up — it did not hang forever, and it did not silently swallow the
  failure.
- The API endpoint (`api/generate.py`) returned a clean `500` with the
  actual upstream error message, not a crash or a hang.
- **No partial or corrupted state was written**: `save_store()` is only
  called after `run_clip()` succeeds; the failed second request left
  Postgres holding exactly the first request's data, verified directly
  against the live database.

**This is not a code defect** — it's a real constraint of using a free,
shared-quota LLM credential for anything beyond light, spaced-out testing.
It is the direct, real-world manifestation of the "Latency/cost tradeoffs"
research question (RQ10) and the "budget alerts" concern the `ai-gateway`
skill itself warns about — genuinely observed, not theoretical.

**Consequences**:
- A second real multi-request end-to-end proof (consistency-match, then
  drift/disguise classification, live against the deployed API) is blocked
  until the shared quota resets or a different credential is used — not
  attempted further this session to avoid burning more of a shared,
  external resource pointlessly.
- The one successful live request is real, sufficient evidence that the
  full stack (real LLM reasoning -> real Postgres persistence -> real
  deployed HTTP API) works end to end. It does not prove multi-request
  reconciliation behavior (consistency matching, drift classification)
  against the *live deployment* specifically — that was already proven
  locally (see the `python run_mvp.py` run earlier this session, which
  completed 2 of 4 clips against real Gemini before hitting the same
  shared quota) and via the Phase 15 benchmark (against `StubReasoner`).

**Reversal condition**: revisit if/when a dedicated (not shared/reused)
Gemini key, or a paid Vercel/Neon AI Gateway credential, becomes available.
