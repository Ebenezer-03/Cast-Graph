"""Phase 13: a plain-language explanation of why a canonical attribute has
the value it has -- the shape described in the brief's Section 16 UX
mockup, built as a function since there's no UI in this project. See
docs/phases/PHASE_13.md for the known blind spot (compressed evidence can't
be shown, only counted).
"""
from __future__ import annotations

from castgraph.memory import MemoryStore


def explain(store: MemoryStore, entity_id: str, attribute: str) -> str:
    entity = store.entities[entity_id]
    lines = [f"{entity.name}.{attribute}"]

    current = entity.canonical.get(attribute)
    if current is None:
        lines.append("  no canonical value established yet")
    else:
        lines.append(f"  canonical value: {current.value!r} (confidence={current.confidence:.2f})")
        lines.append(f"  established at clip: {current.established_at}")
        lines.append(f"  evidence: {len(current.evidence)} clip(s)"
                      + (f", {current.evidence_dropped} older entries compressed away"
                         if current.evidence_dropped else ""))
        for ref in current.evidence:
            lines.append(f"    - {ref.clip_id}: {ref.excerpt}")

    promotions = [d for d in entity.exceptions
                  if d.attribute == attribute and d.classification == "PROMOTED_FROM_PREVIOUS"]
    if promotions:
        lines.append("  promotion history:")
        for p in promotions:
            lines.append(f"    - at clip {p.clip_ref.clip_id}: "
                         f"{p.canonical_value!r} -> {p.observed_value!r} ({p.reasoning})")

    open_unexplained = [d for d in entity.unexplained if d.attribute == attribute]
    if open_unexplained:
        lines.append("  open, unexplained deviations requiring review:")
        for d in open_unexplained:
            lines.append(f"    - clip {d.clip_ref.clip_id}: observed {d.observed_value!r} "
                         f"vs canonical {d.canonical_value!r} -- {d.reasoning}")

    return "\n".join(lines)
