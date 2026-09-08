from castgraph.memory import ClipRef, MemoryStore
from castgraph.drift import reconcile
from castgraph.reasoning import StubReasoner
from castgraph.temporal import canonical_state_at

REASONER = StubReasoner()


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
