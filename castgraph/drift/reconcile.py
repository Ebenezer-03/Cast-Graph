"""Phases 10 + 11 + 5 combined: for each observed attribute, compare against
canonical state, classify any deviation, and reconcile — never overwriting
canonical state on a single new observation (Principle 5). Also implements
Phase 5's promotion policy: a sustained, repeated "unexplained" value
eventually becomes the new canonical truth, rather than staying stuck in
`unexplained` forever — see docs/phases/PHASE_05.md subtask 11.
"""
from __future__ import annotations

from castgraph.memory import ClipRef, Deviation, MemoryStore
from castgraph.reasoning import Reasoner

# Number of consecutive matching UNEXPLAINED_DRIFT/AMBIGUOUS observations
# required before promoting a value to canonical. An ENGINEERING ASSUMPTION,
# not validated against real data -- see docs/phases/PHASE_05.md subtask 11.
PROMOTION_THRESHOLD = 2


def reconcile(
    store: MemoryStore,
    entity_id: str,
    observed: dict,
    clip_ref: ClipRef,
    narrative_context: str,
    reasoner: Reasoner,
    promotion_threshold: int = PROMOTION_THRESHOLD,
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
            entity.pending_promotion.pop(attribute, None)
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
            entity.pending_promotion.pop(attribute, None)
        else:  # UNEXPLAINED_DRIFT, AMBIGUOUS, or an unrecognized label
            store.record_unexplained(entity_id, deviation)

            candidate, count = entity.pending_promotion.get(attribute, (None, 0))
            if candidate == observed_value:
                count += 1
            else:
                count = 1
            entity.pending_promotion[attribute] = (observed_value, count)

            if count >= promotion_threshold:
                store.promote(
                    entity_id, attribute, observed_value, clip_ref,
                    reasoning=(
                        f"{attribute}={observed_value!r} observed {count} consecutive "
                        f"times without explanation; promoted to canonical "
                        f"(threshold={promotion_threshold})."
                    ),
                )
                entity.pending_promotion.pop(attribute, None)
                report.append({
                    "attribute": attribute,
                    "status": "PROMOTED",
                    "detail": f"{classification} repeated {count}x; new canonical value is {observed_value!r}",
                })
                continue

        report.append({
            "attribute": attribute,
            "status": classification,
            "detail": reasoning,
        })

    return report
