"""Runs the full CastGraph MVP loop:

    generate -> observe -> remember -> retrieve -> generate -> verify -> consolidate

over the Marcus/Sarah synthetic scenario, printing memory state and the
verification report at each step.

"Generate" is stubbed (clips are pre-written synthetic text, see
scenario/marcus_sarah.py) since no real video generator is wired up.
Reasoning steps use StubReasoner (see decisions/0002) — swap in
GatewayReasoner once a real AI_GATEWAY_API_KEY/ANTHROPIC_API_KEY exists.
"""
from __future__ import annotations

from castgraph.adapters import build_context
from castgraph.drift import reconcile
from castgraph.identity import resolve_identity
from castgraph.memory import MemoryStore
from castgraph.observation import observe
from castgraph.reasoning import StubReasoner
from castgraph.retrieval import retrieve
from scenario.marcus_sarah import CHARACTER, CLIPS

REASONER = StubReasoner()


def hr(title: str) -> None:
    print(f"\n{'=' * 10} {title} {'=' * 10}")


def run() -> None:
    store = MemoryStore()
    identity = resolve_identity(store, CHARACTER)
    entity_id = identity.entity_id
    print(f"Identity resolution: {CHARACTER} -> {entity_id} "
          f"(method={identity.method}, confidence={identity.confidence})")

    for clip in CLIPS:
        hr(f"CLIP {clip['id']}")
        print(f"Creator prompt: {clip['prompt']}")

        # 1. prompt understanding + selective retrieval (before generation)
        understanding = REASONER.understand_prompt(clip["prompt"], [CHARACTER])
        retrieved = retrieve(store, [entity_id])
        context = build_context(retrieved, understanding["narrative_context"])
        print("\n--- retrieved context handed to (stubbed) generator ---")
        print(context)

        # 2. "generation" is stubbed: the clip text is pre-written
        # 3. observation: extract structured attributes from the generated clip
        observed, clip_ref = observe(clip["id"], clip["clip_text"], CHARACTER, REASONER)
        print(f"\nObserved attributes: {observed}")

        # 4. verification + drift attribution + reconciliation
        report = reconcile(
            store, entity_id, observed, clip_ref,
            narrative_context=clip["prompt"], reasoner=REASONER,
        )
        print("\nVerification report:")
        for item in report:
            print(f"  [{item['status']}] {item['attribute']}: {item['detail']}")

    hr("FINAL MEMORY STATE")
    print(store.to_json())

    hr("MEMORY SIZE")
    print(f"{store.size_bytes()} bytes")

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
