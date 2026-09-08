"""Production storage: Neon Postgres instead of a local JSON file (Phase
14, made real this session -- see decisions/0001-storage-agnostic-json.md
for why a JSONB blob per project, not a normalized schema, was chosen: the
serialization format (MemoryStore.to_dict()) is unchanged, only where the
bytes live moved from disk to a durable, shared database. This is exactly
the swap decision 0001 predicted would eventually be needed.
"""
from __future__ import annotations

import json

import psycopg

from castgraph.memory import MemoryStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_stores (
    project_id TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def ensure_schema(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(_SCHEMA)
    conn.commit()


def load_store(conn: psycopg.Connection, project_id: str) -> MemoryStore:
    """Returns the project's MemoryStore, or a fresh empty one if this
    project has never been written yet (no row is created until save)."""
    with conn.cursor() as cur:
        cur.execute("SELECT data FROM memory_stores WHERE project_id = %s", (project_id,))
        row = cur.fetchone()
    if row is None:
        return MemoryStore()
    return MemoryStore.from_dict(row[0])


def save_store(conn: psycopg.Connection, project_id: str, store: MemoryStore) -> None:
    """Upserts the project's full memory state. Concurrency note: this is a
    last-writer-wins upsert, not optimistic-locked -- fine for the single
    -project, low-concurrency real end-to-end test this session runs; a
    real multi-writer product would need a version check here (Phase 14
    concern, not solved by this swap)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO memory_stores (project_id, data, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (project_id)
            DO UPDATE SET data = EXCLUDED.data, updated_at = now()
            """,
            (project_id, json.dumps(store.to_dict(), default=list)),
        )
    conn.commit()
