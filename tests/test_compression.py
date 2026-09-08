from castgraph.memory import ClipRef, MemoryStore
from castgraph.compression import compress_evidence, enforce_budget


def _store_with_lots_of_evidence(n=10):
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep0", "origin"))
    for i in range(1, n):
        store.establish("marcus", "voice", "deep/rough", ClipRef(f"ep{i}", f"clip {i}"))
    return store


def test_compress_evidence_keeps_first_and_recent():
    store = _store_with_lots_of_evidence(n=10)
    attr = store.entities["marcus"].canonical["voice"]
    assert len(attr.evidence) == 10

    dropped = compress_evidence(store, max_evidence=3)
    assert dropped == 7
    assert len(attr.evidence) == 3
    assert attr.evidence[0].clip_id == "ep0"  # first kept
    assert attr.evidence[-1].clip_id == "ep9"  # most recent kept
    assert attr.evidence_dropped == 7


def test_compression_never_changes_canonical_value_or_confidence():
    store = _store_with_lots_of_evidence(n=10)
    attr = store.entities["marcus"].canonical["voice"]
    value_before, confidence_before = attr.value, attr.confidence

    compress_evidence(store, max_evidence=2)

    assert attr.value == value_before
    assert attr.confidence == confidence_before


def test_enforce_budget_reduces_size_when_over():
    store = _store_with_lots_of_evidence(n=20)
    big_size = store.size_bytes()

    result = enforce_budget(store, budget_bytes=big_size // 2)
    assert result["final_bytes"] < big_size
    assert result["total_dropped"] > 0


def test_enforce_budget_reports_honest_failure_when_unmeetable():
    store = _store_with_lots_of_evidence(n=20)
    result = enforce_budget(store, budget_bytes=1)  # impossible budget
    assert result["met_budget"] is False
    assert result["max_evidence_used"] == 1
