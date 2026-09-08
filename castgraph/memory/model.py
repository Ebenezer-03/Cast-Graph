"""The persistent memory fabric: canonical state, evidence, and recorded
deviations. This is the logical model from Phase 2 of the design brief.

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
    # Saturating evidence counter, NOT a calibrated probability — see
    # docs/phases/PHASE_02.md subtask 11. Do not present this to a user as
    # a real confidence percentage until it's backed by real observation
    # noise data.
    confidence: float = 0.5
    # Count of evidence entries removed by compression (Phase 12) -- kept
    # visible rather than silently lost, per Principle 1/13.
    evidence_dropped: int = 0

    def reinforce(self, step: float = 0.1) -> None:
        self.confidence = min(1.0, self.confidence + step)


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
    # Clip id after which this override should no longer be treated as
    # active (e.g. the disguise ends). None = unbounded (current MVP
    # behavior). Auto-expiry logic is NOT implemented yet — needs Phase 6
    # temporal reasoning; this field just makes expiry expressible.
    active_until: str | None = None
    # Populated only by reasoners that actually provide one (not
    # StubReasoner) -- see docs/phases/PHASE_11.md.
    confidence: float | None = None


@dataclass
class Relationship:
    """Joint state between two entities — not an attribute of either one
    alone (see docs/phases/PHASE_02.md subtask 5 for why this replaced a
    plain dict). Stored on the subject entity; mirrored onto the target too
    when symmetric."""
    target_id: str
    kind: str  # e.g. "ally", "parent_of", "reports_to"
    value: str = ""
    evidence: list[ClipRef] = field(default_factory=list)
    directional: bool = False


@dataclass
class Event:
    """A recorded happening that justifies state changes — the causal link
    Phase 11 (drift attribution) and Phase 13 (provenance) point back to.
    Defined in this phase; not yet populated by run_mvp.py (see
    docs/phases/PHASE_02.md Architecture Changes) — a real, named gap."""
    clip_ref: ClipRef
    entity_ids: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class WorldRule:
    """A world-level constraint, not tied to any single entity."""
    rule: str
    evidence: list[ClipRef] = field(default_factory=list)


@dataclass
class Entity:
    id: str
    name: str
    entity_type: str = "character"  # "character" | "location" | "object"
    # Manually-curated alternate names ("he", "the doctor", nicknames) that
    # should resolve to this entity. Intentionally not auto-inferred — see
    # docs/phases/PHASE_04.md risk note on overly broad aliases.
    aliases: set[str] = field(default_factory=set)
    canonical: dict[str, CanonicalAttribute] = field(default_factory=dict)
    exceptions: list[Deviation] = field(default_factory=list)
    unexplained: list[Deviation] = field(default_factory=list)
    relationships: dict[str, Relationship] = field(default_factory=dict)
    # Attributes explicitly declared as never subject to consistency
    # checking (e.g. "current_outfit" if it's meant to change every scene).
    # Empty by default -> behavior identical to before this phase.
    dynamic_attributes: set[str] = field(default_factory=set)
    # Working state for promotion (Phase 5, subtask 11): attribute ->
    # (candidate_value, consecutive_count). Deliberately excluded from
    # to_json() output -- it's bookkeeping, not truth (Principle 1/4).
    pending_promotion: dict[str, tuple[Any, int]] = field(default_factory=dict, compare=False)


class MemoryStore:
    """Holds all entities for one project/world. Bounded by construction:
    only compact structured state lives here, never raw clip text (Principle 1)
    beyond the short excerpt kept for provenance."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.world_rules: list[WorldRule] = []
        self.events: list[Event] = []
        # Chronological (by processing order) list of clip ids seen so far.
        # Phase 6: gives every clip a stable sequence index for temporal
        # reconstruction, without requiring callers to track it themselves.
        self.clip_sequence: list[str] = []

    def _note_clip(self, clip_id: str) -> None:
        if clip_id not in self.clip_sequence:
            self.clip_sequence.append(clip_id)

    def get_or_create(self, entity_id: str, name: str, entity_type: str = "character") -> Entity:
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(id=entity_id, name=name, entity_type=entity_type)
        return self.entities[entity_id]

    def establish(self, entity_id: str, attribute: str, value: Any, clip_ref: ClipRef) -> None:
        """First-time recording of a canonical attribute, or reinforcement of
        an existing one with matching evidence. Only called for attributes
        not in `dynamic_attributes` — see reconcile()."""
        self._note_clip(clip_ref.clip_id)
        entity = self.entities[entity_id]
        if attribute in entity.canonical:
            entity.canonical[attribute].evidence.append(clip_ref)
            entity.canonical[attribute].reinforce()
        else:
            entity.canonical[attribute] = CanonicalAttribute(
                value=value, evidence=[clip_ref], established_at=clip_ref.clip_id
            )

    def promote(self, entity_id: str, attribute: str, new_value: Any, clip_ref: ClipRef, reasoning: str) -> None:
        """Archives the current canonical value as an exception classified
        PROMOTED_FROM_PREVIOUS, then makes new_value canonical. See
        docs/phases/PHASE_05.md subtask 11 -- promotion threshold/policy
        lives in castgraph/drift/reconcile.py, not here."""
        self._note_clip(clip_ref.clip_id)
        entity = self.entities[entity_id]
        old = entity.canonical.get(attribute)
        if old is not None:
            entity.exceptions.append(Deviation(
                attribute=attribute,
                observed_value=new_value,
                canonical_value=old.value,
                clip_ref=clip_ref,
                classification="PROMOTED_FROM_PREVIOUS",
                reasoning=reasoning,
            ))
        entity.canonical[attribute] = CanonicalAttribute(
            value=new_value, evidence=[clip_ref], established_at=clip_ref.clip_id
        )

    def record_exception(self, entity_id: str, deviation: Deviation) -> None:
        self._note_clip(deviation.clip_ref.clip_id)
        self.entities[entity_id].exceptions.append(deviation)

    def record_unexplained(self, entity_id: str, deviation: Deviation) -> None:
        self._note_clip(deviation.clip_ref.clip_id)
        self.entities[entity_id].unexplained.append(deviation)

    def record_event(self, event: Event) -> None:
        self.events.append(event)

    def to_dict(self) -> dict:
        entities = {}
        for eid, e in self.entities.items():
            d = asdict(e)
            # pending_promotion is working bookkeeping, not persistent
            # truth -- excluded so memory stays compact (Principle 1/4).
            d.pop("pending_promotion", None)
            entities[eid] = d
        return {
            "entities": entities,
            "world_rules": [asdict(r) for r in self.world_rules],
            "events": [asdict(e) for e in self.events],
            # clip_sequence must round-trip -- Phase 6 temporal reconstruction
            # depends on it surviving a save/reload cycle (a real gap, fixed
            # here rather than only noticed once production storage needed it).
            "clip_sequence": list(self.clip_sequence),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            indent=2,
            default=list,  # allows set (dynamic_attributes) to serialize
        )

    def size_bytes(self) -> int:
        return len(self.to_json().encode("utf-8"))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryStore":
        """Reconstructs a MemoryStore from to_dict()'s output. Needed the
        moment memory is persisted anywhere other than an in-process object
        (e.g. Postgres, Phase 14) -- to_json() alone was write-only until
        this existed, a real gap surfaced by going to production storage."""
        store = cls()
        for eid, edata in data.get("entities", {}).items():
            entity = Entity(
                id=edata["id"],
                name=edata["name"],
                entity_type=edata.get("entity_type", "character"),
                aliases=set(edata.get("aliases", [])),
                canonical={
                    attr: CanonicalAttribute(
                        value=v["value"],
                        evidence=[ClipRef(**r) for r in v.get("evidence", [])],
                        established_at=v.get("established_at", ""),
                        confidence=v.get("confidence", 0.5),
                        evidence_dropped=v.get("evidence_dropped", 0),
                    )
                    for attr, v in edata.get("canonical", {}).items()
                },
                exceptions=[_deviation_from_dict(d) for d in edata.get("exceptions", [])],
                unexplained=[_deviation_from_dict(d) for d in edata.get("unexplained", [])],
                relationships={
                    k: Relationship(
                        target_id=v["target_id"], kind=v["kind"], value=v.get("value", ""),
                        evidence=[ClipRef(**r) for r in v.get("evidence", [])],
                        directional=v.get("directional", False),
                    )
                    for k, v in edata.get("relationships", {}).items()
                },
                dynamic_attributes=set(edata.get("dynamic_attributes", [])),
            )
            store.entities[eid] = entity

        store.world_rules = [
            WorldRule(rule=w["rule"], evidence=[ClipRef(**r) for r in w.get("evidence", [])])
            for w in data.get("world_rules", [])
        ]
        store.events = [
            Event(
                clip_ref=ClipRef(**e["clip_ref"]),
                entity_ids=e.get("entity_ids", []),
                summary=e.get("summary", ""),
            )
            for e in data.get("events", [])
        ]
        store.clip_sequence = list(data.get("clip_sequence", []))
        return store

    @classmethod
    def from_json(cls, text: str) -> "MemoryStore":
        return cls.from_dict(json.loads(text))

    @classmethod
    def load(cls, path: str | Path) -> "MemoryStore":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


def _deviation_from_dict(d: dict) -> Deviation:
    return Deviation(
        attribute=d["attribute"],
        observed_value=d["observed_value"],
        canonical_value=d["canonical_value"],
        clip_ref=ClipRef(**d["clip_ref"]),
        classification=d["classification"],
        reasoning=d.get("reasoning", ""),
        active_until=d.get("active_until"),
        confidence=d.get("confidence"),
    )
