# CastGraph

A bounded, persistent memory fabric for keeping characters and world state
consistent across independently generated AI video clips.

This repo started as a research/practice exploration; it now also has a
real, deployed production slice. See `ROADMAP.md` for the full picture and
`decisions/` for why each infrastructure choice was made.

## Status: real deployment, real LLM, real database — one generator still stubbed

No real video generator is wired up (that part of the pipeline is still
synthetic text — see `scenario/`). Everything else is real:

- **Reasoning**: `GeminiReasoner` calls Google Gemini directly for real
  (prompt understanding, observation extraction, drift classification) —
  see `decisions/0003`. Falls back to deterministic `StubReasoner` (no
  API key needed) when `GEMINI_API_KEY` isn't set.
- **Storage**: Neon Postgres (`castgraph/memory/postgres_store.py`), not a
  local JSON file — provisioned via the Vercel Marketplace.
- **Deployment**: a real, live Vercel Python function at
  `https://cast-graph.vercel.app` (`POST /` runs one clip through the full
  loop for a project; `GET /` is a health check).

**Known real constraint** (decision 0004): the Gemini key is a free-tier
key sharing quota with the rest of the account's Google Cloud project —
expect `429` responses under sustained use. The API surfaces this as a
clean `500` with the real upstream error, not a hang or a crash.

### Run locally

```
pip install -r requirements-dev.txt
python run_mvp.py          # uses GeminiReasoner if GEMINI_API_KEY is set, else StubReasoner
pytest tests/               # requires DATABASE_URL for the Postgres integration tests to run (else they're skipped)
```

### Run the live deployment

```
curl -X POST https://cast-graph.vercel.app/ \
  -H "Content-Type: application/json" \
  -d '{"project_id":"demo","character":"Marcus","clip_id":"ep1",
       "prompt":"Marcus talks to Sarah at the docks.",
       "clip_text":"Marcus, black hair, deep rough voice, talks to Sarah at the docks."}'
```

## Layout

- `castgraph/memory/` — canonical + dynamic state model, plus Postgres persistence (`postgres_store.py`)
- `castgraph/observation/` — turns a generated clip (here: synthetic text) into structured observations
- `castgraph/identity/` — resolves observed entities to known characters
- `castgraph/retrieval/` — selects the minimal relevant memory for a new generation
- `castgraph/temporal/` — reconstructs canonical state as of a given clip
- `castgraph/drift/` — classifies deviations (consistent / expected / drift / ambiguous / ...), with promotion for sustained change
- `castgraph/consistency/` — per-attribute consistency reporting
- `castgraph/compression/` — evidence-list compression and memory-budget enforcement
- `castgraph/provenance/` — plain-language "why is this canonical" audit
- `castgraph/adapters/` — generator-independent context representation, with pluggable renderers
- `castgraph/prompt/` — prompt-side extraction (location, transformation cues)
- `castgraph/llm/` — real LLM clients (`gemini.py`, exercised; `gateway.py` for Vercel AI Gateway, unexercised — see decision 0003)
- `castgraph/reasoning.py` — the `Reasoner` seam: `GeminiReasoner` (real), `GatewayReasoner` (real, unexercised), `StubReasoner` (deterministic)
- `castgraph/pipeline.py` — the shared per-clip pipeline step used by `run_mvp.py`, `eval/run_benchmark.py`, and `api/generate.py`
- `api/` — the deployed Vercel Python function
- `docs/phases/` — all 15 phases of the original design brief, each with its own doc
- `decisions/` — ADR-style decision log
- `eval/` — the drift benchmark, baselines, and one real ablation (see `docs/phases/PHASE_15.md`)
- `scenario/` — the Marcus/Sarah synthetic test scenario
