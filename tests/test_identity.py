from castgraph.memory import MemoryStore
from castgraph.identity import resolve_identity


def test_exact_name_resolves_to_same_entity():
    store = MemoryStore()
    first = resolve_identity(store, "Marcus")
    second = resolve_identity(store, "marcus")  # case-insensitive
    assert first.entity_id == second.entity_id
    assert second.method == "exact_name"


def test_new_name_creates_new_entity():
    store = MemoryStore()
    match = resolve_identity(store, "Marcus")
    assert match.method == "new"
    assert match.entity_id in store.entities


def test_alias_resolves_to_existing_entity():
    store = MemoryStore()
    marcus = resolve_identity(store, "Marcus")
    store.entities[marcus.entity_id].aliases.add("the dockworker")

    match = resolve_identity(store, "the dockworker")
    assert match.entity_id == marcus.entity_id
    assert match.method == "alias"
