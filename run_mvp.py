"""Runs the full CastGraph MVP loop:

    generate -> observe -> remember -> retrieve -> generate -> verify -> consolidate

over the Marcus/Sarah synthetic scenario, printing memory state and the
verification report at each step.

"Generate" is stubbed (clips are pre-written synthetic text, see
scenario/marcus_sarah.py) since no real video generator is wired up.

Reasoner selection: uses GeminiReasoner (real LLM, decision 0003) when
GEMINI_API_KEY is set, otherwise falls back to StubReasoner (decision
0002). Set GEMINI_API_KEY to run the real end-to-end test.
"""
from __future__ import annotations

import os

from castgraph.consistency import consistency_report
from castgraph.memory import MemoryStore
from castgraph.pipeline import run_clip
from castgraph.provenance import explain
from castgraph.reasoning import GeminiReasoner, StubReasoner
from castgraph.retrieval import compare_retrieval_strategies
from scenario.marcus_sarah import CHARACTER, CLIPS

REASONER = GeminiReasoner() if os.environ.get("GEMINI_API_KEY") else StubReasoner()


def hr(title: str) -> None:
    print(f"\n{'=' * 10} {title} {'=' * 10}")


def run() -> None:
    print(f"Reasoner: {type(REASONER).__name__}")
    store = MemoryStore()
    entity_id = None
    history: list[list[dict]] = []

    for clip in CLIPS:
        hr(f"CLIP {clip['id']}")
        print(f"Creator prompt: {clip['prompt']}")

        result = run_clip(
            store, CHARACTER, clip["id"], clip["clip_text"], clip["prompt"], REASONER,
        )
        entity_id = result.entity_id

        print(f"Identity resolution: {CHARACTER} -> {result.entity_id} "
              f"(method={result.identity.method}, confidence={result.identity.confidence})")
        print(f"Extracted location: {result.location!r}")
        print("\n--- retrieved context handed to (stubbed) generator ---")
        print(result.context)
        print(f"\nObserved attributes: {result.observed}")
        print("\nVerification report:")
        for item in result.report:
            print(f"  [{item['status']}] {item['attribute']}: {item['detail']}")
        history.append(result.report)

    hr("FINAL MEMORY STATE")
    print(store.to_json())

    hr("MEMORY SIZE")
    print(f"{store.size_bytes()} bytes")

    hr("RETRIEVAL COMPARISON (scenario-specific, see PHASE_08.md before generalizing)")
    print(compare_retrieval_strategies(store, [entity_id]))

    hr("CONSISTENCY REPORT (per-attribute; aggregate is a naive mean, see below)")
    report_summary = consistency_report(history)
    for attr, stats in report_summary["per_attribute"].items():
        print(f"  {attr}: {stats['rate']:.2f} consistent ({stats['checked']} checked)")
    print(f"  aggregate: {report_summary['aggregate']} -- {report_summary['aggregate_caveat']}")

    hr("PROVENANCE / AUDIT: why is 'voice' what it is")
    print(explain(store, entity_id, "voice"))

    hr("UNEXPLAINED DRIFT REQUIRING REVIEW")
    entity = store.entities[entity_id]
    if not entity.unexplained:
        print("(none)")
    for dev in entity.unexplained:
        print(
            f"  {dev.attribute}: canonical={dev.canonical_value!r} vs "
            f"observed={dev.observed_value!r} (clip {dev.clip_ref.clip_id})\n"
            f"    reason: {dev.reasoning}"
        )


if __name__ == "__main__":
    run()
