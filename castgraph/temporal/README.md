# Temporal world-state engine

Phase 6 of the design brief, upgraded from a stub in `docs/phases/PHASE_06.md`:
`canonical_state_at(store, entity_id, attribute, at_clip_id)` answers "what
was this attribute's canonical value as of this clip", reconstructed from
Phase 5's promotion chain — no separate history log needed.

**Still not implemented** (no scenario exists to design these against yet —
see PHASE_06.md): temporal intervals, flashbacks, time jumps, relationship/
object/location evolution, active-window tracking for temporary overrides.
Clip processing order is assumed to equal story chronological order; that
assumption breaks the moment a flashback scenario is built.
