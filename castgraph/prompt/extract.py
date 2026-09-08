"""Phase 7: lightweight, explicitly non-NLU extraction helpers pulled out of
a creator prompt. Keyword/regex based — an ENGINEERING ASSUMPTION, not a
claim of real language understanding. See docs/phases/PHASE_07.md.
"""
from __future__ import annotations

import re

# Shared with castgraph.reasoning.StubReasoner.classify_drift so the same
# cue list is used whether a cue is being *surfaced* (here, pre-generation)
# or *consulted* (there, during drift classification) -- avoids the
# duplication that existed before this phase.
DISGUISE_CUES = ("disguise", "disguising", "undercover", "in hiding")
INJURY_CUES = ("injured", "injury", "recovering", "hospital")

_LOCATION_PATTERN = re.compile(
    r"\b(?:at|outside|in|near)\s+the\s+([a-z][a-z \-]*)", re.IGNORECASE
)


def extract_location(prompt: str) -> str | None:
    """Naive pattern match for "at/outside/in/near the <place>". Will miss
    differently-phrased locations -- see PHASE_07.md subtask 4."""
    match = _LOCATION_PATTERN.search(prompt)
    if not match:
        return None
    return match.group(1).strip().rstrip(".,")


def extract_transformation_cues(text: str) -> list[str]:
    """Returns which known cue categories ("disguise", "injury") appear in
    text, case-insensitively. Not negation-aware -- see PHASE_07.md
    subtask 8 (a known, named weakness of the keyword approach)."""
    lowered = text.lower()
    cues = []
    if any(k in lowered for k in DISGUISE_CUES):
        cues.append("disguise")
    if any(k in lowered for k in INJURY_CUES):
        cues.append("injury")
    return cues
