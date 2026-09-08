# PHASE 15 — Benchmarking, Validation and Production Readiness

## Objective

Build a serious evaluation framework: baselines, ablations, memory-budget
experiments, long-horizon experiments, drift benchmarks. Per the brief's own
Section 24 rule, this phase must not invent results — where a real
experiment (real generator, real dataset, real held-out labels) is not
buildable in this project, that is stated, not faked. Where a small, honest,
clearly-scoped synthetic experiment *is* buildable without those
prerequisites, it is built and run for real.

## What is genuinely run this phase, and what is not

**Run for real** (small, synthetic, mechanism-level — see caveats below):
- A long-horizon synthetic scenario (`eval/drift_benchmark.py`): 28 clips
  for one character mixing consistent observations, two categories of
  legitimate change (disguise, injury — the only two `StubReasoner` can
  recognize), one-off unexplained drift, and a sustained run that should
  trigger promotion.
- Two baselines actually implemented and run against it: **Baseline A (no
  memory)** — every observation is accepted as the new "canonical" fact
  with no reconciliation, nothing is ever flagged; **Baseline F (CastGraph,
  full)** — the actual pipeline built across Phases 1-13.
- Drift-detection precision/recall of Baseline F against the benchmark's
  ground-truth labels (subtask below).
- A rerun of Baseline F with promotion disabled (`PROMOTION_THRESHOLD` set
  effectively infinite) as **Ablation 5-equivalent** ("no drift
  attribution's promotion consequence") to show what changes.

**Not run, explicitly** (matches ROADMAP.md, restated with the specific
reason each requires):
- Baselines B/C/D/E (full historical context, naive retrieval,
  embedding-only memory, structured-without-temporal) — meaningfully
  distinguishing these requires a real generator producing real
  inconsistency for a real LLM to be prompted with; with no generator,
  "full history vs. selective retrieval" collapses to a token-count
  argument already covered narrowly by Phase 8, not a real quality
  comparison.
- The full memory-budget matrix (10KB-10MB) — Phase 12 built the mechanism
  (`enforce_budget`) and tested it works; running it as a matrix against a
  28-clip single-character benchmark would produce numbers with no
  informative variance (this scenario never approaches even the 10KB
  budget).
- The 500-generation long-horizon point, ablations 8/9 (embedding-only,
  structured-only memory) — no embedding memory variant exists to compare
  against (Principle 3 — never built one, nothing to ablate).
- Statistical validation (significance testing) — one 28-clip run has no
  variance/repetition to test significance over; would be theater.
- Novelty/literature validation beyond Phase 1's single search pass.

## Subtasks

### 1. Benchmark dataset design

`eval/drift_benchmark.py`: 28 synthetic clips, each labeled with an
**expected classification category** (independent of `StubReasoner`'s
internals — labels reflect the brief's own drift-benchmark categories:
`consistent`, `legitimate_disguise`, `legitimate_injury`,
`unexplained_drift_oneoff`, `unexplained_drift_sustained`). **Caveat
stated directly, not hidden**: because `StubReasoner` classifies using the
same disguise/injury keyword cues the labels are built from, this
benchmark measures whether the *reconciliation/promotion plumbing* behaves
correctly given a classification, not whether classification itself
generalizes to real ambiguous language. A real classification-quality
benchmark needs `GatewayReasoner` exercised against genuinely varied
phrasing — not possible without a working key (decision 0002).

### 2. Synthetic controlled worlds

The benchmark clips are entirely synthetic text, consistent with the whole
project's stated constraint (no generator).

### 3. Real-world/generated worlds

Not available — no generator integration exists.

### 4. Long-horizon experiments

28 clips run in sequence is the long-horizon test that's actually
buildable; not the 100/250/500-clip points from the brief (would take
proportionally more hand-authored/label-verified synthetic data with no
added insight at this project's current stage — diminishing signal for
sharply increasing authoring cost).

### 5. Controlled drift injection

Implemented in the benchmark's label design directly (subtask 1).

### 6. Baseline comparison

Baseline A (no memory) vs. Baseline F (CastGraph) — implemented and run;
see results below and in `eval/results/`.

### 7. Ablation studies

One ablation run for real (promotion disabled) — see results. The other
nine from the brief's list are either already *effectively* covered by
what's been built-and-tested incrementally through Phases 2-13 (e.g. "no
selective retrieval" is what Baseline-A-style full-dump behavior already
looks like structurally) or require infrastructure that doesn't exist
(embedding memory) — not run separately to avoid manufacturing redundant
or meaningless ablation runs just to fill a checklist.

### 8. Memory-budget experiments

Not run as a matrix (reason above); `enforce_budget` (Phase 12) already
demonstrated to work on this same benchmark's data as a smoke test.

### 9. Latency/cost experiments

Not run — `StubReasoner` has no real latency/cost profile (no network
call); the only components with real cost (`GatewayReasoner`) are
unexercised (decision 0002). Nothing honest to measure yet.

### 10. Failure analysis

Reported directly from the actual benchmark run (`eval/results/benchmark_report.json`),
not glossed over:

- **Baseline F (promotion enabled) status accuracy: 0.93 (26/28)**, drift-
  detection precision 0.67, recall 1.0. **Real, unplanned finding**: the
  two "mistakes" are both benchmark-authoring artifacts, not reconciliation
  bugs — after `unexplained_drift_sustained` triggers a promotion (Phase 5),
  canonical truth genuinely changes to the new value; the next two
  "consistent" clips in the hand-authored sequence were written assuming
  the *original* value stays canonical forever, so they get (correctly,
  relative to the *new* canonical value) flagged as drift. This is exactly
  the kind of subtlety the brief warns about: **once memory is allowed to
  update, "consistent" must be judged against current canonical truth, not
  the value the benchmark author had in mind when writing the clip.** Left
  in rather than quietly rewritten, because it's a genuinely instructive
  result about how promotion changes what "correct" even means downstream,
  not a defect to hide.
- **Ablation (promotion disabled) status accuracy: 1.00 (28/28)**, drift
  detection precision 1.0, recall 1.0 — every deviation classified exactly
  as labeled, because with promotion off, canonical truth never moves, so
  the "consistent" clips' assumption (that the original value stays
  canonical) holds throughout. **This makes the ablation look strictly
  better than the full system on this specific benchmark** — a direct
  illustration of RQ6-adjacent tension: promotion (a feature meant to let
  memory update to a genuine sustained change) actively hurts a
  benchmark's measured accuracy the moment the benchmark's own labels don't
  account for that update. Not a reason to remove promotion (a system that
  can never update canonical truth has its own, worse failure mode: the
  `PROMOTION_THRESHOLD` rationale in `docs/phases/PHASE_05.md` still holds)
  — but a concrete demonstration that **evaluation harnesses for a
  self-updating memory system need labels that also account for legitimate
  updates, which this one, as authored, did not.** Recorded as a
  to-fix-next-time item, not corrected retroactively by relabeling after
  seeing the result.
- **Baseline A: 0 flags, by construction.** Not a finding so much as the
  expected floor — included to make the contrast with Baseline F/ablation
  visible in one report rather than asserted only in prose.

### 11. Statistical validation

Not run (reason above, subtask "not run" list).

### 12. Production-readiness assessment

Answered directly: **not production-ready.** Phase 14 stated why (no real
generator, no real workload). This phase's benchmark reinforces it from
the evaluation side: the only classifier exercised (`StubReasoner`) is a
keyword matcher, not validated against real ambiguous language.

## Running the benchmark

`python -m eval.run_benchmark` (run as a module, from the repo root, so
`eval`'s package-relative imports resolve) runs both baselines against
`eval/drift_benchmark.py` and writes a report to stdout (and, so results
aren't just terminal scrollback, `eval/results/benchmark_report.json`).

## Architecture Changes From Previous Phase

- New `eval/drift_benchmark.py`: 28 labeled synthetic clips.
- New `eval/run_benchmark.py`: runs Baseline A, Baseline F, and the
  promotion-disabled ablation; computes precision/recall for
  unexplained-drift detection; writes a JSON report.
- `castgraph/drift/reconcile.py`'s `PROMOTION_THRESHOLD` made overridable
  per-call (was a module constant only) so the ablation can disable it
  without a monkeypatch.

## Risks

- The central risk, stated as plainly as possible: **this benchmark's
  positive results (if any) demonstrate correct plumbing, not validated
  real-world drift detection.** Anyone citing this project's "precision/
  recall" numbers without that caveat would be misrepresenting them.

## Validation

The benchmark run itself is the validation artifact for this phase; a
pytest also asserts Baseline F's precision/recall on this specific
benchmark stay within an expected range (regression protection, not a
claim of generalization).

## Deliverables

- This document.
- `eval/drift_benchmark.py`, `eval/run_benchmark.py`.
- `eval/results/benchmark_report.json` (generated, checked in as the actual
  run's output — not fabricated).
- Regression test.

## Quality Gate

- **Research quality**: every number produced this phase is labeled with
  exactly what it does and doesn't demonstrate — passes Section 24 directly.
- **Failure-mode check**: does this collapse into "a fake benchmark for
  show"? Resisted by explicitly listing nine things this phase does *not*
  claim to have validated, right alongside the one thing it does.
