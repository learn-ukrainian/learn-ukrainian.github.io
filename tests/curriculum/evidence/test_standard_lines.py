"""Standard line numbering for S-records (issue #9487, check 9).

The State Standard holds page-break form feeds. ``str.splitlines`` split at them, so the old
numbering put the Standard's line 571 at 585, and packs built then recorded, for a locator of
571-572, the text the file holds at 557-558. Lines are now the file's LF-delimited lines, the
numbering an arc, an editor and ``grep -n`` use.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import codes, lock, sources, verify
from tests.curriculum.evidence.test_pack import _build, _verify

REAL_STANDARD = sources.REPO_ROOT / "docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt"


def _standard(tmp_path: Path) -> Path:
    path = tmp_path / "standard-with-page-breaks.txt"
    # Form feeds at a line start (2), mid-line (3) and on their own line (4); a CR stays text (5).
    path.write_bytes(b"line one\n\x0cline two\nline\x0cthree\n\x0c\nline five\r\nline six\n")
    return path


def test_standard_lines_are_the_files_lf_lines() -> None:
    assert sources.standard_file_lines("a\n\x0cb\nc\r\n") == ["a", "\x0cb", "c\r"]
    assert sources.standard_file_lines("a\nb") == ["a", "b"]
    assert sources.standard_file_lines("a\n\n") == ["a", ""]


def test_get_standard_lines_counts_form_feeds_and_crs_as_text(tmp_path: Path) -> None:
    with sources.Sources(standard_path=_standard(tmp_path)) as src:
        assert src.get_standard_lines(2, 2)[0] == "\x0cline two"
        assert src.get_standard_lines(3, 5)[0] == "line\x0cthree\n\x0c\nline five\r"
        assert src.get_standard_lines(6, 6)[0] == "line six"
        with pytest.raises(ValueError, match=codes.INVALID_REQUEST):
            src.get_standard_lines(7, 7)


def _grep_n(needle: str) -> list[int]:
    result = subprocess.run(
        ["grep", "-n", "-F", "--", needle, str(REAL_STANDARD)], capture_output=True, check=True, text=True, timeout=30
    )
    return [int(line.split(":", 1)[0]) for line in result.stdout.splitlines()]


@pytest.mark.parametrize(
    "needle,expected",
    [
        ("4.1.1. Український алфавіт", [571]),
        ("1.3.1.1. Особа вміє", [342, 893, 1612, 2639, 3687, 4804]),
        ("1.3.1. Загальний перелік умінь", None),
    ],
)
def test_real_standard_lines_match_grep_n(needle: str, expected: list[int] | None) -> None:
    """The real Standard (read only, page-break form feeds included) is numbered as ``grep -n`` numbers it."""
    assert b"\x0c" in REAL_STANDARD.read_bytes()
    grep_n = _grep_n(needle)
    if expected is not None:
        assert grep_n == expected
    lines = sources.read_standard_lines(REAL_STANDARD)
    assert [number for number, text in enumerate(lines, 1) if needle in text] == grep_n
    with sources.Sources(standard_path=REAL_STANDARD) as src:
        for number in grep_n:
            assert needle in src.get_standard_lines(number, number)[0]


def _request(tmp_path: Path, lines: str) -> Path:
    request = tmp_path / "req.yaml"
    request.write_text(
        yaml.safe_dump({"request_schema": 1, "module": "a1/test-mod", "standard": [{"id": "S-001", "lines": lines}]}),
        encoding="utf-8",
    )
    return request


def _standard_errors(synthetic_sources: Path, standard: Path, evidence_dir: Path) -> list[str]:
    """pack-verify's Standard errors (the synthetic world has no plan, which pack-verify also reports)."""
    errors = _verify(synthetic_sources, standard, evidence_dir, strict=False)["errors"]
    return [error for error in errors if error.startswith(codes.STANDARD_MISMATCH)]


def test_pack_verify_names_where_a_misplaced_standard_text_really_is(synthetic_sources, tmp_path: Path) -> None:
    standard = _standard(tmp_path)
    evidence_dir = tmp_path / "evidence" / "a1"  # a Standard-only pack needs no word store
    evidence_dir.mkdir(parents=True)
    _build(synthetic_sources, standard, evidence_dir, _request(tmp_path, "2-3"))
    assert _standard_errors(synthetic_sources, standard, evidence_dir) == []

    pack_path = evidence_dir / "test-mod.yaml"
    doc = yaml.safe_load(pack_path.read_text(encoding="utf-8"))
    assert doc["standard"][0]["text"] == "\x0cline two\nline\x0cthree"
    doc["standard"][0]["lines"] = "3-4"  # the locator moves; the recorded text stays lines 2-3
    lock.write(pack_path, lock.yaml_bytes(doc))
    errors = _standard_errors(synthetic_sources, standard, evidence_dir)
    assert len(errors) == 1
    assert errors[0].startswith(f"{codes.STANDARD_MISMATCH}: standard S-001 text differs from the Standard's lines 3-4")
    assert "the recorded text is at lines 2-3" in errors[0]


def test_standard_text_location_is_none_for_text_not_in_the_file(tmp_path: Path) -> None:
    with sources.Sources(standard_path=_standard(tmp_path)) as src:
        assert verify._standard_text_location(src, "line two") is None
        assert verify._standard_text_location(src, "\x0cline two\nline\x0cthree") == "2-3"
