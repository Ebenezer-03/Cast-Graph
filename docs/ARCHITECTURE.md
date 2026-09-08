# Architecture (MVP scope)

## Problem

Independently generated AI video clips of the same character/world drift:
faces, voices, personalities, relationships change between generations with
no narrative cause. CastGraph is a memory layer that sits between a creator's
prompts and a video generator, remembering just enough compact state to keep
generations consistent, while still allowing *intentional* change.

## Pipeline (as implemented)

```
prompt --> [prompt understanding] --> [selective retrieval] --> context block
                                                                      |
                                                                      v
                                                        (external generator —
                                                         stubbed as synthetic
                                                         clip text in the MVP)
                                                                      |
                                                                      v
clip text --> [observation] --> structured attributes
                                       |
                                       v
                              [identity resolution] (name-based, MVP-only)
                                       |
                                       v
                       [consistency verification] vs canonical state
                                       |
                                 deviation found?
                                  /          \
                                no            yes
                                |              |
                                v              v
                          no-op         [drift attribution] (LLM classifies:
                                          CONSISTENT / EXPECTED_CHANGE /
                                          EXPLAINED_TRANSITION /
                                          TEMPORARY_OVERRIDE /
                                          UNEXPLAINED_DRIFT / AMBIGUOUS)
                                                |
                                                v
                                      [state reconciliation]
                                   (canonical state changes only on
                                    repeated, unexplained evidence —
                                    never on a single new observation)
```

## Memory model (current)

A `MemoryStore` holds `Entity` objects. Each entity has:

- `canonical`: dict of attribute name -> `CanonicalAttribute { value, evidence: [ClipRef], established_at }`
- `exceptions`: list of `Exception { attribute, value, reason, clip_ref, classification }` — deviations
  that were explained (disguise, injury, etc.) and therefore recorded *without*
  overwriting canonical state.
- `unexplained`: list of the same shape, for drift that couldn't be explained —
  surfaced to the user, canonical state still untouched.
- `relationships`: dict of `(other_entity_id) -> relationship state`.

This is intentionally not a graph database, not a vector store, and not an
embedding index — see Principle 2/3 in the original design brief. It is a
plain, storage-agnostic structure serialized to JSON in the MVP; the logical
model is what matters, not the file format.

## Known MVP-scoped limitations (see ROADMAP.md for what's deferred)

- Identity resolution is name-string matching only. No face/voice embeddings
  exist because there's no real video ingested.
- No temporal interval reasoning (Phase 6) — clips are just ordered.
- No memory-budget enforcement/compression (Phase 12) — only a handful of
  synthetic clips exist, not enough volume to need it.
- No aggregate consistency score — per-attribute results are kept separate
  deliberately (a design decision carried over from the original brief, not
  something the MVP simplified away).
