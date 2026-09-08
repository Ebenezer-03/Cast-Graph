"""Phase 12: bounded-memory enforcement via evidence-list capping. Only
touches provenance depth, never canonical truth -- see
docs/phases/PHASE_12.md for what this does and doesn't cover.
"""
from __future__ import annotations

from castgraph.memory import MemoryStore


def compress_evidence(store: MemoryStore, max_evidence: int) -> int:
    """Caps every canonical attribute's evidence list at `max_evidence`,
    keeping the first (establishment) entry and the most recent
    `max_evidence - 1`. Returns the total number of entries dropped across
    the whole store this call. Canonical value/confidence are untouched."""
    if max_evidence < 1:
        raise ValueError("max_evidence must be >= 1")

    total_dropped = 0
    for entity in store.entities.values():
        for attr in entity.canonical.values():
            if len(attr.evidence) <= max_evidence:
                continue
            first = attr.evidence[0]
            kept_recent = attr.evidence[-(max_evidence - 1):] if max_evidence > 1 else []
            dropped = len(attr.evidence) - 1 - len(kept_recent)
            attr.evidence = [first] + kept_recent
            attr.evidence_dropped += dropped
            total_dropped += dropped
    return total_dropped


def enforce_budget(store: MemoryStore, budget_bytes: int, floor: int = 1) -> dict:
    """Repeatedly halves the evidence cap until the store fits `budget_bytes`
    or `floor` is reached. Returns a report; honestly flags failure to meet
    the budget rather than pretending it succeeded."""
    starting_size = store.size_bytes()
    if starting_size <= budget_bytes:
        return {
            "met_budget": True,
            "starting_bytes": starting_size,
            "final_bytes": starting_size,
            "max_evidence_used": None,
            "total_dropped": 0,
        }

    max_evidence = 8
    total_dropped = 0
    while True:
        total_dropped += compress_evidence(store, max_evidence)
        size = store.size_bytes()
        if size <= budget_bytes or max_evidence <= floor:
            return {
                "met_budget": size <= budget_bytes,
                "starting_bytes": starting_size,
                "final_bytes": size,
                "max_evidence_used": max_evidence,
                "total_dropped": total_dropped,
            }
        max_evidence = max(floor, max_evidence // 2)
