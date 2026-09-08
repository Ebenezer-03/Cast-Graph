"""Phase 4, reduced to name/alias-based matching. Documented limitation:
with no real video, there are no face/voice embeddings to fuse — see
docs/phases/PHASE_04.md for the full multimodal design and what's blocked.
"""
from __future__ import annotations

from dataclasses import dataclass

from castgraph.memory import MemoryStore


@dataclass
class IdentityMatch:
    entity_id: str
    confidence: float
    method: str  # "exact_name" | "alias" | "new"


def resolve_identity(store: MemoryStore, name: str) -> IdentityMatch:
    """Resolves `name` to a known entity by exact name or registered alias,
    creating a new entity only when neither matches. MVP-only: no fuzzy
    matching, coreference, or multimodal fusion — see PHASE_04.md."""
    needle = name.strip().lower()

    for entity in store.entities.values():
        if entity.name.strip().lower() == needle:
            return IdentityMatch(entity.id, confidence=1.0, method="exact_name")
        if needle in {a.strip().lower() for a in entity.aliases}:
            return IdentityMatch(entity.id, confidence=0.8, method="alias")

    entity_id = needle.replace(" ", "_")
    store.get_or_create(entity_id, name)
    return IdentityMatch(entity_id, confidence=1.0, method="new")
