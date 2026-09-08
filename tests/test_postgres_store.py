"""Integration test against the real Neon Postgres instance (decision
0004). Skipped automatically when DATABASE_URL isn't set (e.g. CI without
the real database) -- this is real infrastructure, not mocked, by design;
see docs/phases/PHASE_14.md for why mocking it would defeat the point of
"production grade, tested end to end"."""
import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

from castgraph.memory import ClipRef, MemoryStore
from castgraph.memory.postgres_store import ensure_schema, load_store, save_store

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set -- this test hits the real Neon Postgres instance",
)


@pytest.fixture
def conn():
    connection = psycopg.connect(os.environ["DATABASE_URL"])
    ensure_schema(connection)
    yield connection
    connection.close()


def test_unwritten_project_loads_empty(conn):
    project_id = f"test-{uuid.uuid4()}"
    store = load_store(conn, project_id)
    assert store.entities == {}


def test_save_then_load_round_trips_real_data(conn):
    project_id = f"test-{uuid.uuid4()}"
    store = MemoryStore()
    store.get_or_create("marcus", "Marcus")
    store.establish("marcus", "voice", "deep/rough", ClipRef("ep1", "intro"))

    save_store(conn, project_id, store)
    reloaded = load_store(conn, project_id)

    assert reloaded.entities["marcus"].canonical["voice"].value == "deep/rough"
    assert reloaded.clip_sequence == ["ep1"]

    # cleanup -- don't leave test rows in the real database
    with conn.cursor() as cur:
        cur.execute("DELETE FROM memory_stores WHERE project_id = %s", (project_id,))
    conn.commit()
