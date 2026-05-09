"""Regression tests for migrate_to_html.py overwrite safety."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
SCRIPT = REPO_ROOT / "scripts" / "docs" / "migrate_to_html.py"


def _run_migrate(input_path: Path, output_path: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(PROJECT_PYTHON), str(SCRIPT), *extra_args, str(input_path), str(output_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def _write_markdown(path: Path, title: str) -> None:
    path.write_text(f"# {title}\n\nBody text.\n", encoding="utf-8")


def test_refuses_hand_curated_destination_without_force(tmp_path: Path) -> None:
    md_path = tmp_path / "REPORT.md"
    html_path = tmp_path / "REPORT.html"
    _write_markdown(md_path, "Regenerated Report")
    original_html = (
        "<!doctype html>\n"
        "<html><head><meta name=\"report-author\" content=\"claude,codex\" /></head>\n"
        "<body>hand curated</body></html>\n"
    )
    html_path.write_text(original_html, encoding="utf-8")

    result = _run_migrate(md_path, html_path)

    assert result.returncode == 1
    assert (
        f"REFUSE: {html_path} appears hand-curated (report-author=claude,codex); "
        "pass --force to overwrite."
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
        "<html><head><meta name=\"report-author\" content=\"codex\" /></head><body>old</body></html>",
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
