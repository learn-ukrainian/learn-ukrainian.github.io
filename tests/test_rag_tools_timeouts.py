"""Regression tests for bounded subprocess calls in RAG and tooling scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


def _result(*, stdout="", stderr="", returncode=0) -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_extract_text_subprocesses_have_pdf_and_ocr_bounds(monkeypatch, tmp_path: Path) -> None:
    import scripts.rag.extract_text as extract

    helper = tmp_path / "helper.swift"
    helper.write_text("// fixture", encoding="utf-8")
    calls: list[dict[str, object]] = []

    def fake_run(_command, **kwargs):
        calls.append(kwargs)
        return _result(
            stdout=json.dumps(
                {
                    "schema_version": extract.SWIFT_OCR_SCHEMA,
                    "metadata": {},
                    "pages": [
                        {
                            "page_number": 1,
                            "text": "Текст.",
                            "observation_count": 1,
                            "mean_confidence": 0.9,
                            "line_break_count": 1,
                        }
                    ],
                }
            )
        )

    monkeypatch.setattr(extract.subprocess, "run", fake_run)
    extract.run_apple_pdfkit_native(tmp_path / "fixture.pdf", helper_path=helper)
    extract.run_apple_pdfkit_native_spatial(tmp_path / "fixture.pdf", [1], helper_path=helper)
    extract.run_apple_vision_ocr(tmp_path / "fixture.pdf", [1], helper_path=helper)

    assert [call["timeout"] for call in calls] == [300, 300, 300]


def test_poc_pair_page_browser_open_is_bounded(monkeypatch, tmp_path: Path) -> None:
    import scripts.rag.poc_pair_page as poc

    pdf_path = tmp_path / "fixture.pdf"
    pdf_path.write_bytes(b"fixture")

    class EmptyDocument:
        def __len__(self):
            return 0

        def close(self):
            pass

    monkeypatch.setattr(poc.pymupdf, "open", lambda _path: EmptyDocument())
    calls: list[dict[str, object]] = []

    def fake_run(_command, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["poc_pair_page.py", str(pdf_path), "1", "--open", "--out", str(tmp_path / "out")],
    )
    poc.main()

    assert calls[0]["timeout"] == 30


def test_diasporiana_subprocesses_have_bounds(monkeypatch, tmp_path: Path) -> None:
    import scripts.rag.scrape_diasporiana as diasporiana

    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs)
        if command[0] == "pdfinfo":
            return _result(stdout="Pages:           3\n")
        if command[0] == "tesseract" and command[1] == "--list-langs":
            return _result(stdout="List of available languages in \"/tmp\":\nukr\nrus\n")
        return _result(stdout="Результат.".encode())

    monkeypatch.setattr(diasporiana.subprocess, "run", fake_run)
    monkeypatch.setattr(diasporiana.shutil, "which", lambda name: f"/usr/bin/{name}")

    assert diasporiana.get_pdf_page_count(tmp_path / "fixture.pdf") == 3
    assert diasporiana._run_pdftotext(tmp_path / "fixture.pdf") == "Результат."
    diasporiana.ensure_tesseract_available()

    output_prefix = tmp_path / "page-0001"
    def fake_render_run(command, **kwargs):
        calls.append(kwargs)
        if command[0] == "pdftoppm":
            output_prefix.with_suffix(".png").write_bytes(b"png")
            return _result()
        return _result(stdout="Результат.".encode())

    monkeypatch.setattr(diasporiana.subprocess, "run", fake_render_run)
    diasporiana.render_page_image(tmp_path / "fixture.pdf", 1, output_prefix)
    diasporiana.ocr_image(output_prefix.with_suffix(".png"))

    assert [call["timeout"] for call in calls] == [120, 120, 60, 300, 300]


def test_scraper_fetches_have_bounds(monkeypatch) -> None:
    import scripts.rag.scrape_litopys as litopys
    import scripts.rag.scrape_ukrlib as ukrlib

    calls: list[dict[str, object]] = []

    def fake_run(_command, **kwargs):
        calls.append(kwargs)
        return _result(stdout=b"<html>text</html>")

    monkeypatch.setattr(litopys.subprocess, "run", fake_run)
    monkeypatch.setattr(ukrlib.subprocess, "run", fake_run)
    assert litopys.fetch_page("http://example.test")
    assert ukrlib.fetch_page("https://example.test")

    assert [call["timeout"] for call in calls] == [60, 60]


def test_agent_watcher_subprocesses_have_bounds(monkeypatch) -> None:
    import scripts.tools.agent_watcher as watcher

    calls: list[dict[str, object]] = []

    def fake_run(_command, **kwargs):
        calls.append(kwargs)
        return _result(returncode=1)

    monkeypatch.setattr(watcher.subprocess, "run", fake_run)
    monkeypatch.setattr(watcher, "load_agent_config", lambda: {"agent": {"process_pattern": "agent"}})
    assert watcher.is_any_agent_active() is False
    watcher.notify_human("codex", "gemini", 1, "timeout-test")

    assert [call["timeout"] for call in calls] == [10, 30]


def test_dead_code_analyzer_subprocesses_have_bounds(monkeypatch, tmp_path: Path) -> None:
    import scripts.tools.analyze_dead_code as dead_code

    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs)
        if command[0] == "git":
            return _result(stdout="2026-08-24 12:00:00 +0000\n")
        return _result()

    monkeypatch.setattr(dead_code.subprocess, "run", fake_run)
    analyzer = dead_code.DeadCodeAnalyzer(tmp_path)
    assert analyzer.get_last_modified(tmp_path / "script.py") is not None
    assert analyzer.count_external_references("script.py") == (0, [])
    assert analyzer.find_python_imports("script.py") == (0, [])

    assert [call["timeout"] for call in calls] == [30, 30, 30]


def test_coverage_report_subprocess_has_bound(monkeypatch, tmp_path: Path) -> None:
    import scripts.tools.coverage_report as coverage_report

    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs)
        report_arg = next(arg for arg in command if arg.startswith("--cov-report=json:"))
        Path(report_arg.removeprefix("--cov-report=json:")).write_text('{"files": {}}', encoding="utf-8")
        return _result()

    monkeypatch.setattr(coverage_report.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["coverage_report.py"])
    assert coverage_report.main() == 0
    assert calls[0]["timeout"] == 180


def test_verify_subprocesses_have_bounds(monkeypatch, tmp_path: Path) -> None:
    import scripts.tools.hetman_verify as hetman
    import scripts.tools.otaman_verify as otaman

    content_path = tmp_path / "lesson.md"
    content_path.write_text("# fixture", encoding="utf-8")
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append(kwargs)
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(hetman.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["hetman_verify.py", str(content_path)])
    assert hetman.main() == 1

    monkeypatch.setattr(otaman.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["otaman_verify.py", str(content_path)])
    assert otaman.main() == 1

    assert [call["timeout"] for call in calls] == [180, 180]
