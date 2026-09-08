"""The MVP test scenario: one character (Marcus), a handful of independently
"generated" clips (synthetic text stand-ins), including one legitimate
narrative-explained deviation and one unexplained one. Matches the worked
example from the original design brief.
"""

CLIPS = [
    {
        "id": "ep1",
        "prompt": "Marcus talks to Sarah at the docks.",
        "clip_text": (
            "Marcus, a man with black hair and a deep, rough voice, speaks "
            "to Sarah at the docks. He is reserved and sarcastic, as usual."
        ),
    },
    {
        "id": "ep2",
        "prompt": "Marcus talks to Sarah outside the hospital.",
        "clip_text": (
            "Marcus, black hair, deep rough voice, meets Sarah outside the "
            "hospital. He is sarcastic as ever."
        ),
    },
    {
        "id": "ep3",
        "prompt": (
            "Marcus is disguising his voice to avoid being recognized while "
            "he talks to Sarah in the crowded market."
        ),
        "clip_text": (
            "Marcus, black hair, speaks to Sarah with a soft, high voice, "
            "clearly putting on a disguise in the crowded market."
        ),
    },
    {
        "id": "ep4",
        "prompt": "Marcus talks to Sarah at the docks again.",
        "clip_text": (
            "Marcus, black hair, speaks to Sarah at the docks with a soft, "
            "high voice."
        ),
    },
]

CHARACTER = "Marcus"
