from scripts.audit.checks import recycle_cadence

STALE_MAP = {
    "кіт": [(1, 1), (2, 0), (3, 0)],
    "мама": [(2, 1)],
}


def test_recycle_cadence_uses_calibrated_a1_floor(monkeypatch):
    monkeypatch.setattr(recycle_cadence, "build_lemma_frequency_map", lambda _track, _module: STALE_MAP)
    monkeypatch.setattr(
        recycle_cadence,
        "_extract_all_ukrainian_surfaces",
        lambda _content: ["кіт", "кіт", "кіт"],
    )

    assert recycle_cadence.check_recycle_cadence("кіт кіт кіт", "a1", 8) == []


def test_recycle_cadence_warns_below_calibrated_a1_floor(monkeypatch):
    monkeypatch.setattr(recycle_cadence, "build_lemma_frequency_map", lambda _track, _module: STALE_MAP)
    monkeypatch.setattr(recycle_cadence, "_extract_all_ukrainian_surfaces", lambda _content: ["кіт"])

    violations = recycle_cadence.check_recycle_cadence("кіт", "a1", 8)

    assert len(violations) == 1
    assert violations[0]["type"] == "recycle_cadence"
    assert violations[0]["observed"] == 1
    assert violations[0]["required"] == 3
