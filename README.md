# CastGraph

A bounded, persistent memory fabric for keeping characters and world state
consistent across independently generated AI video clips.

This repo is a research/practice exploration, not a shipped product. See
`ROADMAP.md` for what's built, what's stubbed, and what's deferred.

## Status: MVP loop only

No real video generator is wired up. "Clips" in the MVP are synthetic text
descriptions; a real LLM (via the Vercel AI Gateway) performs the reasoning
steps (understanding prompts, extracting observations, classifying drift).
This isolates and tests the memory/reconciliation logic, not video
generation itself.

Run the MVP:

```
pip install -r requirements.txt
python run_mvp.py
```

Requires `AI_GATEWAY_API_KEY` in the environment.

## Layout

- `castgraph/memory/` — canonical + dynamic state model, the persistent fabric itself
- `castgraph/observation/` — turns a generated clip (here: synthetic text) into structured observations
- `castgraph/identity/` — resolves observed entities to known characters
- `castgraph/retrieval/` — selects the minimal relevant memory for a new generation
- `castgraph/temporal/` — temporal state / history reconstruction (stub — later phase)
- `castgraph/drift/` — classifies deviations (consistent / expected / drift / ambiguous / ...)
- `castgraph/adapters/` — generator-independent context representation
- `castgraph/llm/` — thin client for the reasoning-step LLM calls
- `docs/` — architecture notes
- `decisions/` — lightweight decision log (ADR-style)
- `eval/` — benchmarking/ablations (deferred, see ROADMAP.md)
- `scenario/` — the Marcus/Sarah synthetic test scenario
