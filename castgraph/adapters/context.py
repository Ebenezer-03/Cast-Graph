"""Phase 9: a generator-independent structured context (`build_context_data`),
rendered by per-generator adapters. No real generator exists to adapt to
yet, so the two renderers here (`render_text`, `render_json`) are a modest,
honestly-scoped proxy for generator independence -- see
docs/phases/PHASE_09.md.
"""
from __future__ import annotations

import json


def build_context_data(retrieved: dict, narrative_context: str,
                        location: str | None = None,
                        constraints: list[str] | None = None) -> dict:
    """The generator-independent structured form. Relationship/temporal/
    world slots exist for forward-compatibility but are empty until those
    subsystems are populated (Phase 2/6 gaps)."""
    return {
        "scene_intent": narrative_context,
        "location": location,
        "entities": retrieved,
        "relationships": {},  # placeholder -- Phase 2/5 gap
        "world_rules": [],    # placeholder -- Phase 2 gap, unpopulated
        "constraints": constraints or [],
    }


def render_text(context_data: dict) -> str:
    """Plain-text rendering -- what run_mvp.py hands to the (stubbed)
    generator today."""
    lines = ["# Generation context", "", f"Scene intent: {context_data['scene_intent']}"]
    if context_data.get("location"):
        lines.append(f"Location: {context_data['location']}")
    lines.append("")
    for data in context_data["entities"].values():
        lines.append(f"## {data['name']}")
        for attr, value in data["canonical"].items():
            lines.append(f"- {attr}: {value}")
        lines.append("")
    if context_data["constraints"]:
        lines.append("Constraints:")
        for c in context_data["constraints"]:
            lines.append(f"- {c}")
    return "\n".join(lines)


def render_json(context_data: dict) -> str:
    """Structured JSON rendering -- stands in for a hypothetical generator
    that takes structured conditioning input rather than a text prompt.
    Not validated against any real generator's actual schema."""
    return json.dumps(context_data, indent=2)


# Backward-compatible convenience wrapper (existing call sites/tests).
def build_context(retrieved: dict, narrative_context: str) -> str:
    return render_text(build_context_data(retrieved, narrative_context))
