from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.phases.honesty_annotator import annotate_content
from build.v6_build import step_honesty_annotate


def _annotated_line(text: str) -> str:
    annotated, log = annotate_content(text)
    assert len(log) == 1
    return annotated


def test_percent_pattern_is_annotated() -> None:
    annotated = _annotated_line("Ukrainian is 42% vowelic.")
    assert annotated == "Ukrainian is 42% vowelic. <!-- VERIFY: precise claim (42%) -->"


def test_range_percent_is_annotated() -> None:
    annotated = _annotated_line("42–46% of spoken Ukrainian is vowels.")
    assert annotated == "42–46% of spoken Ukrainian is vowels. <!-- VERIFY: precise claim (42–46%) -->"


def test_ukrainian_linguistic_units_are_annotated() -> None:
    annotated, log = annotate_content("Ukrainian has 33 літер і 38 звуків.")
    assert " <!-- VERIFY: precise claim (33 літер; 38 звуків) -->" in annotated
    assert log[0]["matches"] == ["33 літер", "38 звуків"]


def test_english_linguistic_units_are_annotated() -> None:
    annotated, log = annotate_content("Ukrainian has 33 letters but 38 sounds.")
    assert " <!-- VERIFY: precise claim (33 letters; 38 sounds) -->" in annotated
    assert log[0]["matches"] == ["33 letters", "38 sounds"]


def test_plain_prose_is_unchanged() -> None:
    content = "Ukrainian is a beautiful language."
    assert annotate_content(content) == (content, [])


def test_already_marked_line_is_unchanged() -> None:
    content = "42% vowelic <!-- VERIFY: existing marker -->"
    assert annotate_content(content) == (content, [])


def test_code_fence_is_skipped() -> None:
    content = "```python\ncount = 42%\n```\n"
    assert annotate_content(content) == (content, [])


def test_heading_is_skipped() -> None:
    content = "## 33 letters"
    assert annotate_content(content) == (content, [])


def test_admonition_markers_are_skipped() -> None:
    content = ":::tip\n:::\n"
    assert annotate_content(content) == (content, [])


def test_html_comment_only_line_is_skipped() -> None:
    content = "<!-- some note -->"
    assert annotate_content(content) == (content, [])


def test_idempotency() -> None:
    content = "- Ukrainian has 33 letters.\n42–46% of spoken Ukrainian is vowels.\n"
    once, _ = annotate_content(content)
    twice, _ = annotate_content(once)
    assert twice == once


def test_list_item_is_annotated() -> None:
    annotated = _annotated_line("- 6 vowels total")
    assert annotated == "- 6 vowels total <!-- VERIFY: precise claim (6 vowels) -->"


def test_blockquote_is_annotated() -> None:
    annotated = _annotated_line("> Ukrainian has 33 letters")
    assert annotated == "> Ukrainian has 33 letters <!-- VERIFY: precise claim (33 letters) -->"


def test_mixed_content_appends_exactly_three_markers() -> None:
    content = "\n".join(
        [
            "# Heading with 33 letters",
            "",
            "Plain intro.",
            "Ukrainian has 33 letters.",
            ":::tip",
            "The tip body has vowels.",
            ":::",
            "```python",
            "ratio = '42%'",
            "```",
            "<!-- 38 sounds note -->",
            "> Ukrainian has 38 sounds.",
            "No precise claim here.",
            "- The alphabet has 10 vowels.",
            "## Another heading 42%",
            "",
            "Closing sentence.",
            "Already 42% marked <!-- VERIFY: existing -->",
            ":::note",
            ":::",
        ]
    )
    annotated, log = annotate_content(content)
    assert annotated.count("<!-- VERIFY: precise claim") == 3
    assert len(log) == 3


def test_multi_sentence_line_marker_attaches_to_matching_first_sentence() -> None:
    annotated, log = annotate_content(
        "Ukrainian has 33 letters. Кави я люблю вранці."
    )
    assert annotated == (
        "Ukrainian has 33 letters. <!-- VERIFY: precise claim (33 letters) --> "
        "Кави я люблю вранці."
    )
    assert log[0]["matches"] == ["33 letters"]


def test_multi_sentence_line_marker_attaches_to_matching_second_sentence() -> None:
    annotated, log = annotate_content(
        "Кави я люблю вранці. Ukrainian has 38 sounds."
    )
    assert annotated == (
        "Кави я люблю вранці. Ukrainian has 38 sounds."
        " <!-- VERIFY: precise claim (38 sounds) -->"
    )
    assert log[0]["matches"] == ["38 sounds"]


def test_multi_sentence_line_marker_attaches_to_middle_sentence() -> None:
    annotated, log = annotate_content(
        "First sentence. Ukrainian has 42% vowels. Third sentence."
    )
    assert annotated == (
        "First sentence. Ukrainian has 42% vowels."
        " <!-- VERIFY: precise claim (42%) --> Third sentence."
    )
    assert log[0]["matches"] == ["42%"]


def test_current_sounds_letters_fixture_would_gain_markers() -> None:
    fixture = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "a1" / "sounds-letters-and-hello.md"
    content = fixture.read_text("utf-8")
    annotated, log = annotate_content(content)
    assert annotated != content
    assert annotated.count("<!-- VERIFY: precise claim") >= 4
    assert len(log) >= 4


def test_step_honesty_annotate_writes_content_and_log(tmp_path: Path) -> None:
    content_path = tmp_path / "a1" / "fixture.md"
    content_path.parent.mkdir(parents=True)
    content_path.write_text("Ukrainian has 33 letters.\nPlain line.\n", "utf-8")
    orch_dir = tmp_path / "a1" / "orchestration" / "fixture"

    assert step_honesty_annotate(content_path, "a1", "fixture", orch_dir) is True

    annotated = content_path.read_text("utf-8")
    assert "Ukrainian has 33 letters. <!-- VERIFY: precise claim (33 letters) -->" in annotated

    log_path = orch_dir / "honesty-annotations.json"
    assert log_path.exists()
    payload = json.loads(log_path.read_text("utf-8"))
    assert payload[0]["line_num"] == 1
    assert payload[0]["line"] == "Ukrainian has 33 letters."
    assert payload[0]["matches"] == ["33 letters"]
    assert payload[0]["marker"] == " <!-- VERIFY: precise claim (33 letters) -->"
