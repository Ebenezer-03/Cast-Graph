"""Round-trip serialization: to_dict()/from_dict() must reconstruct an
equivalent store, not just produce write-only JSON. This is a real gap that
surfaced only once production storage (Postgres) needed to reload memory,
not something the MVP's local-file usage ever exercised."""
from castgraph.memory import ClipRef, MemoryStore
from castgraph.drift import reconcile
from castgraph.reasoning import StubReasoner

REASONER = StubReasoner()


def test_round_trip_preserves_canonical_state_and_clip_sequence():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "intro"))
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep3", "..."),
              narrative_context="Marcus is disguising his voice.", reasoner=REASONER)

    restored = MemoryStore.from_json(store.to_json())

    assert restored.entities["marcus"].canonical["voice"].value == "deep/rough"
    assert restored.entities["marcus"].canonical["voice"].confidence == \
        store.entities["marcus"].canonical["voice"].confidence
    assert len(restored.entities["marcus"].exceptions) == 1
    assert restored.entities["marcus"].exceptions[0].classification == "TEMPORARY_OVERRIDE"
    assert restored.clip_sequence == store.clip_sequence == ["ep1", "ep3"]


def test_round_trip_survives_promotion_history():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep4", "..."),
              narrative_context="no explanation", reasoner=REASONER)
    reconcile(store, "marcus", {"voice": "soft/high"}, ClipRef("ep5", "..."),
              narrative_context="no explanation", reasoner=REASONER)

    restored = MemoryStore.from_json(store.to_json())
    assert restored.entities["marcus"].canonical["voice"].value == "soft/high"
    promotions = [d for d in restored.entities["marcus"].exceptions
                  if d.classification == "PROMOTED_FROM_PREVIOUS"]
    assert len(promotions) == 1
    assert promotions[0].canonical_value == "deep/rough"
