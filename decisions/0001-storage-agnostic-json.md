# 0001 — Use plain JSON files for MVP memory storage

**Context**: The memory model must be storage-agnostic (design principle 2) —
no specific database should be baked into the logical model. The MVP needs
*some* concrete persistence to run at all.

**Options considered**:
- Neo4j / graph database — rejected for MVP: heavy dependency, and the design
  brief explicitly warns against conflating the logical model with a graph
  database implementation this early.
- SQLite — reasonable, rejected only because JSON is more transparent for a
  first pass (memory contents are readable by eye, easy to diff between runs).
- Vector database / embeddings — rejected: nothing in the MVP scenario needs
  semantic similarity search yet (retrieval is by explicit entity name).

**Chosen approach**: plain JSON file(s) via a thin `MemoryStore` abstraction.
The abstraction is the actual deliverable; JSON is a swappable detail.

**Consequences**: trivial to inspect/debug; no concurrency story (fine, MVP
runs single-process); will need to change when memory volume or concurrent
writers show up (see ROADMAP.md future sessions).

**Reversal condition**: revisit once Phase 12 (consolidation/compression) or
real concurrent multi-user access becomes relevant.
