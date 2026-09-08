"""Real LLM client: Google Gemini's generateContent REST API, called
directly with GEMINI_API_KEY (a free-tier key, no billing on file -- see
decisions/0003-use-gemini-not-vercel-gateway.md for why this replaced the
originally-planned Vercel AI Gateway path). Mirrors castgraph/llm/gateway.py's
shape so GatewayReasoner and GeminiReasoner are structurally interchangeable.
"""
from __future__ import annotations

import json
import os
import re
import time

import requests

DEFAULT_MODEL = "gemini-3.6-flash"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Free-tier Gemini returns 503 UNAVAILABLE under load reasonably often --
# a real production failure mode observed while testing this client, not a
# hypothetical. Retry with backoff on the transient status codes only.
_RETRYABLE_STATUS = {429, 503}
_MAX_RETRIES = 3
_BACKOFF_SECONDS = 2


class GeminiError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise GeminiError("GEMINI_API_KEY is not set in the environment.")
    return key


def complete(prompt: str, *, system: str | None = None, model: str = DEFAULT_MODEL,
             temperature: float = 0.0) -> str:
    """Send a single-turn generateContent request, return the raw text reply."""
    contents = [{"parts": [{"text": prompt}]}]
    body: dict = {"contents": contents, "generationConfig": {"temperature": temperature}}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        resp = requests.post(
            f"{API_BASE}/{model}:generateContent",
            params={"key": _api_key()},
            json=body,
            timeout=60,
        )
        if resp.status_code == 200:
            break
        last_error = GeminiError(f"gemini request failed ({resp.status_code}): {resp.text[:500]}")
        if resp.status_code not in _RETRYABLE_STATUS or attempt == _MAX_RETRIES:
            raise last_error
        time.sleep(_BACKOFF_SECONDS * (2 ** attempt))
    else:
        raise last_error  # pragma: no cover -- loop always breaks or raises above

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as exc:
        raise GeminiError(f"unexpected gemini response shape: {data}") from exc


def complete_json(prompt: str, *, system: str | None = None, model: str = DEFAULT_MODEL) -> object:
    """Like complete(), but parses the reply as JSON. Tolerates the model
    wrapping the JSON in a markdown code fence."""
    raw = complete(prompt, system=system, model=model, temperature=0.0)
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    text = fenced.group(1) if fenced else raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"could not parse JSON from model reply: {raw[:500]}") from exc
