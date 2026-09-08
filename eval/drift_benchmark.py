"""Phase 15: a small, labeled, synthetic drift benchmark for one character's
`voice` attribute. See docs/phases/PHASE_15.md for what this can and cannot
validate -- StubReasoner's classification cues were used to construct these
labels, so this benchmark tests reconciliation/promotion plumbing, not
classification generalization to real, varied language.
"""
from __future__ import annotations

CHARACTER = "Marcus"

# Ground-truth category for each clip, in order. "consistent" clips (after
# the first) should match canonical; the first is the baseline
# establishment; legitimate_* clips are narratively explained;
# unexplained_drift_* clips have no explanation, with "_sustained" repeated
# to test promotion (Phase 5).
CATEGORY_SEQUENCE = (
    ["consistent"] * 3
    + ["legitimate_disguise"]
    + ["consistent"] * 2
    + ["legitimate_injury"]
    + ["consistent"] * 2
    + ["unexplained_drift_oneoff"]
    + ["consistent"] * 3
    + ["unexplained_drift_sustained", "unexplained_drift_sustained"]
    + ["consistent"] * 3
    + ["legitimate_disguise"]
    + ["consistent"] * 5
    + ["unexplained_drift_oneoff"]
    + ["consistent"] * 3
)

_TEMPLATES = {
    "consistent": (
        "Marcus talks to Sarah at the docks.",
        "Marcus, black hair, deep rough voice, talks to Sarah at the docks.",
    ),
    "legitimate_disguise": (
        "Marcus is disguising his voice to avoid being recognized.",
        "Marcus, black hair, speaks with a soft, high voice, clearly in disguise.",
    ),
    "legitimate_injury": (
        "Marcus, recovering from an injury, talks to Sarah.",
        "Marcus, black hair, speaks with a soft, high voice while recovering.",
    ),
    "unexplained_drift_oneoff": (
        "Marcus talks to Sarah at the docks again.",
        "Marcus, black hair, speaks with a soft, high voice.",
    ),
    "unexplained_drift_sustained": (
        "Marcus talks to Sarah at the docks again.",
        "Marcus, black hair, speaks with a soft, high voice.",
    ),
}

# Which reconcile() statuses count as "correct" for each category. The
# very first clip is always ESTABLISHED regardless of category (nothing is
# canonical yet); handled specially in build_clips().
EXPECTED_STATUS = {
    "consistent": {"CONSISTENT"},
    "legitimate_disguise": {"TEMPORARY_OVERRIDE"},
    "legitimate_injury": {"EXPLAINED_TRANSITION"},
    "unexplained_drift_oneoff": {"UNEXPLAINED_DRIFT"},
    "unexplained_drift_sustained": {"UNEXPLAINED_DRIFT", "PROMOTED"},
}

# Ground-truth binary label for the drift-detection precision/recall
# measurement (subtask 6 of PHASE_15.md): is this clip a real, unexplained
# change that a consistency system should flag?
IS_UNEXPLAINED = {
    "consistent": False,
    "legitimate_disguise": False,
    "legitimate_injury": False,
    "unexplained_drift_oneoff": True,
    "unexplained_drift_sustained": True,
}


def build_clips() -> list[dict]:
    clips = []
    for i, category in enumerate(CATEGORY_SEQUENCE):
        prompt, clip_text = _TEMPLATES[category]
        clips.append({
            "id": f"clip{i:02d}",
            "category": "consistent" if i == 0 else category,
            "prompt": prompt,
            "clip_text": clip_text,
            "is_baseline": i == 0,
        })
    return clips
