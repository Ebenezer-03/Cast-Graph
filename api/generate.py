"""Production endpoint: POST one clip through the full CastGraph loop for a
project, backed by real Postgres (Neon) and a real LLM (Gemini, when
GEMINI_API_KEY is set -- falls back to StubReasoner otherwise so the
endpoint degrades gracefully rather than 500ing if the key is ever
missing). This is the Phase 14 API design turned real, minimally: one
endpoint, not the full surface documented in docs/phases/PHASE_14.md.

Request (POST), JSON body:
    {
      "project_id": "demo",
      "character": "Marcus",
      "clip_id": "ep1",
      "prompt": "Marcus talks to Sarah at the docks.",
      "clip_text": "Marcus, black hair, deep rough voice, ..."
    }

Response, JSON:
    {
      "identity": {"entity_id": ..., "method": ..., "confidence": ...},
      "location": ...,
      "context": "...",            # what would be handed to a real generator
      "observed": {...},
      "report": [...],             # per-attribute reconciliation report
      "memory_size_bytes": ...,
      "reasoner": "GeminiReasoner" | "StubReasoner"
    }

Optional request field "force_stub": true forces StubReasoner regardless
of GEMINI_API_KEY -- a test-only escape hatch (see
decisions/0005-force-stub-override-for-testing.md) added specifically to
let the real deployment/Postgres/HTTP path be exercised end to end while
the shared Gemini free-tier quota (decision 0004) is exhausted. It does
NOT bypass GEMINI_API_KEY-gated behavior in any way that matters for real
usage -- normal requests are unaffected unless they explicitly opt in.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler

import psycopg

from castgraph.memory.postgres_store import ensure_schema, load_store, save_store
from castgraph.pipeline import run_clip
from castgraph.reasoning import GeminiReasoner, StubReasoner


def _reasoner(force_stub: bool = False):
    if force_stub:
        return StubReasoner()
    return GeminiReasoner() if os.environ.get("GEMINI_API_KEY") else StubReasoner()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond(200, {"status": "ok", "service": "cast-graph"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")

            project_id = body["project_id"]
            character = body["character"]
            clip_id = body["clip_id"]
            prompt = body["prompt"]
            clip_text = body["clip_text"]
            force_stub = bool(body.get("force_stub", False))
        except (KeyError, json.JSONDecodeError) as exc:
            self._respond(400, {"error": f"invalid request body: {exc}"})
            return

        try:
            database_url = os.environ["DATABASE_URL"]
        except KeyError:
            self._respond(500, {"error": "DATABASE_URL is not configured"})
            return

        reasoner = _reasoner(force_stub)

        conn = psycopg.connect(database_url)
        try:
            ensure_schema(conn)
            store = load_store(conn, project_id)
            result = run_clip(store, character, clip_id, clip_text, prompt, reasoner)
            save_store(conn, project_id, store)
        except Exception as exc:  # noqa: BLE001 -- surface any failure as a clean 500, not a crash
            self._respond(500, {"error": str(exc), "reasoner": type(reasoner).__name__})
            return
        finally:
            conn.close()

        self._respond(200, {
            "identity": {
                "entity_id": result.identity.entity_id,
                "method": result.identity.method,
                "confidence": result.identity.confidence,
            },
            "location": result.location,
            "context": result.context,
            "observed": result.observed,
            "report": result.report,
            "memory_size_bytes": store.size_bytes(),
            "reasoner": type(reasoner).__name__,
        })

    def _respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
