from castgraph.memory import ClipRef, MemoryStore
from castgraph.drift import reconcile
from castgraph.reasoning import StubReasoner
from castgraph.provenance import explain

REASONER = StubReasoner()


def test_explain_plain_attribute():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "intro clip"))

    text = explain(store, "marcus", "voice")
    assert "deep/rough" in text
    assert "ep1" in text


def test_explain_shows_promotion_history():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep4", "..."),
              narrative_context="no explanation", reasoner=REASONER)
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep5", "..."),
              narrative_context="no explanation", reasoner=REASONER)

    text = explain(store, "marcus", "voice")
    assert "deep/rough" in text
    assert "soft/high" in text
    assert "promotion history" in text
