from __future__ import annotations

from scripts.audit.content_surface_gates import scan_module_surface, scan_surface_text


def test_a1_english_scaffolding_is_allowed() -> None:
    text = """
Read the dialogue and notice the verb.

**Я чекаю на автобус.** — I am waiting for the bus.
"""
    report = scan_surface_text(text, level="a1")

    assert report["passed"] is True
    assert report["counts"]["critical"] == 0


def test_a2_english_led_prose_warns_without_failing() -> None:
    text = """
This paragraph explains the whole grammar point in English before any Ukrainian anchor appears.

**Я чекаю на автобус.**
"""
    report = scan_surface_text(text, level="a2")

    assert report["passed"] is True
    assert report["verdict"] == "WARN"
    assert any(finding["type"] == "english_led_line" for finding in report["findings"])


def test_b1_plus_english_led_prose_fails() -> None:
    text = """
This paragraph explains the whole grammar point in English before any Ukrainian anchor appears.

**Я чекаю на автобус.**
"""
    report = scan_surface_text(text, level="b1")

    assert report["passed"] is False
    assert report["verdict"] == "FAIL"
    assert any(
        finding["type"] == "english_led_line" and finding["severity"] == "critical"
        for finding in report["findings"]
    )


def test_ai_and_path_leaks_are_blocking_even_at_a1() -> None:
    text = """
As an AI, I cannot assist with this request.

<activity_split_audit>level=B1 inline_n=1 workbook_n=2</activity_split_audit>

Read /Users/person/project/curriculum/l2-uk-en/a1/foo/module.md.
"""
    report = scan_surface_text(text, level="a1")

    assert report["passed"] is False
    assert {finding["type"] for finding in report["findings"]} >= {"ai_leakage", "path_leakage"}


def test_html_verify_comments_do_not_count_as_path_leaks() -> None:
    text = """
<!-- VERIFY: source="curriculum/l2-uk-en/plans/a1/foo.yaml" -->

**Я чекаю на автобус.**
"""
    report = scan_surface_text(text, level="b1")

    assert report["passed"] is True
    assert report["findings"] == []


def test_calqued_warning_metaphrase_fails_deterministically() -> None:
    text = """
У **застереженні** зміст інший: будь обережний, щоб небажаний результат не стався.

Будь обережний на сходах.
"""
    report = scan_surface_text(text, level="b1")

    assert report["passed"] is False
    assert report["verdict"] == "FAIL"
    assert any(
        finding["type"] == "ukrainian_grammar_calque"
        and finding["text"] == "будь обережний, щоб небажаний результат не став"
        for finding in report["findings"]
    )
    assert len(
        [finding for finding in report["findings"] if finding["type"] == "ukrainian_grammar_calque"]
    ) == 1


def test_sidecar_scan_catches_ai_leak_without_english_ratio_false_positive(tmp_path) -> None:
    module_dir = tmp_path / "b1" / "sidecar"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Урок\n\n**Я чекаю на автобус.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: quiz\n"
        "  prompt: This YAML activity prompt is intentionally English but allowed as data.\n"
        "  note: As an AI, I cannot assist with this request.\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    report = scan_module_surface(module_dir, level="b1")

    assert report["passed"] is False
    assert any(
        finding["type"] == "ai_leakage" and finding["source"] == "activities.yaml"
        for finding in report["findings"]
    )
    assert not any(
        finding["type"] == "english_led_line" and finding["source"] == "activities.yaml"
        for finding in report["findings"]
    )


def test_yaml_activity_correction_keys_are_not_ai_leaks(tmp_path) -> None:
    module_dir = tmp_path / "b1" / "sidecar"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Урок\n\n**Не відкривайте файл.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: error-correction\n"
        "  prompt: Виправте речення.\n"
        "  items:\n"
        "    - incorrect: Не відкрийте файл.\n"
        "      correction: Не відкривайте файл.\n"
        "      explanation: Це заборона контрольованої дії.\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    report = scan_module_surface(module_dir, level="b1")

    assert report["passed"] is True
    assert not any(
        finding["type"] == "ai_leakage" and finding["source"] == "activities.yaml"
        for finding in report["findings"]
    )


def test_yaml_activity_correction_label_in_value_still_fails(tmp_path) -> None:
    module_dir = tmp_path / "b1" / "sidecar"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Урок\n\n**Не відкривайте файл.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: quiz\n"
        "  prompt: 'Correction: rewrite the learner-facing line before publishing.'\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")

    report = scan_module_surface(module_dir, level="b1")

    assert report["passed"] is False
    assert any(
        finding["type"] == "ai_leakage" and finding["source"] == "activities.yaml"
        for finding in report["findings"]
    )


def test_markdown_correction_label_still_fails() -> None:
    text = """
Correction: rewrite this draft before publishing.

**Не відкривайте файл.**
"""
    report = scan_surface_text(text, level="b1", source="module.md")

    assert report["passed"] is False
    assert any(finding["type"] == "ai_leakage" for finding in report["findings"])
