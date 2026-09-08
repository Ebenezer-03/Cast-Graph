# Benchmarking / evaluation — deferred

Phase 15, the ablation studies, the memory-budget matrix (10KB-10MB), and
the long-horizon experiment all need either a real video generator or a
much larger, deliberately-designed synthetic dataset to produce numbers that
mean anything. A 4-clip demo scenario cannot support any of that; running
these "experiments" against it now would just be theater.

See ROADMAP.md, future session 5, for what needs to happen before this
directory gets real content: a benchmark dataset design with controlled
drift injection (legitimate changes vs. unexplained drift, per the drift
benchmark categories in the original brief) is the prerequisite.
