from castgraph.memory import ClipRef, MemoryStore
from castgraph.drift import reconcile
from castgraph.reasoning import StubReasoner
from castgraph.temporal import canonical_state_at

REASONER = StubReasoner()


def test_a_purely_consistent_clip_is_still_registered_in_clip_sequence():
    """Regression test for a real bug found via a live production test
    (2026-09-08): a clip whose only outcome was CONSISTENT never got
    registered in clip_sequence, because that branch mutated canonical
    state directly instead of going through a MemoryStore method that
    registers the clip as a side effect. See castgraph/drift/reconcile.py."""
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))

    reconcile(store, "marcus", {"voice": "deep/rough"}, ClipRef("ep2", "..."),
              narrative_context="Marcus talks to Sarah.", reasoner=REASONER)

    assert "ep2" in store.clip_sequence
    # and the temporal query must be able to resolve it, not raise
    assert canonical_state_at(store, "marcus", "voice", "ep2") == "deep/rough"


def test_reconstructs_value_before_and_after_promotion():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))

    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep4", "..."),
              narrative_context="no explanation", reasoner=REASONER)
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep5", "..."),
              narrative_context="no explanation", reasoner=REASONER)

    # promoted at ep5 -- before it, canonical was still deep/rough
    assert canonical_state_at(store, "marcus", "voice", "ep1") == "deep/rough"
    assert canonical_state_at(store, "marcus", "voice", "ep4") == "deep/rough"
    # at and after the promotion, canonical is the new value
    assert canonical_state_at(store, "marcus", "voice", "ep5") == "soft/high"
