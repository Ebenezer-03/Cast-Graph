"""Phase 10: per-attribute consistency rates across a run, plus a clearly
-labeled naive aggregate. See docs/phases/PHASE_10.md -- the aggregate is
an unweighted mean, not a validated or calibrated score, and must not be
presented as one.
"""
from __future__ import annotations

CONSISTENT_STATUSES = {"CONSISTENT", "EXPECTED_CHANGE", "EXPLAINED_TRANSITION",
                        "TEMPORARY_OVERRIDE", "PROMOTED"}
NOT_CHECKED_STATUSES = {"ESTABLISHED", "DYNAMIC"}


def consistency_report(history: list[list[dict]]) -> dict:
    """`history` is the list of per-clip reports returned by
    castgraph.drift.reconcile() over a run. Returns
    {"per_attribute": {attr: {"rate": float, "checked": int}}, "aggregate":
    float | None, "aggregate_caveat": str}."""
    totals: dict[str, list[int]] = {}  # attr -> [consistent_count, checked_count]

    for clip_report in history:
        for item in clip_report:
            attribute = item["attribute"]
            status = item["status"]
            if status in NOT_CHECKED_STATUSES:
                continue
            consistent, checked = totals.setdefault(attribute, [0, 0])
            checked += 1
            if status in CONSISTENT_STATUSES:
                consistent += 1
            totals[attribute] = [consistent, checked]

    per_attribute = {
        attr: {"rate": consistent / checked, "checked": checked}
        for attr, (consistent, checked) in totals.items()
        if checked > 0
    }

    if per_attribute:
        aggregate = sum(v["rate"] for v in per_attribute.values()) / len(per_attribute)
    else:
        aggregate = None

    return {
        "per_attribute": per_attribute,
        "aggregate": aggregate,
        "aggregate_caveat": (
            "unweighted mean across attributes that happened to be observed "
            "in this run -- not a validated or calibrated score (see "
            "docs/phases/PHASE_10.md)"
        ),
    }
