"""Regression for insert_after fix directive (plateau diagnosis, 2026-04-14).

The review prompt (`scripts/build/phases/v6-review.md:163`) tells the reviewer
to use `insert_after: <anchor>` + `text: <payload>` directives for
word-count shortfalls. The parser in `v6_build._parse_review_fixes`
previously kept only entries with both `find` and `replace` keys, so
`insert_after` directives were silently dropped. Under-target modules
therefore plateaued indefinitely — every under-1200-word A1 module
hit this path.

These tests lock the fix in place.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build.v6_build import _apply_review_fixes, _parse_review_fixes


def _wrap(payload: str) -> str:
    return f"""Some review prose before.

<fixes>
{payload}
</fixes>

Trailing prose.
"""


class TestParseReviewFixes:
    def test_parses_insert_after_directive(self) -> None:
        fixes = _parse_review_fixes(
            _wrap(
                '- insert_after: "anchor text here"\n'
                '  text: " appended payload"\n'
            )
        )
        assert len(fixes) == 1
        assert fixes[0]["insert_after"] == "anchor text here"
        assert fixes[0]["text"] == " appended payload"

    def test_parses_mixed_find_and_insert(self) -> None:
        fixes = _parse_review_fixes(
            _wrap(
                '- find: "old phrase"\n'
                '  replace: "new phrase"\n'
                '- insert_after: "anchor"\n'
                '  text: " extra"\n'
            )
        )
        assert len(fixes) == 2
        assert "replace" in fixes[0]
        assert "insert_after" in fixes[1]

    def test_ignores_incomplete_directives(self) -> None:
        fixes = _parse_review_fixes(
            _wrap(
                '- insert_after: "anchor"\n'
                '- text: "orphan"\n'
                '- find: "only-find"\n'
            )
        )
        assert fixes == []


class TestApplyInsertAfter:
    def test_inserts_payload_after_anchor(self, tmp_path: Path) -> None:
        content_path = tmp_path / "m.md"
        content_path.write_text(
            "Opening line.\n"
            "Self-check question one? Self-check question two?\n"
            "Closing line.\n",
            "utf-8",
        )
        review = _wrap(
            '- insert_after: "Self-check question two?"\n'
            '  text: " Extra Ukrainian practice: Я хочу каву."\n'
        )
        ok, count = _apply_review_fixes(review, content_path)
        assert ok is True
        assert count == 1
        out = content_path.read_text("utf-8")
        assert "Self-check question two? Extra Ukrainian practice: Я хочу каву." in out
        # Pre- and post- content preserved.
        assert out.startswith("Opening line.")
        assert out.endswith("Closing line.\n")

    def test_reports_when_anchor_missing(self, tmp_path: Path) -> None:
        content_path = tmp_path / "m.md"
        content_path.write_text("Unrelated content.\n", "utf-8")
        review = _wrap(
            '- insert_after: "absent anchor"\n'
            '  text: " payload"\n'
        )
        ok, count = _apply_review_fixes(review, content_path)
        assert ok is False
        assert count == 0
        # Content unchanged.
        assert content_path.read_text("utf-8") == "Unrelated content.\n"

    def test_stress_mark_tolerant_anchor(self, tmp_path: Path) -> None:
        # Content has combining acute after ч.
        content_path = tmp_path / "m.md"
        content_path.write_text("Я хочу\u0301 каву.\n", "utf-8")
        review = _wrap(
            '- insert_after: "Я хочу каву."\n'
            '  text: " Додатково: я мушу працювати."\n'
        )
        ok, count = _apply_review_fixes(review, content_path)
        assert ok is True
        assert count == 1
        out = content_path.read_text("utf-8")
        assert "Додатково: я мушу працювати." in out
        # Original stress mark preserved.
        assert "хочу\u0301" in out
