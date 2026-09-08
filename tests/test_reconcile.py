"""Locks in the core claim of Phase 5/11: canonical state is never
overwritten by a single new observation, and a disguise is classified
differently than an unexplained change."""
from castgraph.memory import ClipRef, MemoryStore
from castgraph.drift import reconcile
from castgraph.reasoning import StubReasoner

REASONER = StubReasoner()


def _store_with_marcus():
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "..."))
    return store


def test_matching_observation_is_consistent():
    store = _store_with_marcus()
    report = reconcile(
        store, "marcus", {"voice": "deep/rough"}, ClipRef("ep2", "..."),
        narrative_context="Marcus talks to Sarah.", reasoner=REASONER,
    )
    assert report[0]["status"] == "CONSISTENT"
    assert store.entities["marcus"].canonical["voice"].value == "deep/rough"


def test_disguise_is_temporary_override_not_drift():
    store = _store_with_marcus()
    report = reconcile(
        store, "marcus", {"voice": "soft/high"}, ClipRef("ep3", "..."),
        narrative_context="Marcus is disguising his voice to avoid being recognized.",
        reasoner=REASONER,
    )
    assert report[0]["status"] == "TEMPORARY_OVERRIDE"
    # canonical state must NOT change
    assert store.entities["marcus"].canonical["voice"].value == "deep/rough"
    assert len(store.entities["marcus"].exceptions) == 1
    assert len(store.entities["marcus"].unexplained) == 0


def test_unexplained_change_is_flagged_not_applied():
    store = _store_with_marcus()
    report = reconcile(
        store, "marcus", {"voice": "soft/high"}, ClipRef("ep4", "..."),
        narrative_context="Marcus talks to Sarah at the docks again.",
        reasoner=REASONER,
    )
    assert report[0]["status"] == "UNEXPLAINED_DRIFT"
    # canonical state must NOT change even though nothing explained it
    assert store.entities["marcus"].canonical["voice"].value == "deep/rough"
    assert len(store.entities["marcus"].unexplained) == 1
    assert len(store.entities["marcus"].exceptions) == 0


def test_conflicting_cues_are_classified_ambiguous():
    store = _store_with_marcus()
    report = reconcile(
        store, "marcus", {"voice": "soft/high"}, ClipRef("ep6", "..."),
        narrative_context="Marcus, recovering from an injury, is also disguising his voice.",
        reasoner=REASONER,
    )
    assert report[0]["status"] == "AMBIGUOUS"
    assert store.entities["marcus"].canonical["voice"].value == "deep/rough"
    assert len(store.entities["marcus"].unexplained) == 1


def test_repeated_unexplained_value_gets_promoted():
    store = _store_with_marcus()
    # First unexplained observation: recorded, not promoted (below threshold).
    report1 = reconcile(
        store, "marcus", {"voice": "soft/high"}, ClipRef("ep4", "..."),
        narrative_context="Marcus talks to Sarah at the docks again.",
        reasoner=REASONER,
    )
    assert report1[0]["status"] == "UNEXPLAINED_DRIFT"
    assert store.entities["marcus"].canonical["voice"].value == "deep/rough"

    # Second consecutive matching unexplained observation: promoted.
    report2 = reconcile(
        store, "marcus", {"voice": "soft/high"}, ClipRef("ep5", "..."),
        narrative_context="Marcus talks to Sarah at the docks again.",
        reasoner=REASONER,
    )
    assert report2[0]["status"] == "PROMOTED"
    assert store.entities["marcus"].canonical["voice"].value == "soft/high"
    # the old value is archived, not lost
    archived = [d for d in store.entities["marcus"].exceptions
                if d.classification == "PROMOTED_FROM_PREVIOUS"]
    assert len(archived) == 1
    assert archived[0].canonical_value == "deep/rough"


def test_dynamic_attribute_skips_reconciliation():
    store = _store_with_marcus()
    store.entities["marcus"].dynamic_attributes.add("outfit")
    report = reconcile(
        store, "marcus", {"outfit": "red jacket"}, ClipRef("ep2", "..."),
        narrative_context="Marcus talks to Sarah.", reasoner=REASONER,
    )
    assert report[0]["status"] == "DYNAMIC"
    assert "outfit" not in store.entities["marcus"].canonical


def test_new_attribute_is_established_as_baseline():
    store = _store_with_marcus()
    report = reconcile(
        store, "marcus", {"hair": "black"}, ClipRef("ep1", "..."),
        narrative_context="Marcus talks to Sarah.", reasoner=REASONER,
    )
    assert report[0]["status"] == "ESTABLISHED"
    assert store.entities["marcus"].canonical["hair"].value == "black"
