"""Phases 10 + 11 + 5 combined: for each observed attribute, compare against
canonical state, classify any deviation, and reconcile — never overwriting
canonical state on a single new observation (Principle 5).
"""
from __future__ import annotations

from castgraph.memory import ClipRef, Deviation, MemoryStore
from castgraph.reasoning import Reasoner


def reconcile(
    store: MemoryStore,
    entity_id: str,
    observed: dict,
    clip_ref: ClipRef,
    narrative_context: str,
    reasoner: Reasoner,
) -> list[dict]:
    """Returns a per-attribute verification report: one entry per observed
    attribute with its status, so weaknesses aren't hidden behind one
    aggregate score (Phase 10)."""
    entity = store.entities[entity_id]
    report: list[dict] = []

    for attribute, observed_value in observed.items():
        if attribute in entity.dynamic_attributes:
            report.append({
                "attribute": attribute,
                "status": "DYNAMIC",
                "detail": "declared dynamic; not subject to consistency checking",
            })
            continue

        if attribute not in entity.canonical:
            store.establish(entity_id, attribute, observed_value, clip_ref)
            report.append({
                "attribute": attribute,
                "status": "ESTABLISHED",
                "detail": f"no prior canonical value; recorded {observed_value!r} as baseline",
            })
            continue

        canonical_value = entity.canonical[attribute].value
        if canonical_value == observed_value:
            entity.canonical[attribute].evidence.append(clip_ref)
            entity.canonical[attribute].reinforce()
            report.append({
                "attribute": attribute,
                "status": "CONSISTENT",
                "detail": f"matches canonical {canonical_value!r}",
            })
            continue

        result = reasoner.classify_drift(attribute, canonical_value, observed_value, narrative_context)
        classification = result["classification"]
        reasoning = result.get("reasoning", "")
        deviation = Deviation(
            attribute=attribute,
            observed_value=observed_value,
            canonical_value=canonical_value,
            clip_ref=clip_ref,
            classification=classification,
            reasoning=reasoning,
        )

        if classification in ("EXPECTED_CHANGE", "EXPLAINED_TRANSITION", "TEMPORARY_OVERRIDE"):
            store.record_exception(entity_id, deviation)
        else:  # UNEXPLAINED_DRIFT, AMBIGUOUS, or an unrecognized label -> don't touch canonical
            store.record_unexplained(entity_id, deviation)

        report.append({
            "attribute": attribute,
            "status": classification,
            "detail": reasoning,
        })

    return report
