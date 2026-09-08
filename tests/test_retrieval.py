from castgraph.memory import ClipRef, MemoryStore
from castgraph.retrieval import retrieve, compare_retrieval_strategies


def _store_with_marcus():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))
    return store


def test_retrieve_includes_confidence():
    store = _store_with_marcus()
    result = retrieve(store, ["marcus"])
    assert "confidence" in result["marcus"]
    assert result["marcus"]["confidence"]["voice"] == 0.5


def test_selective_retrieval_never_exceeds_full_history():
    store = _store_with_marcus()
    sizes = compare_retrieval_strategies(store, ["marcus"])
    assert sizes["selective_bytes"] <= sizes["full_history_bytes"]
    assert 0.0 <= sizes["selective_to_full_ratio"] <= 1.0
