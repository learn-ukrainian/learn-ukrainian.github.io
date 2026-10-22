"""Standard line numbering for S-records (issue #9487, check 9).

The State Standard holds page-break form feeds. ``str.splitlines`` split at them, so the old
numbering put the Standard's line 571 at 585, and packs built then recorded, for a locator of
571-572, the text the file holds at 557-558. Lines are now the file's LF-delimited lines, the
numbering an arc, an editor and ``grep -n`` use.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.curriculum.evidence import codes, lock, sources
from tests.curriculum.evidence.test_pack import _build, _verify


def _standard(tmp_path: Path) -> Path:
    path = tmp_path / "standard-with-page-breaks.txt"
    # Form feeds at a line start (2), mid-line (3) and on their own line (4); a CR stays text (5).
    path.write_bytes(b"line one\n\x0cline two\nline\x0cthree\n\x0c\nline five\r\nline six\n")
    return path


def test_standard_lines_are_the_files_lf_lines() -> None:
    assert sources.standard_file_lines("a\n\x0cb\nc\r\n") == ["a", "\x0cb", "c\r"]
    assert sources.standard_file_lines("a\nb") == ["a", "b"]
    assert sources.standard_file_lines("a\n\n") == ["a", ""]


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
