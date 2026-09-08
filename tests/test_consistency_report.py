from castgraph.consistency import consistency_report


def test_computes_rate_excluding_established_and_dynamic():
    history = [
        [{"attribute": "voice", "status": "ESTABLISHED", "detail": ""}],
        [{"attribute": "voice", "status": "CONSISTENT", "detail": ""}],
        [{"attribute": "voice", "status": "CONSISTENT", "detail": ""}],
        [{"attribute": "voice", "status": "UNEXPLAINED_DRIFT", "detail": ""}],
        [{"attribute": "outfit", "status": "DYNAMIC", "detail": ""}],
    ]
    result = consistency_report(history)
    assert result["per_attribute"]["voice"]["checked"] == 3
    assert result["per_attribute"]["voice"]["rate"] == 2 / 3
    assert "outfit" not in result["per_attribute"]
    assert result["aggregate"] == 2 / 3


def test_no_checked_observations_gives_none_aggregate():
    history = [[{"attribute": "voice", "status": "ESTABLISHED", "detail": ""}]]
    result = consistency_report(history)
    assert result["per_attribute"] == {}
    assert result["aggregate"] is None
