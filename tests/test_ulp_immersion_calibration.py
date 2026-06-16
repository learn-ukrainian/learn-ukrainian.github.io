import pytest

from scripts import config


@pytest.mark.parametrize(
    ("track", "vocab_count", "expected_key"),
    [
        ("a1", 0, "a1-m01-03"),
        ("a1", 139, "a1-m01-03"),
        ("a1", 140, "a1-m04-06"),
        ("a1", 242, "a1-m07-14"),
        ("a1", 573, "a1-m15-24"),
        ("a1", 593, "a1-m25-34"),
        ("a1", 621, "a1-m35-54"),
        ("a1", 647, "a1-m55+"),
    ],
)
def test_ulp_calibrated_knees_select_expected_band(monkeypatch, track, vocab_count, expected_key):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    band = config.compute_immersion_band(
        track,
        99,
        learner_state={"cumulative_vocabulary": vocab_count, "known_grammar": []},
    )

    assert band["key"] == expected_key


@pytest.mark.parametrize(
    ("module_num", "expected_key", "expected_range"),
    [
        (1, "a2-bridge", (75, 100)),
        (4, "a2-ramp", (85, 100)),
        (8, "a2-m01-20", (85, 100)),
        (21, "a2-m21-50", (90, 100)),
        (51, "a2-m51-70", (95, 100)),
    ],
)
def test_a2_uses_module_bands_not_old_vocab_knees(
    monkeypatch,
    module_num,
    expected_key,
    expected_range,
):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    for vocab_count in (0, 9999):
        band = config.compute_immersion_band(
            "a2",
            module_num,
            learner_state={"cumulative_vocabulary": vocab_count, "known_grammar": []},
        )
        assert band["key"] == expected_key
        assert (band["advisory_pct_min"], band["advisory_pct_max"]) == expected_range


def test_ulp_derivation_falls_back_to_static_policy_without_learner_state(monkeypatch):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    band = config.compute_immersion_band("a1", 20)

    assert band["key"] == "a1-m15-24"
    assert (band["advisory_pct_min"], band["advisory_pct_max"]) == (40, 55)


def test_a2_derivation_keeps_easy_ukrainian_ranges(monkeypatch):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    ramp = config.compute_immersion_band(
        "a2",
        4,
        learner_state={"cumulative_vocabulary": 1153, "known_grammar": []},
    )
    late = config.compute_immersion_band(
        "a2",
        51,
        learner_state={"cumulative_vocabulary": 4470, "known_grammar": []},
    )

    assert ramp["key"] == "a2-ramp"
    assert (ramp["advisory_pct_min"], ramp["advisory_pct_max"]) == (85, 100)
    assert "Do not add English support paragraphs" in ramp["rule"]
    assert late["key"] == "a2-m51-70"
    assert (late["advisory_pct_min"], late["advisory_pct_max"]) == (95, 100)


@pytest.mark.parametrize(
    ("module_num", "vocab_count"),
    [
        (1, 0),
        (2, 44),
        (3, 84),
    ],
)
def test_a1_m01_m03_backward_compat_with_static_advisory_band(
    monkeypatch,
    module_num,
    vocab_count,
):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", False)
    before = config.compute_immersion_band("a1", module_num)

    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)
    after = config.compute_immersion_band(
        "a1",
        module_num,
        learner_state={"cumulative_vocabulary": vocab_count, "known_grammar": []},
    )

    assert after["key"] == before["key"]
    assert abs(after["advisory_pct_min"] - before["advisory_pct_min"]) <= 2
    assert abs(after["advisory_pct_max"] - before["advisory_pct_max"]) <= 2


def test_recycle_cadence_defaults_are_ulp_calibrated():
    assert config.get_recycle_cadence_policy("a1") == {
        "recycle_window": 6,
        "recycle_floor": 3,
    }
    assert config.get_recycle_cadence_policy("a2") == {
        "recycle_window": 8,
        "recycle_floor": 6,
    }
    assert config.get_recycle_cadence_policy("b1") == {
        "recycle_window": 21,
        "recycle_floor": 12,
    }
