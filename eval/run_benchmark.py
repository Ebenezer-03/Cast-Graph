"""Phase 15: runs Baseline A (no memory), Baseline F (CastGraph, full), and
a promotion-disabled ablation against eval/drift_benchmark.py. Prints and
writes a report. See docs/phases/PHASE_15.md for what these results do and
do not demonstrate -- read that before quoting any number from here.
"""
from __future__ import annotations

import json
from pathlib import Path

from castgraph.drift import reconcile
from castgraph.identity import resolve_identity
from castgraph.memory import ClipRef, MemoryStore
from castgraph.observation import observe
from castgraph.reasoning import StubReasoner
from eval.drift_benchmark import CHARACTER, EXPECTED_STATUS, IS_UNEXPLAINED, build_clips

REASONER = StubReasoner()


def run_baseline_a_no_memory(clips: list[dict]) -> dict:
    """No reconciliation at all: each observation silently becomes the new
    'truth', overwriting whatever was there. Nothing is ever flagged --
    included specifically to make that absence of detection visible."""
    detected = 0  # by construction, always 0
    for clip in clips:
        pass  # no-op: this baseline does not even look at attributes
    return {
        "name": "baseline_a_no_memory",
        "flags_raised": detected,
        "note": "no reconciliation exists in this baseline; it cannot ever flag a deviation",
    }


def run_castgraph(clips: list[dict], promotion_threshold: int) -> dict:
    store = MemoryStore()
    identity = resolve_identity(store, CHARACTER)
    entity_id = identity.entity_id

    correct = 0
    total_graded = 0
    tp = fp = fn = tn = 0
    mistakes = []

    for clip in clips:
        observed, clip_ref = observe(clip["id"], clip["clip_text"], CHARACTER, REASONER)
        report = reconcile(
            store, entity_id, observed, clip_ref,
            narrative_context=clip["prompt"], reasoner=REASONER,
            promotion_threshold=promotion_threshold,
        )
        voice_status = next((r["status"] for r in report if r["attribute"] == "voice"), None)
        if voice_status is None:
            continue

        expected = {"ESTABLISHED"} if clip["is_baseline"] else EXPECTED_STATUS[clip["category"]]
        total_graded += 1
        if voice_status in expected:
            correct += 1
        else:
            mistakes.append({"clip": clip["id"], "category": clip["category"],
                              "expected": sorted(expected), "actual": voice_status})

        if not clip["is_baseline"]:
            predicted_positive = voice_status in {"UNEXPLAINED_DRIFT", "PROMOTED", "AMBIGUOUS"}
            actual_positive = IS_UNEXPLAINED[clip["category"]]
            if predicted_positive and actual_positive:
                tp += 1
            elif predicted_positive and not actual_positive:
                fp += 1
            elif not predicted_positive and actual_positive:
                fn += 1
            else:
                tn += 1

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None

    return {
        "name": f"castgraph(promotion_threshold={promotion_threshold})",
        "status_accuracy": correct / total_graded if total_graded else None,
        "graded": total_graded,
        "drift_detection_precision": precision,
        "drift_detection_recall": recall,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "mistakes": mistakes,
        "final_memory_bytes": store.size_bytes(),
    }


def main() -> dict:
    clips = build_clips()

    results = {
        "caveat": (
            "See docs/phases/PHASE_15.md before quoting any number here: "
            "this is a small, synthetic, mechanism-level benchmark, not a "
            "validated real-world drift-detection result."
        ),
        "clip_count": len(clips),
        "baseline_a": run_baseline_a_no_memory(clips),
        "baseline_f": run_castgraph(clips, promotion_threshold=2),
        "ablation_no_promotion": run_castgraph(clips, promotion_threshold=10_000),
    }

    print(json.dumps(results, indent=2))

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "benchmark_report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    return results


if __name__ == "__main__":
    main()
