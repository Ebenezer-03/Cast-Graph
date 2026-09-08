"""One per-clip pipeline step, shared by every caller (run_mvp.py,
eval/run_benchmark.py, api/generate.py). Extracted per the architecture
review's candidate 3 ("one per-clip pipeline step, two callers") -- adding
the production API as a third caller is exactly the second/third adapter
that justifies the seam.
"""
from __future__ import annotations

from dataclasses import dataclass

from castgraph.adapters import build_context_data, render_text
from castgraph.drift import reconcile
from castgraph.identity import IdentityMatch, resolve_identity
from castgraph.memory import MemoryStore
from castgraph.observation import observe
from castgraph.prompt import extract_location
from castgraph.reasoning import Reasoner
from castgraph.retrieval import retrieve


@dataclass
class ClipResult:
    identity: IdentityMatch
    entity_id: str
    location: str | None
    context: str
    observed: dict
    report: list[dict]


def run_clip(
    store: MemoryStore,
    character_name: str,
    clip_id: str,
    clip_text: str,
    prompt: str,
    reasoner: Reasoner,
) -> ClipResult:
    """Runs one clip through the full generate(stubbed)->observe->remember->
    retrieve loop against `store`, mutating it in place. Callers add their
    own instrumentation (printing, grading, HTTP response shaping)."""
    identity = resolve_identity(store, character_name)
    entity_id = identity.entity_id

    understanding = reasoner.understand_prompt(prompt, [character_name])
    location = extract_location(prompt)
    name_to_id = {character_name: entity_id}
    relevant_ids = [name_to_id[n] for n in understanding["entities"] if n in name_to_id] or [entity_id]

    retrieved = retrieve(store, relevant_ids)
    context_data = build_context_data(retrieved, understanding["narrative_context"], location=location)
    context = render_text(context_data)

    observed, clip_ref = observe(clip_id, clip_text, character_name, reasoner)
    report = reconcile(store, entity_id, observed, clip_ref, narrative_context=prompt, reasoner=reasoner)

    return ClipResult(
        identity=identity, entity_id=entity_id, location=location,
        context=context, observed=observed, report=report,
    )
