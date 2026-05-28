"""Tests for learner-state audit checks."""

import yaml

from scripts.audit.checks import learner_state as learner_state_checks
from scripts.pipeline import learner_state

UKRAINIAN_ALPHABET = "абвгдеєжзиіїйклмнопрстуфхцчшщьюя"


def _write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _unknown_words(count):
    words = []
    for index in range(count):
        first = UKRAINIAN_ALPHABET[index % len(UKRAINIAN_ALPHABET)]
        second = UKRAINIAN_ALPHABET[(index // len(UKRAINIAN_ALPHABET)) % len(UKRAINIAN_ALPHABET)]
        words.append(f"невідоме{first}{second}")
    return words


def _setup_curriculum(root, level):
    _write_yaml(root / "curriculum.yaml", {
        "levels": {
            level: {
                "modules": ["module-a", "module-b", "module-c", "module-d", "module-e"],
            },
        },
    })
    for slug in ["module-a", "module-b", "module-c", "module-d", "module-e"]:
        _write_yaml(root / level / slug / "vocabulary.yaml", {"items": []})


def _empty_learner_state(*_args):
    return {
        "cumulative_vocabulary": [],
        "known_grammar": [],
        "module_count": 0,
        "previous_theme": None,
        "next_topic": [],
    }


def _fake_verify_words(words):
    lookup = {
        "ранку": {"lemma": "ранок", "pos": "noun", "tags": ""},
        "понадкрай": {"lemma": "понадкрай", "pos": "prep", "tags": ""},
    }
    return {
        word: [lookup[word]] if word in lookup else []
        for word in words
    }


def _assert_allowed(content, monkeypatch, **kwargs):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)
    assert learner_state_checks.check_unknown_vocabulary(
        content,
        "a1",
        20,
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
        **kwargs,
    ) == []


def test_layered_allowlist_accepts_wiki_vocabulary_minimum(monkeypatch):
    _assert_allowed(
        "ранок",
        monkeypatch,
        wiki_manifest={"wiki_vocabulary_minimum": [{"lemma": "ранок"}]},
    )


def test_layered_allowlist_accepts_plan_new_vocabulary(monkeypatch):
    _assert_allowed(
        "кава",
        monkeypatch,
        plan={"targets": {"new_vocabulary": ["кава"]}},
    )


def test_layered_allowlist_accepts_plan_vocabulary_hints(monkeypatch):
    _assert_allowed(
        "чай",
        monkeypatch,
        plan={"vocabulary_hints": {"required": ["чай (tea)"]}},
    )


def test_layered_allowlist_accepts_cumulative_learner_state(monkeypatch):
    monkeypatch.setattr(
        learner_state_checks,
        "build_learner_state",
        lambda *_args: {
            "cumulative_vocabulary": ["вчора"],
            "known_grammar": [],
            "module_count": 1,
            "previous_theme": None,
            "next_topic": [],
        },
    )

    assert learner_state_checks.check_unknown_vocabulary(
        "вчора",
        "a1",
        20,
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    ) == []


def test_layered_allowlist_accepts_closed_class_function_words(monkeypatch):
    _assert_allowed("і", monkeypatch)


def test_layered_allowlist_accepts_proper_nouns_from_wiki_examples(monkeypatch):
    _assert_allowed("Леся", monkeypatch, wiki_text="Приклад: Леся Українка пише.")


def test_layered_allowlist_accepts_bad_form_markers(monkeypatch):
    _assert_allowed(
        "завтрак",
        monkeypatch,
        wiki_text="Маркер: <!-- bad -->завтрак<!-- /bad -->.",
    )


def test_layered_allowlist_accepts_quoted_evidence_from_cited_chunks(monkeypatch):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)
    content = "> Тут є цитата [S1]\n\nцитата"
    assert learner_state_checks.check_unknown_vocabulary(
        content,
        "a1",
        20,
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    ) == []


def test_combined_allowlist_rejects_lemma_in_no_source(monkeypatch):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)

    violations = learner_state_checks.check_unknown_vocabulary(
        "ранок невідоме",
        "a1",
        20,
        wiki_manifest={"wiki_vocabulary_minimum": [{"lemma": "ранок"}]},
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    )

    assert [violation["lemma"] for violation in violations] == ["невідоме"]


def test_unknown_vocabulary_band_tolerance(monkeypatch):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)

    assert learner_state_checks.check_unknown_vocabulary(
        "одина дваа",
        "a1",
        20,
        max_unsupported=2,
        verify_words_fn=_fake_verify_words,
    ) == []
    violations = learner_state_checks.check_unknown_vocabulary(
        "одина дваа триа чотира",
        "a1",
        20,
        max_unsupported=2,
        verify_words_fn=_fake_verify_words,
    )
    assert [violation["lemma"] for violation in violations] == ["дваа", "одина", "триа", "чотира"]


def test_function_word_miss_counts_toward_band_without_individual_fail(monkeypatch):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)

    violations = learner_state_checks.check_unknown_vocabulary(
        "понадкрай",
        "a1",
        20,
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    )

    assert violations[0]["type"] == "unknown_vocabulary_band"
    assert violations[0]["lemma"] is None
    assert violations[0]["unsupported_count"] == 1


def test_vesum_normalization_allows_inflected_form_when_lemma_is_allowed(monkeypatch):
    monkeypatch.setattr(learner_state_checks, "build_learner_state", _empty_learner_state)

    assert learner_state_checks.check_unknown_vocabulary(
        "ранку",
        "a1",
        20,
        plan={"targets": {"new_vocabulary": ["ранок"]}},
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    ) == []
    violations = learner_state_checks.check_unknown_vocabulary(
        "ранку",
        "a1",
        20,
        max_unsupported=0,
        verify_words_fn=_fake_verify_words,
    )
    assert violations[0]["lemma"] == "ранок"


def test_unknown_vocabulary_returns_violation_lemma(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _setup_curriculum(root, "a1")
    module_dir = root / "a1" / "module-b"
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    words = _unknown_words(11)
    violations = learner_state_checks.check_unknown_vocabulary(
        " ".join(words),
        "a1",
        2,
        module_dir,
    )

    assert violations
    assert violations[0]["lemma"] == words[0]


def test_unknown_vocabulary_severity_warn_at_sequence_2_and_hard_at_sequence_5(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _setup_curriculum(root, "a1")
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)
    content = " ".join(_unknown_words(40))

    warn_violations = learner_state_checks.check_unknown_vocabulary(
        content,
        "a1",
        2,
        root / "a1" / "module-b",
    )
    hard_violations = learner_state_checks.check_unknown_vocabulary(
        content,
        "a1",
        5,
        root / "a1" / "module-e",
    )

    assert {violation["severity"] for violation in warn_violations} == {"WARN"}
    assert {violation["severity"] for violation in hard_violations} == {"HARD"}


def test_known_grammar_re_explanation_detects_matching_section_header(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "curriculum.yaml", {
        "levels": {"a1": {"modules": ["module-a", "module-b"]}},
    })
    _write_yaml(root / "plans" / "a1" / "module-a.yaml", {
        "grammar": ["це + noun"],
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)

    violations = learner_state_checks.check_known_grammar_re_explanation(
        "## Це + noun\n\nAlready taught.",
        "a1",
        2,
    )

    assert violations
    assert violations[0]["topic"] == "це + noun"


def test_known_grammar_re_explanation_severity_warn_a1_hard_b1(tmp_path, monkeypatch):
    root = tmp_path / "curriculum" / "l2-uk-en"
    _write_yaml(root / "curriculum.yaml", {
        "levels": {
            "a1": {"modules": ["module-a", "module-b"]},
            "b1": {"modules": ["module-a", "module-b"]},
        },
    })
    _write_yaml(root / "plans" / "a1" / "module-a.yaml", {
        "grammar": ["це + noun"],
    })
    _write_yaml(root / "plans" / "b1" / "module-a.yaml", {
        "grammar": ["це + noun"],
    })
    monkeypatch.setattr(learner_state, "CURRICULUM_ROOT", root)
    content = "### Це + noun\n\nAlready taught."

    warn_violations = learner_state_checks.check_known_grammar_re_explanation(content, "a1", 2)
    hard_violations = learner_state_checks.check_known_grammar_re_explanation(content, "b1", 2)

    assert warn_violations[0]["severity"] == "WARN"
    assert hard_violations[0]["severity"] == "HARD"
