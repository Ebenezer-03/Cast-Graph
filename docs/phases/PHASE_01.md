# PHASE 1 — Research Formalization

## Objective

Precisely define the consistency problem CastGraph addresses, formalize what
"persistent memory" and "consistency" mean in this system, distinguish
intentional from unexplained change, state memory constraints as a research
variable (not a fixed guarantee), and ground the project's novelty claim in
an honest gap analysis against real, found literature — not an assumption
that nothing like this exists.

## Assumptions

- **ASSUMPTION**: the creator interacts with a video generator through
  discrete, independently-triggered generations (clip-by-clip), not one
  continuous autoregressive session. This is what makes the problem
  different from in-model memory (see Gap Analysis) and is the premise the
  rest of the design rests on. If the target generator is actually a single
  long autoregressive run, most of this project's contribution collapses
  into what Section 3 already does internally.
- **ASSUMPTION**: "the creator" is a single individual/small team authoring
  a serialized piece of content (episodes/clips), not a multi-tenant
  platform with many concurrent authors on one world (that's a Phase 14
  concern, explicitly deferred).

## Research Questions (from the brief, kept as-is; no better ones surfaced yet)

RQ1-RQ10 as stated in the master brief. Restated compactly for reference:
memory-boundedness vs. consistency (RQ1, RQ2), selective retrieval vs. full
history (RQ3), structured vs. unstructured memory (RQ4), intentional vs.
unexplained change detection (RQ5), consolidation without information loss
(RQ6), provenance's effect on trust/correction (RQ7), generator-agnosticism
(RQ8), long-horizon degradation (RQ9), latency/cost tradeoffs (RQ10).

## Subtasks

### 1. Precisely define the consistency problem

**Problem**: "Consistency" is used loosely in the brief (identity, voice,
appearance, relationships, world rules, all folded into one word).
**Approach**: split it into independently measurable sub-consistencies
(see subtasks 4-7) rather than one property, so failures in one dimension
don't hide behind success in another.
**Alternatives considered**: (a) one aggregate consistency score computed
early — rejected, matches the brief's own Phase 10 warning against hiding
weaknesses behind one score; (b) leave it undefined until Phase 10 — rejected,
downstream phases (retrieval, drift attribution) need the taxonomy now to
know what they're preserving.
**Recommended approach**: consistency = the property that, absent an
intentional or narratively-explained change, an entity's or relationship's
canonical attributes are reproduced (exactly for discrete attributes,
within a stated tolerance for continuous/perceptual ones — e.g. an ASR/vision
similarity threshold) in every subsequent independent generation referencing
that entity.
**Implementation implications**: the memory model must store attributes
per-dimension (subtask 4-7 schema), not a single blob.
**Research implications**: this is a **design hypothesis**, not a proven
definition — an open question is whether creators actually want strict
attribute reproduction vs. "recognizably the same character" (a much looser,
harder-to-formalize bar). Flagged for future user research; not resolved here.

### 2. Define what "persistent memory" means in this system

**Problem**: distinguish memory that survives across independent generations
from memory that is only within-generation (a single model's context window
or KV-cache).
**Approach**: persistent memory = state that exists *outside* any single
generation call and *outside* any single generator's internal
representation, addressable and retrievable before the next call.
**Alternatives**: rely on generator-native long-context/KV-cache memory (as
Echo-Forcing, FramePack-style compression, and Future Forcing do internally,
per the gap analysis below) — rejected as the *sole* mechanism because it
ties consistency to one generator/session and disappears the moment a
different tool, a new session, or a different model version is used.
**Recommended approach**: an external, generator-agnostic store (Principle 8)
is the persistent layer; in-generator memory (if any) is out of scope and
orthogonal.
**Implementation implications**: `castgraph/memory/` already reflects this
(entities exist independent of any `run_mvp.py` invocation, serializable to
disk).
**Research implications**: this framing is what differentiates the project
from most literature found below, which operates *inside* one generation
pipeline.

### 3. Define what "consistency" means (formally)

**Problem**: need a check-able, not just descriptive, definition.
**Approach**: for attribute `a` of entity `e`, given canonical value `c`,
and observed value `o` in a new generation, define:
`consistent(e, a) := match(c, o) OR classification(deviation) IN
{EXPECTED_CHANGE, EXPLAINED_TRANSITION, TEMPORARY_OVERRIDE, CONSISTENT}`.
`match` is exact equality for categorical attributes, a similarity threshold
for continuous/perceptual ones (voice embedding distance, face similarity
score) — **the threshold values themselves are an ENGINEERING ASSUMPTION,
unset and unvalidated** until real perceptual models are wired up (Phase 3+).
**Alternatives**: probabilistic consistency (Bayesian belief over attribute
value) — more principled, rejected for MVP as unnecessary complexity before
the categorical case is validated.
**Recommended approach**: start categorical (as built), add continuous
similarity metrics only when real observation models exist.
**Implementation implications**: `castgraph/drift/reconcile.py`'s
`canonical_value == observed_value` check is the categorical case only;
this is a known simplification, not a design decision expected to survive
Phase 10's real consistency verification engine.
**Research implications**: the threshold-calibration question (RQ1/RQ2)
cannot be answered without real perceptual models and real held-out video —
neither exists yet.

### 4. Define identity consistency

**Problem**: "is this the same character" is itself unsolved in general
(see EntityBench/VideoMemory below — this is an open research problem, not
solved by this project).
**Approach**: define identity consistency as a *downstream user* of identity
resolution (Phase 4), not identity resolution itself — Phase 1 only needs
the property statement: entity `e`'s identity is consistent across clips
`i, j` if identity resolution assigns the same entity id to the character
observed in both, with confidence above a stated threshold.
**Alternatives**: define identity consistency purely in terms of raw
similarity metrics (face/voice embedding distance) — rejected at this phase
because it conflates identity *resolution* (Phase 4) with identity
*consistency* (a property resolution should preserve).
**Recommended approach**: keep the two concepts separate as above.
**Implementation implications**: `castgraph/identity/resolve.py` is
explicitly named-based only (MVP) — real identity consistency cannot be
claimed until embedding-based resolution exists.
**Research implications**: RQ1 is unanswerable for identity specifically
until Phase 4 is built for real.

### 5. Define attribute consistency

**Problem**: appearance/voice/clothing attributes change legitimately
(costume, aging) and illegitimately (drift) — the definition must not
conflate the two.
**Approach**: attribute consistency is defined relative to the
canonical/exception split (subtask 8): an attribute is consistent if its
observed value matches canonical OR falls into a recorded, classified
exception.
**Alternatives**: define consistency without exceptions (strict match only)
— rejected, contradicts Principle 6 (context determines valid change) and
would misclassify every legitimate costume change as a failure.
**Recommended approach**: as stated; implemented in `castgraph/drift/reconcile.py`.
**Implementation implications**: none beyond what's built.
**Research implications**: none new.

### 6. Define relationship consistency

**Problem**: relationships (Marcus/Sarah) are relational state between two
entities, not an attribute of one — needs its own representation.
**Approach**: relationship consistency = the relationship-state edge between
two entity ids is reproduced or validly transitioned (e.g. "strangers" ->
"allies" is a valid narrative transition, not drift) across generations.
**Alternatives**: model relationships as just another attribute on one
entity (e.g. `Marcus.relationship_to_sarah`) — rejected: loses the fact that
a relationship transition is a joint event with its own evidence and
potentially its own narrative cause, and doesn't generalize to many-entity
relationships.
**Recommended approach**: relationships live in `Entity.relationships` as a
first-class dict today (MVP: unstructured string), should become its own
typed sub-model with evidence/classification like attributes once a second
relationship-bearing scenario exists to design against.
**Implementation implications**: `Entity.relationships: dict[str, str]` in
`castgraph/memory/model.py` is a placeholder, not yet exercised by
`reconcile()` — **this is a real gap**: relationship drift is not currently
detectable by the MVP at all. Recorded here rather than hidden.
**Research implications**: RQ5 (intentional vs. unexplained) is currently
answered only for attributes, not relationships.

### 7. Define narrative/world consistency

**Problem**: world rules (e.g. "magic doesn't exist in this world") and
location/object state are structurally similar to character attributes but
scoped to non-character entities.
**Approach**: model locations, objects, and world rules as entities in the
same `MemoryStore`, just with a different `id` namespace and no identity
resolution needed (a location's name *is* its identity, generally).
**Alternatives**: a wholly separate "world state" subsystem — rejected,
duplicates the canonical/exception/evidence machinery already built for
characters for no clear benefit.
**Recommended approach**: reuse `Entity`/`MemoryStore` for all entity types;
add an `entity_type` field when a second entity type is actually built
(currently only `Marcus` exists — building this now would be speculative).
**Implementation implications**: not built; `Entity` has no `entity_type`
field yet. Flagged as a near-term addition, not urgent for a 1-character MVP.
**Research implications**: none new.

### 8. Define intentional versus unexplained change

**Problem**: the crux of the whole project — how is this actually decided.
**Approach**: intentional/explained change = a deviation for which the
prompt or scene context, when reasoned over, yields a narrative or
production justification (disguise, injury, aging, time jump, etc.);
unexplained = no such justification is found.
**Alternatives**: a fixed keyword/rule list (what `StubReasoner` currently
does) — acceptable as a temporary stand-in, explicitly **not** the intended
final mechanism; a learned classifier trained on labeled drift/change
examples — the eventual likely direction, but requires a labeled dataset
that doesn't exist yet (Phase 15 prerequisite).
**Recommended approach**: LLM-as-classifier over (canonical value, observed
value, narrative context) is the current best-available approach given no
training data exists; this is a **design hypothesis**, unvalidated against
real ambiguous cases (the brief's own AMBIGUOUS category exists precisely
because this is expected to fail sometimes).
**Implementation implications**: `castgraph/reasoning.py`'s
`classify_drift` is the seam; `GatewayReasoner` is the real (unexercised)
implementation, `StubReasoner` the keyword-rule stand-in.
**Research implications**: RQ5 is the central open research question of
the entire project and is not resolved by having a classifier — it's
resolved only by evaluating that classifier against a labeled benchmark,
which is Phase 15, not done yet.

### 9. Formalize memory constraints

**Problem**: the brief mandates budgets from 10KB-10MB as an experimental
variable, not a fixed target.
**Approach**: define `MemorySize(store) = len(serialize(store))` in bytes
(already implemented as `MemoryStore.size_bytes()`), and treat the
optimization as: maximize a consistency metric subject to
`MemorySize <= Budget`, across the budget matrix — **not yet run** (needs
Phase 12's compression strategies and Phase 15's evaluation harness first;
today's 4-clip demo produces ~3KB, uninformative about saturation behavior
at any budget above the smallest one).
**Alternatives**: token-count budget instead of byte-count — worth tracking
in parallel later (token budget determines generation-context cost, byte
budget determines storage cost; they're not the same variable) — noted as
a future refinement, not resolved now.
**Recommended approach**: keep byte-size as the primary budget variable for
now; add token-count as a second tracked metric once retrieval feeds a real
generator prompt.
**Implementation implications**: `size_bytes()` exists; the budget
*constraint enforcement* (truncating/compressing when over budget) does not
exist yet — Phase 12.
**Research implications**: RQ2 (how much memory is necessary) cannot be
answered from a single 1-character, 4-clip run. This requires the Phase 15
memory-budget experiment matrix and is explicitly unanswered here.

### 10. Define research hypotheses

Restated as falsifiable statements (not yet tested):

- H1: for a fixed generator and fixed budget B >= some threshold, structured
  selective retrieval yields higher attribute-consistency than full-history
  prompting at equal or lower token cost. (Tests RQ3, RQ4.)
- H2: an LLM-based drift classifier, given narrative context, achieves
  higher precision/recall distinguishing intentional from unexplained
  change than a keyword-rule baseline (`StubReasoner`). (Tests RQ5.)
- H3: consistency degrades measurably over long horizons (25+ generations)
  without persistent memory, and this degradation is reduced (not
  necessarily eliminated) by CastGraph's approach. (Tests RQ9.)

All three are **UNVALIDATED CLAIMS** at this point in the project — no
experiment has been run. Phase 15 is where these get tested, if they get
tested at all.

### 11. Define measurable success criteria

**Problem**: "success" needs numbers, not vibes.
**Approach**: per-dimension consistency rate (subtasks 4-7) on a held-out
set of generations; drift-classification precision/recall against a labeled
set (Phase 15's drift benchmark); memory size at a given consistency level;
latency/cost overhead vs. no-memory baseline.
**Alternatives**: a single blended "CastGraph score" — rejected, same
reasoning as subtask 1.
**Recommended approach**: report the metrics above separately; only compute
an aggregate if/when a real product decision needs one number (e.g. a
dashboard), and label it explicitly as a weighted aggregate, not "the"
consistency score.
**Implementation implications**: none yet — no evaluation harness exists
(Phase 15).
**Research implications**: none new.

### 12. Initial novelty/gap analysis

**This subtask required real research, not memorized claims — a live web
search was run rather than asserting novelty from training data.**

**What was found (KNOWN FROM LITERATURE, as of this search):**

- **Memento** (arXiv 2606.14667) — dual-query memory retrieval + memory-based
  subject reconstruction to preserve long-term identity evidence for
  cross-shot consistency in long-form generation.
- **VideoMemory** (arXiv 2601.03655) — an entity-centric framework with a
  "Dynamic Memory Bank" storing explicit visual/semantic descriptors for
  characters/props/backgrounds, with retrieval-update for cross-shot
  consistency.
- **EntityBench** (arXiv 2605.15199) — a multi-agent system with persistent
  per-entity memory banks (visual + textual) injected as context for
  cross-shot generation, plus a benchmark for entity-consistent multi-shot
  video generation.
- **Coverage-Maximizing Retrieval** (arXiv 2606.02479) — retrieval strategy
  specifically to maximize what's covered for consistent long video
  generation.
- Several KV-cache/latent-history compression systems (Echo-Forcing, Surprise
  Forcing, Future Forcing, FramePack-style packing, Echo-Infinity) address
  bounded-memory long video generation, but operate as **in-model,
  in-session** mechanisms (compressed frame/latent/KV-cache history), not as
  an external structured store surviving across independent generation
  calls/sessions/tools.
- No system found in this search performs **explicit intentional-vs-
  unexplained change classification with a stated taxonomy** (disguise vs.
  drift, injury vs. drift) as a first-class reasoning step with provenance;
  the found systems retrieve/reconstruct entity state for consistency but
  don't appear to reason about *why* a deviation exists before deciding
  whether to trust it.

**Gap identified**: the found systems cluster into two groups — (a)
in-model/in-session memory mechanisms bounded by compute (KV-cache/latent
compression), and (b) entity memory banks (visual+text descriptors)
retrieved within one long-form generation pipeline for cross-shot
consistency. CastGraph's distinguishing bet, **not yet validated**, is
being (1) external to and independent of any single generator/session/model
version (Principle 8), (2) structured around canonical-state-with-
exceptions rather than a similarity-retrieval memory bank (Principle 5, so a
disguise doesn't silently overwrite the character's true voice), and (3)
built around an explicit deviation-classification step with provenance
(Phase 11/13) rather than implicit consistency-by-retrieval.

**This is a positioning claim, not a validated contribution.** It has not
been benchmarked against Memento/VideoMemory/EntityBench, and it is entirely
possible those systems already handle canonical-vs-exception reasoning
internally in ways this search didn't surface — a deeper literature reading
pass (full papers, not abstracts) is a prerequisite before any publication
claim, and is explicitly deferred (see ROADMAP.md).

Sources: [Memento](https://arxiv.org/html/2606.14667v1), [VideoMemory](https://arxiv.org/abs/2601.03655), [EntityBench](https://arxiv.org/pdf/2605.15199), [Coverage-Maximizing Retrieval](https://arxiv.org/pdf/2606.02479), [Echo-Forcing](https://arxiv.org/pdf/2605.16003), [Surprise Forcing](https://arxiv.org/html/2607.18436), [Future Forcing](https://arxiv.org/html/2605.30083v1), [Echo-Infinity](https://arxiv.org/pdf/2606.04527).

## Architecture (as of Phase 1)

No implementation architecture changes in this phase — Phase 1 is
formalization only, per the brief ("Do NOT write implementation code yet").
The existing MVP code (built before this phase was done formally) already
happens to match most of the definitions above; where it doesn't (relationship
drift detection, entity_type, continuous-attribute matching), that's called
out as a gap above rather than silently left implicit.

## Data Flow

Unchanged from `docs/ARCHITECTURE.md` — this phase doesn't add a new
component, it defines the vocabulary the rest of the phases must use
consistently.

## Interfaces

None new.

## Risks

- **Definitional risk**: the identity/attribute/relationship/world split may
  not survive contact with a second, more complex scenario (e.g. group
  scenes, multiple simultaneous relationships) — flagged, not yet tested.
- **Novelty risk**: the gap claim above is based on abstracts from one
  search pass, not full papers — it could collapse on closer reading.
- **Threshold risk**: continuous-attribute matching (subtask 3) has no real
  values yet; picking them later will be somewhat arbitrary without
  perceptual-model calibration data.

## Validation

None run. Phase 1 produces definitions and hypotheses, not results. The
"validation" for this phase is: do the definitions let every later phase
proceed without redefining terms? (Checked informally by writing Phases 2+
against these definitions — see later phase docs.)

## Deliverables

- This document.
- Restated, falsifiable research hypotheses (subtask 10).
- An honest novelty/gap analysis grounded in a real (if narrow) literature
  search (subtask 12), with explicit caveats about its limits.

## Architecture Changes From Previous Phase

N/A — first phase.

## Quality Gate

- **Research quality**: problem is defined per-dimension, not as one vague
  "consistency" property. Hypotheses are falsifiable. Contribution is
  explicitly *not* claimed as validated — passes.
- **Technical quality**: definitions map cleanly onto structures already in
  `castgraph/memory/model.py`; gaps (relationships, entity_type) are named,
  not hidden — passes.
- **Novelty quality**: grounded in a real search, gap stated narrowly and
  with caveats rather than "nobody has done this" — passes, with the caveat
  that it's a shallow pass (abstracts only).
- **Failure mode check**: does this collapse into "just a knowledge graph"
  etc.? No — Phase 1 explicitly keeps canonical/exception/provenance
  semantics distinct from a bare retrieval-memory-bank framing, which is the
  precise thing the gap analysis says existing systems don't obviously do.
