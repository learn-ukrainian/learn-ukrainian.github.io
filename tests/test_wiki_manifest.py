from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build.phases.wiki_manifest import (
    WIKI_MANIFEST_SCHEMA,
    _normalize_external_role,
    _repository_relative_wiki_path,
    extract_manifest,
)
from wiki import config as wiki_config

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parents[1]


def test_normalize_external_role_rejects_substring_only_youtube_match() -> None:
    """py/incomplete-url-substring-sanitization regression: use host check, not substring."""
    # Real YouTube hosts → "youtube"
    assert _normalize_external_role(None, url="https://www.youtube.com/watch?v=x") == "youtube"
    assert _normalize_external_role(None, url="https://youtube.com/watch?v=x") == "youtube"
    assert _normalize_external_role(None, url="https://youtu.be/abc") == "youtube"
    # Attack patterns where "youtube.com" appears in path or query → must NOT match
    assert _normalize_external_role(None, url="https://evil.com/youtube.com/watch") != "youtube"
    assert _normalize_external_role(None, url="https://evil.com?host=youtube.com") != "youtube"
    assert _normalize_external_role(None, url="https://youtube.com.evil.com/") != "youtube"
    # Malformed URLs must not crash; fall through to article since URL is non-empty
    assert _normalize_external_role(None, url="not a url") == "article"


def test_my_morning_manifest_extracts_required_obligations() -> None:
    manifest = extract_manifest(ROOT / "wiki/pedagogy/a1/my-morning.md")

    assert manifest["external_resources"] == []
    assert len(manifest["wiki_vocabulary_minimum"]) == 21
    assert manifest["wiki_vocabulary_minimum"][0] == {
        "lemma": "прокидатися",
        "frequency_tier": "high",
        "gloss": "базова ранкова дія, з якої починається день",
    }
    assert len(manifest["l2_errors"]) == 6
    assert len(manifest["sequence_steps"]) == 5
    incorrect = [item["incorrect"] for item in manifest["l2_errors"]]
    assert "Я прокидаєшся. / Він прокидаюся." in incorrect
    assert "Вимова: [прокидайешся]" in incorrect
    assert "Вимова: [одягайет'с'а]" in incorrect
    assert "Я мию себе." in incorrect
    assert "Я дивюся. / Я дивюсь." in incorrect
    assert "Я користуювася." in incorrect
    assert any(item["written"] == "-шся" and item["spoken"] == "[с':а]" for item in manifest["phonetic_rules"])
    assert any(item["written"] == "-ться" and item["spoken"] == "[ц':а]" for item in manifest["phonetic_rules"])


def test_manifest_extracts_vocabulary_minimum_tiers_and_glosses(tmp_path: Path) -> None:
    wiki = tmp_path / "vocab.md"
    wiki.write_text(
        """# Vocabulary fixture

## Словниковий мінімум

- ранок (★★★) — morning [S1].
- обід (★★) — lunch.
- вечір (★) — evening.
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert manifest["wiki_vocabulary_minimum"] == [
        {"lemma": "ранок", "frequency_tier": "high", "gloss": "morning"},
        {"lemma": "обід", "frequency_tier": "mid", "gloss": "lunch"},
        {"lemma": "вечір", "frequency_tier": "low", "gloss": "evening"},
    ]


def test_manifest_missing_vocabulary_minimum_returns_empty_list(tmp_path: Path) -> None:
    wiki = tmp_path / "no-vocab.md"
    wiki.write_text(
        """# No vocabulary fixture

## Методичний підхід

Є методика.
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert manifest["wiki_vocabulary_minimum"] == []


def test_manifest_handles_mixed_or_missing_vocabulary_stars(tmp_path: Path) -> None:
    wiki = tmp_path / "mixed-stars.md"
    wiki.write_text(
        """# Mixed stars fixture

## Словниковий мінімум

- кава (★★☆) — coffee.
- чай () — tea.
- сік — juice.
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert manifest["wiki_vocabulary_minimum"] == [
        {"lemma": "кава", "frequency_tier": "mid", "gloss": "coffee"},
        {"lemma": "чай", "frequency_tier": "unknown", "gloss": "tea"},
        {"lemma": "сік", "frequency_tier": "unknown", "gloss": "juice"},
    ]


def test_manifest_handles_a1_heading_variants() -> None:
    pages = [
        "around-the-city",
        "at-the-cafe",
        "checkpoint-actions",
        "checkpoint-first-contact",
    ]
    counts = {}
    for slug in pages:
        manifest = extract_manifest(ROOT / f"wiki/pedagogy/a1/{slug}.md")
        counts[slug] = (len(manifest["l2_errors"]), len(manifest["sequence_steps"]))

    assert counts == {
        "around-the-city": (6, 5),
        "at-the-cafe": (6, 4),
        "checkpoint-actions": (6, 6),
        "checkpoint-first-contact": (7, 6),
    }


def test_manifest_accepts_sequence_heading_variants(tmp_path: Path) -> None:
    wiki = tmp_path / "variant.md"
    wiki.write_text(
        """# Variant

## Послідовність викладання

Крок 1: Перша дія.
Треба показати форму.

## Типові помилки L2

| ❌ Помилково | ✅ Правильно | Чому |
|---|---|---|
| Я є студент. | Я студент. | Калька з English is. |
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert manifest["sequence_steps"][0]["heading"] == "Крок 1: Перша дія."
    assert manifest["l2_errors"][0]["incorrect"] == "Я є студент."


def test_manifest_strips_html_verify_comments_from_l2_error_cells(tmp_path: Path) -> None:
    wiki = tmp_path / "verify-comments.md"
    wiki.write_text(
        """# Verify comments

## Типові помилки L2

| ❌ Помилково | ✅ Правильно | Чому |
|---|---|---|
| Я є студент <!-- VERIFY: hidden reviewer note -->. | Я студент. | Калька. |
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert manifest["l2_errors"][0]["incorrect"] == "Я є студент."


def test_manifest_extracts_external_resources_section(tmp_path: Path) -> None:
    wiki = tmp_path / "external.md"
    wiki.write_text(
        """# External resources fixture

slug: external-fixture

## Зовнішні ресурси

| Роль | Назва | URL | Автор | Опис |
|---|---|---|---|---|
| youtube | [Ukrainian morning routine](https://youtu.be/abc12345678) | | Speak Ukrainian | Short listening clip. |
| blog | Morning vocabulary | https://example.com/morning | Ukrainian Lessons | Blog explainer. |
| textbook | Караман Grade 10, p.176 | | Караман | Зворотні дієслова. |

## Послідовність викладання

Крок 1: Перша дія.
Треба показати форму.
""",
        encoding="utf-8",
    )

    manifest = extract_manifest(wiki)

    assert "external_resources" in WIKI_MANIFEST_SCHEMA["required"]
    assert manifest["external_resources"] == [
        {
            "role": "youtube",
            "title": "Ukrainian morning routine",
            "url": "https://youtu.be/abc12345678",
            "author": "Speak Ukrainian",
            "description": "Short listening clip.",
        },
        {
            "role": "blog",
            "title": "Morning vocabulary",
            "url": "https://example.com/morning",
            "author": "Ukrainian Lessons",
            "description": "Blog explainer.",
        },
        {
            "role": "textbook",
            "title": "Караман Grade 10, p.176",
            "url": None,
            "author": "Караман",
            "description": "Зворотні дієслова.",
        },
    ]


def test_repository_relative_wiki_path_prefers_staged_wiki_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staged wiki root wins over the checkout root. A normal read stays put.

    ``PROJECT_ROOT`` is left unchanged. A stage directory inside the checkout
    is still under that root; the stored path must not keep the stage prefix.
    """
    project_root = Path(wiki_config.PROJECT_ROOT).resolve()
    today = "wiki/pedagogy/a1/sounds-letters-and-hello.md"
    article_suffix = Path("pedagogy/a1/sounds-letters-and-hello.md")

    assert _repository_relative_wiki_path(project_root / today) == today
    checkout_script = project_root / "scripts/build/phases/wiki_manifest.py"
    assert _repository_relative_wiki_path(checkout_script) == "scripts/build/phases/wiki_manifest.py"

    outside_wiki = tmp_path / "outside-9335" / "wiki"
    outside_resolved = outside_wiki.resolve()
    assert project_root != outside_resolved and project_root not in outside_resolved.parents
    monkeypatch.setattr(wiki_config, "WIKI_DIR", outside_wiki)
    assert _repository_relative_wiki_path(outside_wiki / article_suffix) == today

    shallow_wiki = project_root / "tmp" / "impl-9335-r4-path-shallow" / "wiki"
    deep_wiki = project_root / "tmp" / "impl-9335-r4-path-deep" / "nested" / "stage" / "wiki"
    assert len(shallow_wiki.relative_to(project_root).parts) < len(deep_wiki.relative_to(project_root).parts)
    for wiki_root in (shallow_wiki, deep_wiki):
        assert project_root in wiki_root.resolve().parents
        monkeypatch.setattr(wiki_config, "WIKI_DIR", wiki_root)
        assert _repository_relative_wiki_path(wiki_root / article_suffix) == today
