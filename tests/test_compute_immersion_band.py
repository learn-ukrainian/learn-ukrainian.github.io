from scripts import config


def test_compute_immersion_band_flag_off_matches_static_policy(monkeypatch):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", False)

    computed = config.compute_immersion_band("a1", 5)
    static = config.get_immersion_policy("a1", 5)

    assert computed == static
    assert computed["key"] == "a1-m04-06"


def test_compute_immersion_band_flag_on_uses_cumulative_vocab_not_module_num(monkeypatch):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", True)

    low_vocab = config.compute_immersion_band(
        "a1",
        40,
        learner_state={"cumulative_vocabulary": ["так"] * 10, "known_grammar": []},
    )
    high_vocab = config.compute_immersion_band(
        "a1",
        1,
        learner_state={"cumulative_vocabulary": ["так"] * 400, "known_grammar": []},
    )

    assert low_vocab["key"] == "a1-m01-03"
    assert high_vocab["key"] == "a1-m35-54"
    assert low_vocab["advisory_pct_min"] != high_vocab["advisory_pct_min"]


def test_immersion_accessors_preserve_backward_compat_when_flag_off(monkeypatch):
    monkeypatch.setattr(config, "USE_ULP_IMMERSION_DERIVATION", False)

    policy = config.get_immersion_policy("a1", 15)
    assert policy["key"] == "a1-m15-24"
    assert config.get_immersion_range("a1", 15) == (
        policy["advisory_pct_min"],
        policy["advisory_pct_max"],
    )
    structural = config.get_immersion_structural("a1", 15)
    assert structural["min_uk_dialogue_lines"] == policy["min_uk_dialogue_lines"]
    assert config.get_immersion_rule("a1", 15) == policy["rule"]
