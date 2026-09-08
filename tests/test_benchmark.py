"""Regression test for the Phase 15 benchmark: pins the actual observed
numbers from eval/run_benchmark.py so future changes to reconcile()/
StubReasoner don't silently shift behavior unnoticed. Not a claim that
these specific numbers generalize -- see docs/phases/PHASE_15.md.
"""
from eval.run_benchmark import run_baseline_a_no_memory, run_castgraph
from eval.drift_benchmark import build_clips


def test_baseline_a_never_detects_anything():
    clips = build_clips()
    result = run_baseline_a_no_memory(clips)
    assert result["flags_raised"] == 0


def test_castgraph_recall_is_perfect_precision_has_known_false_positives():
    clips = build_clips()
    result = run_castgraph(clips, promotion_threshold=2)
    # recall: every truly-unexplained clip gets flagged (nothing is missed)
    assert result["drift_detection_recall"] == 1.0
    # precision: known false positives from the promotion-changes-canonical
    # benchmark-labeling artifact documented in PHASE_15.md subtask 10 --
    # asserted explicitly so a future fix to the benchmark labels (not the
    # reconciliation logic) is a deliberate, visible change to this test.
    assert result["confusion"]["fp"] == 2


def test_ablation_without_promotion_matches_labels_exactly_on_this_benchmark():
    clips = build_clips()
    result = run_castgraph(clips, promotion_threshold=10_000)
    assert result["status_accuracy"] == 1.0
    assert result["confusion"]["fp"] == 0
