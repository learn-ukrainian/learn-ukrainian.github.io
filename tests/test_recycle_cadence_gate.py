from scripts.audit.checks import recycle_cadence

STALE_MAP = {
    "кіт": [(1, 1), (2, 0), (3, 0)],
    "мама": [(2, 1)],
}


def test_recycle_cadence_warns_when_stale_lemmas_are_missing(monkeypatch):
    monkeypatch.setattr(recycle_cadence, "build_lemma_frequency_map", lambda _track, _module: STALE_MAP)
    monkeypatch.setattr(recycle_cadence, "_extract_all_ukrainian_surfaces", lambda _content: ["нове"])

    violations = recycle_cadence.check_recycle_cadence("нове", "A1", 8)

    assert len(violations) == 1
    assert violations[0]["type"] == "recycle_cadence"
    assert violations[0]["severity"] == "WARN"
    assert violations[0]["blocking"] is False


def test_recycle_cadence_passes_with_sufficient_recycle(monkeypatch):
    monkeypatch.setattr(recycle_cadence, "build_lemma_frequency_map", lambda _track, _module: STALE_MAP)
    monkeypatch.setattr(
        recycle_cadence,
        "_extract_all_ukrainian_surfaces",
        lambda _content: ["кіт", "кіт", "кіт", "нове"],
    )

    violations = recycle_cadence.check_recycle_cadence("кіт кіт кіт нове", "A1", 8)

    assert violations == []


def test_recycle_cadence_a1_severity_is_warn(monkeypatch):
    monkeypatch.setattr(recycle_cadence, "build_lemma_frequency_map", lambda _track, _module: STALE_MAP)
    monkeypatch.setattr(recycle_cadence, "_extract_all_ukrainian_surfaces", lambda _content: [])

    violations = recycle_cadence.check_recycle_cadence("", "a1", 8)

    assert violations[0]["severity"] == "WARN"
