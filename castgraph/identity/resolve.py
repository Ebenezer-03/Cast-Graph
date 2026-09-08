"""Phase 4, reduced to name-based matching. Documented limitation: with no
real video, there are no face/voice embeddings to fuse — see ROADMAP.md.
Kept as its own module (not inlined elsewhere) so a real multimodal
implementation can replace this function without touching call sites.
"""
from __future__ import annotations

from castgraph.memory import MemoryStore


def resolve_identity(store: MemoryStore, name: str) -> str:
    """Returns an entity_id for `name`, creating one if unseen. MVP-only:
    exact case-insensitive name match, no fuzzy/alias/embedding matching."""
    entity_id = name.strip().lower().replace(" ", "_")
    store.get_or_create(entity_id, name)
    return entity_id
