from pathlib import Path

from scripts.validate.validate_vocab_yaml import validate_file


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_validate_vocab_yaml_accepts_bare_word_list(tmp_path: Path) -> None:
    vocab_path = _write(
        tmp_path / "vocabulary.yaml",
        """
- word: відмінок
  translation: case
  pos: noun
  example: "Називний - це відмінок."
- word: називний
  translation: nominative
  pos: adjective
  example: "Студент - це називний відмінок."
""",
    )

    assert validate_file(vocab_path) is True


def test_validate_vocab_yaml_accepts_enriched_items_schema(tmp_path: Path) -> None:
    vocab_path = _write(
        tmp_path / "vocabulary.yaml",
        """
items:
  - lemma: відмінок
    ipa: "/ʋidˈminok/"
    translation: case
    pos: noun
    gender: m
""",
    )

    assert validate_file(vocab_path) is True


def test_validate_vocab_yaml_requires_enriched_lemma(tmp_path: Path) -> None:
    vocab_path = _write(
        tmp_path / "vocabulary.yaml",
        """
items:
  - lemma: ""
    word: відмінок
    ipa: "/ʋidˈminok/"
    translation: case
    pos: noun
    gender: m
""",
    )

    assert validate_file(vocab_path) is False


def test_validate_vocab_yaml_rejects_unknown_top_level_schema(tmp_path: Path) -> None:
    vocab_path = _write(
        tmp_path / "vocabulary.yaml",
        """
terms:
  - word: відмінок
    translation: case
""",
    )

    assert validate_file(vocab_path) is False
