"""Phase 6, reduced to one real query: what was an attribute's canonical
value at a given point in clip processing order. Reconstructs the answer
from Phase 5's promotion chain rather than storing a separate history log,
to keep memory bounded (Principle 4). See docs/phases/PHASE_06.md for what
this does and does not cover (no flashbacks/time jumps/intervals yet).
"""
from __future__ import annotations

from typing import Any

from castgraph.memory import MemoryStore


def canonical_state_at(store: MemoryStore, entity_id: str, attribute: str, at_clip_id: str) -> Any | None:
    """Returns the canonical value of `attribute` as of `at_clip_id` (in
    clip processing order), or None if the attribute didn't exist yet at
    that point. Only reconstructs canonical truth, not active temporary
    overrides — see PHASE_06.md known limitation."""
    if at_clip_id not in store.clip_sequence:
        raise ValueError(f"unknown clip_id: {at_clip_id!r}")
    cutoff = store.clip_sequence.index(at_clip_id)

    entity = store.entities[entity_id]
    promotions = sorted(
        (d for d in entity.exceptions
         if d.attribute == attribute and d.classification == "PROMOTED_FROM_PREVIOUS"),
        key=lambda d: store.clip_sequence.index(d.clip_ref.clip_id),
    )

    if attribute not in entity.canonical and not promotions:
        return None

    # Build the (sequence_index, value) breakpoints: the value in effect
    # from that index onward, oldest first.
    breakpoints: list[tuple[int, Any]] = []
    if promotions:
        first = promotions[0]
        first_idx = store.clip_sequence.index(first.clip_ref.clip_id)
        # the value that was canonical *before* the first promotion had no
        # recorded start point of its own (see PHASE_06.md subtask 12) --
        # treated as in effect from the beginning of the sequence.
        breakpoints.append((0, first.canonical_value))
        for p in promotions:
            breakpoints.append((store.clip_sequence.index(p.clip_ref.clip_id), p.observed_value))
    elif attribute in entity.canonical:
        established_idx = store.clip_sequence.index(entity.canonical[attribute].established_at)
        breakpoints.append((established_idx, entity.canonical[attribute].value))

    value = None
    for idx, val in breakpoints:
        if idx <= cutoff:
            value = val
        else:
            break
    return value
