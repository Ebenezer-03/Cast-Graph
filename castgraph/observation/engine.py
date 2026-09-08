"""Phase 3, reduced to text-only: turns a synthetic clip description into
structured observations. RAW MEDIA (the clip text) is never stored in
memory beyond a short excerpt for provenance — only the extracted
observations are (Principle 1).
"""
from __future__ import annotations

from castgraph.memory import ClipRef
from castgraph.reasoning import Reasoner


def observe(clip_id: str, clip_text: str, character_name: str, reasoner: Reasoner) -> tuple[dict, ClipRef]:
    """Returns (observed_attributes, clip_ref)."""
    attributes = reasoner.extract_observation(clip_text, character_name)
    excerpt = clip_text if len(clip_text) <= 120 else clip_text[:117] + "..."
    return attributes, ClipRef(clip_id=clip_id, excerpt=excerpt)
