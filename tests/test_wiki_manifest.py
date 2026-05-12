from __future__ import annotations

from pathlib import Path

from scripts.build.phases.wiki_manifest import (
    WIKI_MANIFEST_SCHEMA,
    _normalize_external_role,
    extract_manifest,
)

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
