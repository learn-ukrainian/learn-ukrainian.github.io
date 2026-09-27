"""Regression tests for migrate_to_html.py overwrite safety."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PYTHON = Path(sys.executable)
SCRIPT = REPO_ROOT / "scripts" / "docs" / "migrate_to_html.py"


def _run_migrate(input_path: Path, output_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PROJECT_PYTHON), str(SCRIPT), *extra_args, str(input_path), str(output_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )


def _write_markdown(path: Path, title: str) -> None:
    path.write_text(f"# {title}\n\nBody text.\n", encoding="utf-8")


def test_refuses_hand_curated_destination_without_force(tmp_path: Path) -> None:
    md_path = tmp_path / "REPORT.md"
    html_path = tmp_path / "REPORT.html"
    _write_markdown(md_path, "Regenerated Report")
    original_html = (
        "<!doctype html>\n"
        '<html><head><meta name="report-author" content="claude,codex" /></head>\n'
        "<body>hand curated</body></html>\n"
    )
    html_path.write_text(original_html, encoding="utf-8")

    result = _run_migrate(md_path, html_path)

    assert result.returncode == 1
    assert (
        f"REFUSE: {html_path} appears hand-curated (report-author=claude,codex); pass --force to overwrite."
    ) in result.stderr
    assert html_path.read_text(encoding="utf-8") == original_html


def test_overwrites_script_output_without_report_author(tmp_path: Path) -> None:
    md_path = tmp_path / "REPORT.md"
    html_path = tmp_path / "REPORT.html"
    _write_markdown(md_path, "First Title")

    first_result = _run_migrate(md_path, html_path)
    assert first_result.returncode == 0, first_result.stderr
    first_html = html_path.read_text(encoding="utf-8")
    assert "report-author" not in first_html

    _write_markdown(md_path, "Second Title")
    second_result = _run_migrate(md_path, html_path)

    assert second_result.returncode == 0, second_result.stderr
    second_html = html_path.read_text(encoding="utf-8")
    assert "Second Title" in second_html
    assert "First Title" not in second_html


def test_force_overwrites_hand_curated_destination(tmp_path: Path) -> None:
    md_path = tmp_path / "REPORT.md"
    html_path = tmp_path / "REPORT.html"
    _write_markdown(md_path, "Forced Report")
    html_path.write_text(
        '<html><head><meta name="report-author" content="codex" /></head><body>old</body></html>',
        encoding="utf-8",
    )

    result = _run_migrate(md_path, html_path, "--force")

    assert result.returncode == 0, result.stderr
    html_text = html_path.read_text(encoding="utf-8")
    assert "Forced Report" in html_text
    assert "report-author" not in html_text


def test_writes_fresh_destination(tmp_path: Path) -> None:
    md_path = tmp_path / "REPORT.md"
    html_path = tmp_path / "REPORT.html"
    _write_markdown(md_path, "Fresh Report")

    result = _run_migrate(md_path, html_path)

    assert result.returncode == 0, result.stderr
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "Fresh Report" in html_text
    assert "report-class" in html_text


def test_same_source_is_byte_identical_at_different_wall_clocks(tmp_path: Path, monkeypatch) -> None:
    from scripts.docs import migrate_to_html

    md_path = tmp_path / "REPORT.md"
    md_path.write_text("---\ndate: 2026-04-23\n---\n# Dated Report\n\nBody.\n", encoding="utf-8")
    first = tmp_path / "a.html"
    second = tmp_path / "b.html"
    clocks = iter([datetime(2020, 1, 1, 1, 2, 3), datetime(2030, 12, 31, 23, 59, 0)])

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return next(clocks)

    monkeypatch.setattr(migrate_to_html, "datetime", FrozenDatetime, raising=False)
    assert migrate_to_html.migrate(md_path, first, force=True)
    assert migrate_to_html.migrate(md_path, second, force=True)
    assert first.read_bytes() == second.read_bytes()
    html = first.read_text(encoding="utf-8")
    assert 'name="report-date" content="2026-04-23"' in html
    assert "Migrated from Markdown on 2026-04-23" in html
    assert "2020-01-01" not in html
    assert "2030-12-31" not in html
