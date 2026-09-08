"""Phase 8, reduced to entity-based retrieval only: pulls canonical state
for just the entities mentioned in the prompt, not the whole memory store.
No semantic/embedding retrieval yet (nothing in the MVP scenario needs it —
see ROADMAP.md).
"""
from __future__ import annotations

from castgraph.memory import MemoryStore


def retrieve(store: MemoryStore, entity_ids: list[str]) -> dict:
    """Returns {entity_id: {"name": ..., "canonical": {attr: value}}} for
    only the requested entities -- never the full store."""
    result = {}
    for entity_id in entity_ids:
        entity = store.entities.get(entity_id)
        if entity is None:
            continue
        result[entity_id] = {
            "name": entity.name,
            "canonical": {attr: ca.value for attr, ca in entity.canonical.items()},
            "confidence": {attr: ca.confidence for attr, ca in entity.canonical.items()},
        }
    return result
