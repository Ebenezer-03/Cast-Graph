"""The persistent memory fabric: canonical state, evidence, and recorded
deviations. This is the logical model from Phase 2 of the design brief,
reduced to what the MVP scenario actually needs.

Deliberately not a graph database, not a vector store: plain dataclasses
serialized to JSON. See decisions/0001-storage-agnostic-json.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class ClipRef:
    """Provenance pointer to where a piece of evidence came from. In a real
    system this would point at a video timestamp; here a clip is just a
    synthetic text description, so the "span" is the clip id itself."""
    clip_id: str
    excerpt: str


@dataclass
class CanonicalAttribute:
    """A persistent, established fact about an entity (Principle 5: this is
    never overwritten by a single new observation)."""
    value: Any
    evidence: list[ClipRef] = field(default_factory=list)
    established_at: str = ""  # clip_id where this was first established


@dataclass
class Deviation:
    """A recorded departure from canonical state, with its classification.
    Explained deviations (exceptions) do NOT change canonical state; neither
    do unexplained ones — they're surfaced instead. Phase 11/5."""
    attribute: str
    observed_value: Any
    canonical_value: Any
    clip_ref: ClipRef
    classification: str  # CONSISTENT | EXPECTED_CHANGE | EXPLAINED_TRANSITION
                          # | TEMPORARY_OVERRIDE | UNEXPLAINED_DRIFT | AMBIGUOUS
    reasoning: str = ""


@dataclass
class Entity:
    id: str
    name: str
    canonical: dict[str, CanonicalAttribute] = field(default_factory=dict)
    exceptions: list[Deviation] = field(default_factory=list)
    unexplained: list[Deviation] = field(default_factory=list)
    relationships: dict[str, str] = field(default_factory=dict)


class MemoryStore:
    """Holds all entities for one project/world. Bounded by construction:
    only compact structured state lives here, never raw clip text (Principle 1)
    beyond the short excerpt kept for provenance."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}

    def get_or_create(self, entity_id: str, name: str) -> Entity:
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(id=entity_id, name=name)
        return self.entities[entity_id]

    def establish(self, entity_id: str, attribute: str, value: Any, clip_ref: ClipRef) -> None:
        """First-time recording of a canonical attribute. Only used when no
        canonical value exists yet for this attribute — see reconcile()."""
        entity = self.entities[entity_id]
        if attribute in entity.canonical:
            entity.canonical[attribute].evidence.append(clip_ref)
        else:
            entity.canonical[attribute] = CanonicalAttribute(
                value=value, evidence=[clip_ref], established_at=clip_ref.clip_id
            )

    def record_exception(self, entity_id: str, deviation: Deviation) -> None:
        self.entities[entity_id].exceptions.append(deviation)

    def record_unexplained(self, entity_id: str, deviation: Deviation) -> None:
        self.entities[entity_id].unexplained.append(deviation)

    def to_json(self) -> str:
        return json.dumps(
            {eid: asdict(e) for eid, e in self.entities.items()}, indent=2
        )

    def size_bytes(self) -> int:
        return len(self.to_json().encode("utf-8"))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")
