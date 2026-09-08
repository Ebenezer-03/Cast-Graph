# 0003 — Use Gemini directly (not Vercel AI Gateway) for real LLM calls

**Context**: The user asked for a fully real, production-grade end-to-end
test with real LLM calls. Decision 0002 had deferred real calls entirely
for lack of a working key. This session tried to get one working for real.

**What was tried**:
- Vercel AI Gateway (the originally-planned path, per the grill-session
  decision): auth via `VERCEL_OIDC_TOKEN` works, but Vercel returns
  `403 customer_verification_required` — a credit card must be on file
  before *any* request is served, even against the free $5/month credit.
- Neon's AI Gateway (available since Neon Postgres was provisioned this
  session): the gateway is blocked entirely on Neon's free plan — a paid
  Neon plan is required just to provision it, per the `neon-ai-gateway`
  skill's own documented gating.
- The user was asked directly and chose not to add a card to either
  account for this project right now.

**Chosen approach**: a free Google AI Studio (Gemini) API key — genuinely
free tier, no billing info required, verified with a real
`generateContent` call (`gemini-3.6-flash`, HTTP 200, real completion).
`castgraph/llm/gemini.py` is a new, minimal REST client mirroring
`castgraph/llm/gateway.py`'s shape (`complete`/`complete_json`); a new
`GeminiReasoner` in `castgraph/reasoning.py` implements the `Reasoner`
protocol against it.

**Consequences**:
- `GeminiReasoner` is the first reasoner in this project ever exercised
  against a real LLM — every claim in `docs/phases/PHASE_15.md` and
  elsewhere about "no reasoning step has been validated against real
  language" is updated by this decision for the parts that now run through
  Gemini; it does **not** retroactively validate `GatewayReasoner`, which
  remains unexercised (nothing about the Vercel Gateway path changed).
- `GatewayReasoner` (Vercel AI Gateway) is kept, unexercised, as the
  documented path for if/when a card is added later — no code removed,
  per the reversal-condition discipline established in decision 0002.
- Free-tier Gemini keys carry rate limits not investigated here; this is
  a real risk for a production deployment under real load, not just a
  cost concern.

**Reversal condition**: if a card is later added to the Vercel or Neon
account, `GatewayReasoner` can be swapped in the same way `GeminiReasoner`
was swapped in for `StubReasoner` — a one-line change per call site.
