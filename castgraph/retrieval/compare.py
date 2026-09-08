"""Phase 8 subtask 12: a small, real, honestly-scoped measurement comparing
full-history retrieval against selective entity-based retrieval, on
whatever memory currently exists in the store. See docs/phases/PHASE_08.md
for why this is not evidence for RQ3 at scale -- it's a proof the mechanism
behaves as expected on one tiny scenario.
"""
from __future__ import annotations

from castgraph.memory import MemoryStore
from castgraph.retrieval.select import retrieve


def compare_retrieval_strategies(store: MemoryStore, entity_ids: list[str]) -> dict:
    """Returns byte sizes for full-history vs. selective retrieval, plus the
    ratio. Scenario-specific -- see PHASE_08.md before generalizing."""
    full_size = len(store.to_json().encode("utf-8"))

    selective = retrieve(store, entity_ids)
    selective_size = len(str(selective).encode("utf-8"))

    ratio = selective_size / full_size if full_size else 0.0
    return {
        "full_history_bytes": full_size,
        "selective_bytes": selective_size,
        "selective_to_full_ratio": ratio,
    }
