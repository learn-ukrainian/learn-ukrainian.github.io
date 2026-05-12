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
