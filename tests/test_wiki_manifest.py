from __future__ import annotations

from pathlib import Path

from scripts.build.phases.wiki_manifest import extract_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_my_morning_manifest_extracts_required_obligations() -> None:
    manifest = extract_manifest(ROOT / "wiki/pedagogy/a1/my-morning.md")

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

