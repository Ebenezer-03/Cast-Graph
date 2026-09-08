"""The reasoning-step interface. Every place the architecture needs judgment
(extract attributes from a clip, understand a prompt, classify a deviation)
goes through a `Reasoner`. See decisions/0002-stub-llm-reasoning-for-now.md:
`StubReasoner` is deterministic and used today; `GatewayReasoner` is real but
unexercised until an API key exists. Swapping is a one-line change.
"""
from __future__ import annotations

from typing import Protocol

from castgraph.llm import gateway
from castgraph.llm import gemini
from castgraph.prompt import extract_transformation_cues


class Reasoner(Protocol):
    def extract_observation(self, clip_text: str, character_name: str) -> dict:
        """Return {"attribute": value, ...} observed for character_name in clip_text."""
        ...

    def understand_prompt(self, prompt: str, known_entities: list[str]) -> dict:
        """Return {"entities": [...], "narrative_context": str}."""
        ...

    def classify_drift(self, attribute: str, canonical_value: str, observed_value: str,
                        narrative_context: str) -> dict:
        """Return {"classification": ..., "reasoning": ...}."""
        ...


class GatewayReasoner:
    """Real implementation, calls the Vercel AI Gateway. Not exercised in
    this session (no key available) but ready to be swapped in."""

    def extract_observation(self, clip_text: str, character_name: str) -> dict:
        prompt = (
            f"Extract observable attributes of the character '{character_name}' "
            f"from this clip description. Reply as JSON with keys among: "
            f"voice, hair, appearance, personality, clothing. Only include what's "
            f"actually stated.\n\nClip:\n{clip_text}"
        )
        return gateway.complete_json(prompt)

    def understand_prompt(self, prompt: str, known_entities: list[str]) -> dict:
        instruction = (
            f"Given this creator prompt and this list of known characters "
            f"{known_entities}, return JSON: "
            f'{{"entities": [...names mentioned...], "narrative_context": "..."}}.'
            f"\n\nPrompt: {prompt}"
        )
        return gateway.complete_json(instruction)

    def classify_drift(self, attribute: str, canonical_value: str, observed_value: str,
                        narrative_context: str) -> dict:
        instruction = (
            f"Canonical {attribute} = {canonical_value!r}. Newly observed "
            f"{attribute} = {observed_value!r}. Narrative context: "
            f"{narrative_context!r}. Classify this deviation as one of: "
            f"CONSISTENT, EXPECTED_CHANGE, EXPLAINED_TRANSITION, "
            f"TEMPORARY_OVERRIDE, UNEXPLAINED_DRIFT, AMBIGUOUS. Reply as JSON "
            f'{{"classification": "...", "reasoning": "..."}}.'
        )
        return gateway.complete_json(instruction)


class GeminiReasoner:
    """Real implementation, calls Gemini directly (see
    decisions/0003-use-gemini-not-vercel-gateway.md for why Gemini rather
    than the originally-planned Vercel AI Gateway). This is the first
    reasoner in this project ever exercised against a real LLM."""

    _JSON_ONLY = "Reply with ONLY a single JSON object, no markdown fence, no other text."

    def extract_observation(self, clip_text: str, character_name: str) -> dict:
        # Normalized-categorical instruction, not free text -- Phase 3
        # subtask 12 predicted exactly this gap (real LLM output doesn't
        # naturally match a fixed canonical string) and recommended this
        # fix. "voice" is constrained to this scenario's two known values;
        # a general system would need a real controlled vocabulary per
        # attribute, not a hardcoded pair -- this is a scenario-specific
        # mitigation, not a general solution.
        prompt = (
            f"Extract observable attributes of the character '{character_name}' "
            f"from this clip description. Reply as a JSON object with keys among: "
            f"voice, hair, appearance, personality, clothing. Only include what's "
            f"actually stated in the text; omit keys with no evidence. "
            f"For 'voice' specifically, reply with exactly one of the literal "
            f"strings 'deep/rough' or 'soft/high' (pick whichever the text "
            f"actually describes) -- not a paraphrase. "
            f"{self._JSON_ONLY}\n\nClip:\n{clip_text}"
        )
        return gemini.complete_json(prompt)

    def understand_prompt(self, prompt: str, known_entities: list[str]) -> dict:
        instruction = (
            f"Given this creator prompt and this list of known characters "
            f"{known_entities}, return a JSON object: "
            f'{{"entities": [...names from the list that are mentioned...], '
            f'"narrative_context": "..."}}. {self._JSON_ONLY}'
            f"\n\nPrompt: {prompt}"
        )
        return gemini.complete_json(instruction)

    def classify_drift(self, attribute: str, canonical_value: str, observed_value: str,
                        narrative_context: str) -> dict:
        instruction = (
            f"Canonical {attribute} = {canonical_value!r}. Newly observed "
            f"{attribute} = {observed_value!r}. Narrative context: "
            f"{narrative_context!r}. Classify this deviation as exactly one of: "
            f"CONSISTENT, EXPECTED_CHANGE, EXPLAINED_TRANSITION, "
            f"TEMPORARY_OVERRIDE, UNEXPLAINED_DRIFT, AMBIGUOUS. Reply as a JSON "
            f'object {{"classification": "...", "reasoning": "..."}}. '
            f"{self._JSON_ONLY}"
        )
        return gemini.complete_json(instruction)


class StubReasoner:
    """Deterministic stand-in. Rules are written to fit the MVP scenario only
    — see decisions/0002 for why this must not be read as evidence the
    approach generalizes."""

    def extract_observation(self, clip_text: str, character_name: str) -> dict:
        text = clip_text.lower()
        obs: dict = {}
        if "soft" in text and "voice" in text:
            obs["voice"] = "soft/high"
        elif "deep" in text and "voice" in text:
            obs["voice"] = "deep/rough"
        if "black hair" in text:
            obs["hair"] = "black"
        if "sarcastic" in text:
            obs["personality"] = "reserved, sarcastic"
        return obs

    def understand_prompt(self, prompt: str, known_entities: list[str]) -> dict:
        mentioned = [name for name in known_entities if name.lower() in prompt.lower()]
        context = prompt
        return {"entities": mentioned, "narrative_context": context}

    def classify_drift(self, attribute: str, canonical_value: str, observed_value: str,
                        narrative_context: str) -> dict:
        cues = extract_transformation_cues(narrative_context)
        if "disguise" in cues and "injury" in cues:
            return {
                "classification": "AMBIGUOUS",
                "reasoning": (
                    f"{attribute} differs from canonical ({canonical_value!r} -> "
                    f"{observed_value!r}); both disguise and injury cues are "
                    f"present in the narrative context, and a keyword match "
                    f"can't resolve which (if either) actually applies. "
                    f"Surfaced for review rather than guessed at."
                ),
            }
        if "disguise" in cues:
            return {
                "classification": "TEMPORARY_OVERRIDE",
                "reasoning": (
                    f"{attribute} differs from canonical ({canonical_value!r} -> "
                    f"{observed_value!r}), but the prompt indicates a disguise. "
                    f"Treated as an intentional, temporary deviation."
                ),
            }
        if "injury" in cues:
            return {
                "classification": "EXPLAINED_TRANSITION",
                "reasoning": (
                    f"{attribute} differs from canonical, explained by an "
                    f"injury/recovery narrative beat."
                ),
            }
        return {
            "classification": "UNEXPLAINED_DRIFT",
            "reasoning": (
                f"{attribute} differs from canonical ({canonical_value!r} -> "
                f"{observed_value!r}) with no narrative explanation found in "
                f"the prompt/context. Canonical state is preserved; this is "
                f"surfaced for review rather than applied."
            ),
        }
