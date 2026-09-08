# Temporal world-state engine — stub

Phase 6 of the design brief. Deliberately not implemented yet: the MVP's
4-clip scenario has no flashbacks, time jumps, or overlapping intervals to
reason about, so there's nothing real to design against yet.

`castgraph.drift.reconcile` currently treats clips as a simple ordered
sequence (evidence lists are append-only, in clip order). When a future
session needs real temporal semantics (answering "what was true at time T",
reconstructing state at an arbitrary point, reasoning about flashbacks),
build it here rather than overloading the memory model — see ROADMAP.md,
future session 1.
