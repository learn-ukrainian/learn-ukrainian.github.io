"""Tests for V6 quick verify — fast structural checks after WRITE."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build.quick_verify import (
    QuickVerifyError,
    build_correction_directive,
    format_results,
    has_errors,
    quick_verify,
)


def _make_plan(
    sections=None,
    word_target=1200,
    required_vocab=None,
):
    """Create a minimal plan dict for testing."""
    if sections is None:
        sections = [
            {"section": "Звуки і літери (Sounds and Letters)", "words": 300},
            {"section": "Перші слова (First Words)", "words": 300},
        ]
    plan = {
        "word_target": word_target,
        "content_outline": sections,
        "vocabulary_hints": {
            "required": required_vocab or [],
        },
    }
    return plan


def _make_content(word_count=1200, sections=None, extra=""):
    """Generate test content with given word count and sections."""
    if sections is None:
        sections = ["Звуки і літери", "Перші слова"]

    lines = []
    for s in sections:
        lines.append(f"## {s}")
        lines.append("")

    # Add filler Ukrainian words to reach target
    filler = "Українська мова дуже гарна і мелодійна. " * (word_count // 6)
    lines.append(filler)
    lines.append(extra)
    return "\n".join(lines)


# --- Structure checks ---


def test_structure_pass():
    plan = _make_plan()
    content = _make_content()
    results = quick_verify(content, plan)
    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 0


def test_structure_missing_section():
    plan = _make_plan()
    # Content only has first section
    content = "## Звуки і літери\n\nContent here. " * 200
    results = quick_verify(content, plan)
    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 1
    assert "Перші слова" in structure_errors[0].message


# --- Word count checks ---


def test_word_count_pass():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=1200)
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 0


def test_word_count_too_short():
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=300)  # Way under
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 1
    assert wc_errors[0].severity == "ERROR"
    assert "Too short" in wc_errors[0].message


def test_word_count_over_target_is_ok():
    """Word targets are MINIMUMS — exceeding them is always acceptable."""
    plan = _make_plan(word_target=1200)
    content = _make_content(word_count=2400)  # 2x target — fine
    results = quick_verify(content, plan)
    wc_errors = [r for r in results if r.check == "WORD_COUNT"]
    assert len(wc_errors) == 0  # No ceiling — more content is always OK


# --- Toxic token checks ---


def test_toxic_russian_chars():
    plan = _make_plan()
    content = _make_content(extra="Ты знаешь русский? ы э ё")
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert any("Russian characters" in r.message for r in toxic_errors)


def test_toxic_severe_russianisms():
    plan = _make_plan()
    content = _make_content(extra="пожалуйста скажите хорошо")
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert any("Severe Russianisms" in r.message for r in toxic_errors)


def test_toxic_clean():
    plan = _make_plan()
    content = _make_content()  # No Russian
    results = quick_verify(content, plan)
    toxic_errors = [r for r in results if r.check == "TOXIC"]
    assert len(toxic_errors) == 0


# --- Vocabulary checks ---


def test_vocabulary_present():
    plan = _make_plan(required_vocab=["мова", "гарна"])
    content = _make_content(extra="Українська мова дуже гарна.")
    results = quick_verify(content, plan)
    vocab_errors = [r for r in results if r.check == "VOCABULARY"]
    assert len(vocab_errors) == 0


def test_vocabulary_missing():
    plan = _make_plan(required_vocab=[
        "стіл (table, m)",
        "книга (book, f)",
        "вікно (window, n)",
        "кімната (room, f)",
    ])
    content = _make_content(extra="Тут є стіл і книга.")  # Missing вікно, кімната
    results = quick_verify(content, plan)
    vocab_errors = [r for r in results if r.check == "VOCABULARY"]
    assert len(vocab_errors) == 1
    assert "2/4" in vocab_errors[0].message


# --- Integration ---


def test_has_errors_true():
    errors = [QuickVerifyError("TEST", "ERROR", "fail")]
    assert has_errors(errors) is True


def test_has_errors_false_warnings_only():
    errors = [QuickVerifyError("TEST", "WARNING", "warn")]
    assert has_errors(errors) is False


def test_has_errors_empty():
    assert has_errors([]) is False


def test_format_results_pass():
    result = format_results([])
    assert "PASSED" in result


def test_format_results_fail():
    errors = [QuickVerifyError("TEST", "ERROR", "something broke")]
    result = format_results(errors)
    assert "FAILED" in result
    assert "something broke" in result


def test_correction_directive():
    errors = [
        QuickVerifyError("WORD_COUNT", "ERROR", "Too short: 500 words"),
        QuickVerifyError("TOXIC", "WARNING", "Latin chars found"),
    ]
    directive = build_correction_directive(errors)
    assert "<correction_directive>" in directive
    assert "Too short: 500 words" in directive
    assert "Latin chars found" in directive
    assert "Fix ONLY the listed errors" in directive


def test_correction_directive_empty():
    assert build_correction_directive([]) == ""


# --- Exercise item count checks ---


def _make_plan_with_activities(activity_hints=None, **kwargs):
    """Create a plan dict with activity_hints."""
    plan = _make_plan(**kwargs)
    if activity_hints is not None:
        plan["activity_hints"] = activity_hints
    return plan


def test_exercises_no_hints():
    """No activity_hints in plan => no exercise errors."""
    plan = _make_plan()
    content = _make_content()
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_placeholders_match():
    """Placeholders match activity_hints count => pass."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
    ])
    content = _make_content(extra=(
        "\n:::exercise-placeholder\ntype: quiz\ntitle: Test 1\n:::\n"
        "\n:::exercise-placeholder\ntype: fill-in\ntitle: Test 2\n:::\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_zero_placeholders():
    """Plan has hints but content has no placeholders => warning."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
    ])
    content = _make_content()
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 1
    assert ex_errors[0].severity == "WARNING"
    assert "0 placeholders" in ex_errors[0].message


def test_exercises_fewer_than_expected():
    """Content has fewer exercises than plan expects => warning."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
        {"type": "match-up", "title": "Test 3"},
    ])
    content = _make_content(extra=(
        "\n:::exercise-placeholder\ntype: quiz\ntitle: Test 1\n:::\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 1
    assert "3 exercise(s) but content has 1" in ex_errors[0].message


def test_exercises_filled_count():
    """Filled exercises (:::quiz etc.) count toward the total."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
    ])
    content = _make_content(extra=(
        "\n:::quiz\nsome quiz content\n:::\n"
        "\n:::fill-in\nsome fill content\n:::\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_mixed_placeholder_and_filled():
    """Mix of placeholders and filled exercises counts correctly."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
    ])
    content = _make_content(extra=(
        "\n:::exercise-placeholder\ntype: quiz\ntitle: Test 1\n:::\n"
        "\n:::fill-in\nsome fill content\n:::\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_more_than_expected():
    """More exercises than expected => no error (overshoot is fine)."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
    ])
    content = _make_content(extra=(
        "\n:::exercise-placeholder\ntype: quiz\ntitle: Test 1\n:::\n"
        "\n:::exercise-placeholder\ntype: fill-in\ntitle: Bonus\n:::\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


# --- INJECT_ACTIVITY marker counting (#1054) ---


def test_exercises_inject_markers_count():
    """INJECT_ACTIVITY markers count as exercises (#1054)."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
    ])
    content = _make_content(extra=(
        "\n<!-- INJECT_ACTIVITY: quiz-sounds -->\n"
        "\n<!-- INJECT_ACTIVITY: fill-in-letters -->\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_inject_markers_zero_no_false_warning():
    """Plan with hints + INJECT markers should NOT warn about 0 placeholders (#1054)."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
    ])
    content = _make_content(extra="\n<!-- INJECT_ACTIVITY: quiz-test -->\n")
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_unnormalized_markers_count():
    """Unnormalized `type, description` form markers count too (#1189).

    Regression test for the false EXERCISE failures on participles-passive
    (1/6 reported), participle-phrases (2/6 reported), b1-baseline-past-present
    (5/6 reported), and daily-life-and-routines (4/5 reported). The strict
    regex `[a-z0-9][a-z0-9-]*` only matched normalized kebab-case IDs and
    rejected the loose `type, description` form that the writer commonly
    emits before the marker normalizer runs. Codex root-cause analysis in
    issue #1189 task `b1-participles-exercises`.
    """
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "reading", "title": "T1"},
        {"type": "essay-response", "title": "T2"},
        {"type": "fill-in", "title": "T3"},
        {"type": "error-correction", "title": "T4"},
        {"type": "quiz", "title": "T5"},
        {"type": "match-up", "title": "T6"},
    ])
    # All 6 markers in unnormalized "type, description" form
    content = _make_content(extra=(
        "\n<!-- INJECT_ACTIVITY: reading, Past participle reading -->\n"
        "\n<!-- INJECT_ACTIVITY: essay-response, Compose 5 sentences -->\n"
        "\n<!-- INJECT_ACTIVITY: fill-in, Past tense forms -->\n"
        "\n<!-- INJECT_ACTIVITY: error-correction, Aspect mistakes -->\n"
        "\n<!-- INJECT_ACTIVITY: quiz, Participle vs adjective -->\n"
        "\n<!-- INJECT_ACTIVITY: match-up, Verb to participle -->\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert ex_errors == [], (
        f"Loose marker regex should match `type, description` form. "
        f"Got: {[str(e) for e in ex_errors]}"
    )


def test_exercises_jsx_components_count():
    """Already-injected JSX activity components count (#1054)."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
    ])
    content = _make_content(extra='\n<Quiz id="test" items={[]} />\n')
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


def test_exercises_mixed_inject_and_legacy():
    """Mix of INJECT markers and legacy DSL counts correctly."""
    plan = _make_plan_with_activities(activity_hints=[
        {"type": "quiz", "title": "Test 1"},
        {"type": "fill-in", "title": "Test 2"},
        {"type": "match-up", "title": "Test 3"},
    ])
    content = _make_content(extra=(
        "\n<!-- INJECT_ACTIVITY: quiz-test -->\n"
        "\n:::fill-in\nsome content\n:::\n"
        "\n<MatchUp id=\"test\" items={[]} />\n"
    ))
    results = quick_verify(content, plan)
    ex_errors = [r for r in results if r.check == "EXERCISES"]
    assert len(ex_errors) == 0


# --- AC10: Retry catches bad output ---


def test_retry_catches_bad_output():
    """Content missing H2 headers fails quick_verify, and
    build_correction_directive produces a non-empty directive."""
    plan = _make_plan(
        sections=[
            {"section": "Привітання (Greetings)", "words": 400},
            {"section": "Знайомство (Introductions)", "words": 400},
        ],
        word_target=800,
    )
    # Content has NO H2 headers at all — just plain text
    bad_content = "Українська мова дуже гарна і мелодійна. " * 150

    results = quick_verify(bad_content, plan)
    assert has_errors(results), "Missing H2 headers should produce ERROR results"

    structure_errors = [r for r in results if r.check == "STRUCTURE"]
    assert len(structure_errors) == 2, "Both sections should be flagged as missing"

    directive = build_correction_directive(results)
    assert directive, "Directive should be non-empty"
    assert "<correction_directive>" in directive
    assert "Привітання" in directive


# --- AC11: Exhausted retries flags human ---


def test_exhausted_retries_flags_human(tmp_path, monkeypatch):
    """When all retries are exhausted, an error report is generated."""
    import importlib

    # Import v6_build module
    v6_mod = importlib.import_module("build.v6_build")

    # Set up a fake curriculum root in tmp_path
    level = "a1"
    slug = "test-slug"

    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    plan_dir = curriculum_root / "plans" / level
    plan_dir.mkdir(parents=True)
    level_dir = curriculum_root / level
    level_dir.mkdir(parents=True)

    # Write a minimal plan
    plan_content = {
        "title": "Test Module",
        "word_target": 1200,
        "content_outline": [
            {"section": "Section A", "words": 600},
            {"section": "Section B", "words": 600},
        ],
    }
    import yaml as _yaml
    (plan_dir / f"{slug}.yaml").write_text(
        _yaml.dump(plan_content, allow_unicode=True), "utf-8",
    )

    # Write bad content that always fails quick_verify (missing headers, too short)
    bad_md = "This is bad content without any H2 headers or Ukrainian."
    content_path = level_dir / f"{slug}.md"
    content_path.write_text(bad_md, "utf-8")

    # Monkeypatch CURRICULUM_ROOT and step_write to always return bad content
    monkeypatch.setattr(v6_mod, "CURRICULUM_ROOT", curriculum_root)

    def fake_step_write(level, module_num, slug, packet_path,
                        writer="gemini", correction_directive="", skeleton="",
                        no_chunk=False, **kwargs):
        """Always return the bad content file."""
        content_path.write_text(bad_md, "utf-8")
        return content_path

    monkeypatch.setattr(v6_mod, "step_write", fake_step_write)

    # Run with max_retries=1 (2 total attempts)
    result = v6_mod.step_write_with_retry(
        level=level, module_num=1, slug=slug,
        packet_path=None, writer="gemini", max_retries=1,
    )

    # Should return the output (for human to fix)
    assert result is not None

    # Error report should exist
    error_report = curriculum_root / level / "build-errors" / f"{slug}-errors.md"
    assert error_report.exists(), "Error report should be generated"
    report_text = error_report.read_text("utf-8")
    assert "Build Error Report" in report_text
    assert "Attempts: 2" in report_text

    # Friction file should exist (AC9 integration check)
    friction_path = curriculum_root / level / "orchestration" / slug / "friction.yaml"
    assert friction_path.exists(), "Friction file should be auto-generated"
    friction_data = _yaml.safe_load(friction_path.read_text("utf-8"))
    assert isinstance(friction_data, list)
    assert len(friction_data) >= 1
    entry = friction_data[-1]
    assert entry["source"] == "auto-generated"
    assert entry["status"] == "active"
    assert "V6 build failed after 2 attempts" in entry["note"]
