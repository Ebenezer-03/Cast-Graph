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

# Free-tier Gemini returns 503 UNAVAILABLE under load, and 429
# RESOURCE_EXHAUSTED once the free tier's request-per-minute quota (5 RPM
# at time of writing) is hit -- both observed for real while testing this
# client against the MVP scenario, not hypothetical. Retry with backoff on
# the transient status codes only, honoring the server's own suggested
# delay for 429s rather than guessing a fixed backoff (a fixed 2/4/8s
# schedule was measured too short against a "retry in 30s" response).
_RETRYABLE_STATUS = {429, 503}
_MAX_RETRIES = 4
_BACKOFF_SECONDS = 2
_RETRY_DELAY_PATTERN = re.compile(r"retry in ([\d.]+)s", re.IGNORECASE)

# Proactive client-side rate limit, not just reactive retry: the free tier
# allows 5 requests/minute, so pace calls to stay under that rather than
# bursting through it and eating the 429/backoff cost every time. A real
# multi-instance production deployment would need a shared limiter (Redis,
# not in-process) -- this in-process one is honest about only protecting a
# single process, which is what this session's real end-to-end test is.
_RATE_LIMIT_PER_MINUTE = 5
_request_times: list[float] = []


def _throttle() -> None:
    now = time.monotonic()
    cutoff = now - 60
    while _request_times and _request_times[0] < cutoff:
        _request_times.pop(0)
    if len(_request_times) >= _RATE_LIMIT_PER_MINUTE:
        wait = _request_times[0] + 60 - now
        if wait > 0:
            time.sleep(wait)
    _request_times.append(time.monotonic())


def _retry_delay(attempt: int, response_text: str) -> float:
    match = _RETRY_DELAY_PATTERN.search(response_text)
    if match:
        return float(match.group(1)) + 1  # small margin over the server's own estimate
    return _BACKOFF_SECONDS * (2 ** attempt)


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
        _throttle()
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
        time.sleep(_retry_delay(attempt, resp.text))
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
