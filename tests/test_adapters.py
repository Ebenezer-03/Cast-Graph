import json

from castgraph.adapters import build_context_data, render_text, render_json


def _sample_context():
    retrieved = {
        "marcus": {
            "name": "Marcus",
            "canonical": {"voice": "deep/rough"},
            "confidence": {"voice": 0.5},
        }
    }
    return build_context_data(retrieved, "Marcus talks to Sarah.", location="docks")


def test_text_and_json_renderers_preserve_the_same_facts():
    context_data = _sample_context()

    text = render_text(context_data)
    assert "deep/rough" in text
    assert "docks" in text

    as_json = render_json(context_data)
    parsed = json.loads(as_json)
    assert parsed["entities"]["marcus"]["canonical"]["voice"] == "deep/rough"
    assert parsed["location"] == "docks"


def test_renderers_dont_require_touching_memory_or_retrieval_code():
    # Same context_data object serves both renderers -- proves the
    # generator-independent structure is the actual seam, not the renderer.
    context_data = _sample_context()
    assert render_text(context_data)
    assert render_json(context_data)
