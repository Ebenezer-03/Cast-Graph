from castgraph.prompt import extract_location, extract_transformation_cues


def test_extract_location_finds_at_the_place():
    assert extract_location("Marcus talks to Sarah at the docks.") == "docks"


def test_extract_location_finds_outside_the_place():
    assert extract_location("Marcus talks to Sarah outside the hospital.") == "hospital"


def test_extract_location_returns_none_when_absent():
    assert extract_location("Marcus talks to Sarah.") is None


def test_extract_transformation_cues_detects_disguise():
    cues = extract_transformation_cues("Marcus is disguising his voice.")
    assert "disguise" in cues
    assert "injury" not in cues


def test_extract_transformation_cues_detects_injury():
    cues = extract_transformation_cues("Marcus is recovering from an injury.")
    assert "injury" in cues


def test_extract_transformation_cues_empty_when_no_cue():
    assert extract_transformation_cues("Marcus talks to Sarah at the docks.") == []
