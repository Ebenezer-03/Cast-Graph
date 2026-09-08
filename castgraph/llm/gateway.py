"""Thin client for the reasoning-step LLM calls, routed through the Vercel
AI Gateway (OpenAI-compatible chat completions endpoint).

This is the only place in the codebase that talks to an LLM. Every other
module receives already-parsed structured data, so swapping providers or
models later touches only this file.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

GATEWAY_URL = "https://ai-gateway.vercel.sh/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-5"


class GatewayError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("AI_GATEWAY_API_KEY")
    if not key:
        raise GatewayError(
            "AI_GATEWAY_API_KEY is not set in the environment."
        )
    return key


def complete(prompt: str, *, system: str | None = None, model: str = DEFAULT_MODEL,
             temperature: float = 0.0) -> str:
    """Send a single-turn chat completion request, return the raw text reply."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        GATEWAY_URL,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        json={"model": model, "messages": messages, "temperature": temperature},
        timeout=60,
    )
    if resp.status_code != 200:
        raise GatewayError(f"gateway request failed ({resp.status_code}): {resp.text[:500]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise GatewayError(f"unexpected gateway response shape: {data}") from exc


def complete_json(prompt: str, *, system: str | None = None, model: str = DEFAULT_MODEL) -> Any:
    """Like complete(), but parses the reply as JSON. Tolerates the model
    wrapping the JSON in a markdown code fence."""
    raw = complete(prompt, system=system, model=model, temperature=0.0)
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    text = fenced.group(1) if fenced else raw
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GatewayError(f"could not parse JSON from model reply: {raw[:500]}") from exc
