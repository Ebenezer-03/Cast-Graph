# PHASE 3 — Multimodal Observation Engine

## Objective

Design the system that turns generated content into structured
observations, keeping RAW MEDIA, OBSERVATIONS, and MEMORY explicitly
distinct (Principle 1), and decide what's retained vs. discarded.

## Assumptions

- **ASSUMPTION, load-bearing**: this phase is designed for real video (shot
  detection, face/voice analysis) but *implemented* only for text, because
  no generator/vision/audio model is wired up (per the grill session
  decision). Every subtask below states the real-video design AND the
  text-only stand-in, not one or the other.

## Subtasks

### 1. Video ingestion

**Problem**: get raw frames/audio into a processable form.
**Approach (real)**: standard decode (ffmpeg or equivalent) into frame
sequence + audio track.
**Text-only stand-in**: the "clip" is already structured text (`scenario/marcus_sarah.py`);
"ingestion" is just reading the string — implemented, trivial.
**Recommended approach**: keep the seam (`observe()`'s `clip_text` param) so
swapping in a real decoder only changes what produces that string, not the
function signature. **Risk**: this seam assumes ingestion always ends in
something summarizable as text before extraction — real vision models
operating on frames directly would need a different signature (frames in,
not text in). Flagged, not resolved — a real decision needs a real vision
model to design against.

### 2. Scene segmentation / 3. Shot detection

**Problem**: a clip may contain multiple scenes/shots, each needing separate
observation.
**Approach (real)**: shot-boundary detection (histogram/embedding
discontinuity) then per-shot processing.
**Text-only stand-in**: each scenario clip is authored as one shot; no
segmentation exists.
**Recommended approach**: deferred — no multi-shot synthetic scenario has
been built to design against yet (see ROADMAP.md future session). Building
segmentation logic now, untested against real multi-shot content, would be
speculative code with no way to validate it.

### 4. Character detection / 5. Face analysis / 6. Voice/speaker analysis / 7. Appearance extraction

**Problem**: extract *who* is in frame and *what they look/sound like*.
**Approach (real)**: face detection + embedding, speaker diarization +
voice embedding, attribute classifiers (hair/clothing/age) per detected
person.
**Text-only stand-in**: `StubReasoner.extract_observation` / eventually
`GatewayReasoner.extract_observation` reads the character name and
attribute keywords directly out of text — there is no actual visual/audio
analysis, just text parsing.
**Alternatives considered for the real version**: a single end-to-end
multimodal model doing detection+attribute-extraction jointly vs. a
pipeline of specialized models (face embedding model + separate attribute
classifier + separate ASR/speaker-id) — **not decided**, this needs real
model benchmarking against real generated video, which doesn't exist in
this project yet. Recording both options rather than picking one
speculatively.
**Recommended approach for now**: keep `extract_observation`'s signature
(`clip_text/frames, character_name -> attributes dict`) generic enough that
either approach can sit behind it later.

### 8. Speech/dialogue analysis

**Problem**: what a character *says* (not just how they sound) can carry
personality/relationship signal.
**Approach (real)**: ASR transcript + dialogue-act/sentiment analysis.
**Text-only stand-in**: none — the synthetic clips don't include dialogue
transcripts, only descriptions. **Named gap**: `StubReasoner` cannot
currently detect a personality shift expressed only through *what* a
character says (only through described attributes like "sarcastic").

### 9. Behavior/personality signals

Folded into attribute extraction above (`personality` key) — same
limitations apply.

### 10. Relationship/event extraction

**Problem**: detect *that* an interaction/relationship-relevant event
happened, not just entity attributes.
**Approach (real + stand-in)**: not implemented at all yet — this is the
`Event`/`Relationship` gap already named in Phase 2. `observe()` currently
returns only attribute observations, never event/relationship observations.
**Recommended approach**: extend `extract_observation` (or add a sibling
function `extract_events`) once a scenario with an actual relationship
transition exists to validate against — speculative otherwise.

### 11. Confidence estimation

**Problem**: real extraction models produce calibrated (or at least
comparable) confidence scores; text-keyword matching does not.
**Approach (real)**: propagate the model's own confidence/logit as the
observation's confidence.
**Text-only stand-in**: `StubReasoner` returns no confidence at all
(implicitly 1.0). **This is a real, named limitation**: `CanonicalAttribute.confidence`
(Phase 2) can only be as meaningful as the observation confidence feeding
it, and today that's not real. Recommended fix, deferred: `extract_observation`'s
return contract should become `{attribute: (value, confidence)}` once a
real extractor exists to actually vary that number meaningfully.

### 12. Observation normalization

**Problem**: raw extraction might produce "deep voice" vs. "deep, rough
voice" vs. "his voice is deep" for the same underlying fact — canonical
matching (`==` in `reconcile()`) needs normalized values or it will
false-positive on drift.
**Approach**: a controlled vocabulary/normalization step between extraction
and reconciliation (e.g. mapping free text to a fixed attribute-value enum
per attribute).
**Alternatives**: similarity-based matching instead of exact equality (embed
both values, compare distance) — more robust to phrasing, rejected for now
because it reintroduces the "not everything is embeddings" tension
(Principle 3) for what should be a small, controllable value space per
attribute.
**Recommended approach**: `StubReasoner` already normalizes implicitly by
only ever emitting fixed strings (`"deep/rough"`, `"soft/high"`) — this
works *only* because the stub is hand-written to do so. **A real
`GatewayReasoner` has no such guarantee** and will likely need an explicit
normalization step (e.g. asking the LLM to pick from a fixed enum in its
extraction prompt) before this reaches production quality. Flagged as a
concrete, non-speculative next step for `GatewayReasoner.extract_observation`.

## RAW MEDIA vs. OBSERVATIONS vs. MEMORY (explicit statement, per brief)

- **RAW MEDIA**: the clip itself (real: video/audio file; here: the
  `clip_text` string in `scenario/marcus_sarah.py`). Never stored in
  `MemoryStore` — only a ≤120-char excerpt is kept (`ClipRef.excerpt`),
  for provenance, not reconstruction.
- **OBSERVATIONS**: the output of `observe()` — a plain dict of attribute ->
  value for one clip, one character. Transient — not persisted on its own,
  only fed into `reconcile()`.
- **MEMORY**: `MemoryStore`'s canonical/exception/unexplained state —
  compact, persistent, the only thing that survives across `run_mvp.py`
  invocations (once serialized via `save()`).

This three-way split was already implicit in the code; this phase makes it
explicit and confirms nothing violates it (checked: no full clip text is
ever written into `MemoryStore`).

## Architecture Changes From Previous Phase

No code changes this phase beyond what's already true — Phase 3's real
value is naming which subtasks are genuinely built (4-7, partially) vs.
structurally impossible to validate right now (1-3, 8-9, 11-12) without
real media/models. Building speculative code for the unvalidatable subtasks
would violate the "don't invent results" rule as much as inventing a result
would.

## Risks

- **Biggest risk in the whole project**: `StubReasoner`'s extraction is
  hand-fitted to the exact vocabulary in `scenario/marcus_sarah.py`. Any
  claim that "observation extraction works" is true only for that fixture
  and should not be generalized.
- Normalization (subtask 12) is unsolved for the real (`GatewayReasoner`)
  path — likely to surface false UNEXPLAINED_DRIFT from phrasing differences
  alone once real LLM calls are exercised, unless fixed before that point.

## Validation

None beyond the existing `tests/test_reconcile.py` (which tests
reconciliation given fixed observation dicts, not extraction itself — no
test exists for `extract_observation` because there's no ground truth to
check it against beyond the hand-written stub matching its own hand-written
rules, which would be a circular test).

## Deliverables

- This document — an honest map of what Phase 3 requires vs. what exists.

## Quality Gate

- **Failure-mode check**: does this collapse into "just video analysis"?
  No — the phase explicitly separates observation (transient) from memory
  (persistent), and named the normalization gap that a naive "just run
  extraction" approach would silently hide.
- **Honesty check**: subtasks 1-3, 8-9, 11-12 are marked deferred/unsolved
  rather than papered over with placeholder code that looks more finished
  than it is — passes.
