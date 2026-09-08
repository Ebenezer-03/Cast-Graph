"""Phase 9, reduced to a single generator-agnostic text block. No real
generator exists to adapt to, so there's only one "adapter" today: a plain
text rendering of retrieved memory. A real system would have one adapter per
generator API; this function is the seam where those would plug in.
"""
from __future__ import annotations


def build_context(retrieved: dict, narrative_context: str) -> str:
    """Turns retrieved memory into the plain-text block that would be handed
    to a video generator's prompt/conditioning input."""
    lines = ["# Generation context", "", f"Scene intent: {narrative_context}", ""]
    for entity_id, data in retrieved.items():
        lines.append(f"## {data['name']}")
        for attr, value in data["canonical"].items():
            lines.append(f"- {attr}: {value}")
        lines.append("")
    return "\n".join(lines)
