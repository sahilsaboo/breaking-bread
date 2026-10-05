from app.pipeline.fixtures import sample


def test_sample_fixture_reads_as_utf8():
    # Windows defaults to cp1252, which turns "°F" into "Â°F".
    notes = " ".join(s.get("safety_note") or "" for s in sample()["steps"])
    assert "165°F" in notes
    assert "Â" not in notes
