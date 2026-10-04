from __future__ import annotations

from pathlib import Path

import pytest

from scripts.hygiene import lint_tmp_paths as lint

LITERAL = "/" + "tmp/fixture"


def test_repository_literal_guard(capsys):
    assert lint.main([]) == 0, capsys.readouterr().out


def test_python_shell_tests_and_help_are_scanned(tmp_path):
    for relative in ("scripts/a.py", "scripts/a.sh", "tests/a.py"):
        path = tmp_path / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# example: {LITERAL}\n")
    assert len(lint.find_literal_tmp_paths(tmp_path)) == 3


def test_allowlist_is_exact_counted_and_line_independent(tmp_path, monkeypatch):
    path = tmp_path / "scripts/a.py"
    path.parent.mkdir()
    line = f'ROOT = "{LITERAL}"'
    path.write_text("# heading\n" + line + "\n")
    monkeypatch.setattr(lint, "ALLOWLIST", (("scripts/a.py", "fixture only", lint.line_digest(line) + ":1"),))
    assert lint.find_literal_tmp_paths(tmp_path) == []
    path.write_text(line + "\n" + line + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/a.py", 2)]
    path.write_text(line.replace("fixture", "new-producer") + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == [("scripts/a.py", 1)]
    monkeypatch.setattr(lint, "ALLOWLIST", (("scripts/a.py", "", ""),))
    with pytest.raises(ValueError, match="reason"):
        lint.find_literal_tmp_paths(tmp_path)


def test_managed_and_harness_paths_do_not_match(tmp_path):
    path = tmp_path / "scripts/a.py"
    path.parent.mkdir()
    path.write_text('ROOT = "$TMPDIR/probe"\n# ~/.gemini' + LITERAL.replace("fixture", "project") + "\n")
    assert lint.find_literal_tmp_paths(tmp_path) == []


def test_cli_exit_status(tmp_path, capsys):
    assert lint.main(["--repo", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "literal_tmp_findings=0\n"
    path = tmp_path / "tests/a.py"
    path.parent.mkdir()
    path.write_text(f'ROOT = "{LITERAL}"\n')
    assert lint.main(["--repo", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "tests/a.py:1" in out and "literal_tmp_findings=1" in out
    assert "$TMPDIR/" in out and "tempfile.TemporaryDirectory()/NamedTemporaryFile()" in out
    assert "scripts/hygiene/lint_tmp_paths.py" in out and "ALLOWLIST" in out
    assert "specific reason" in out and "#9702" in out
    assert f"counted fingerprint={lint.line_digest(path.read_text().strip())}:1" in out
    assert "maximum allowed count" in out and "never a whole-file exemption" in out
    assert LITERAL not in out


def test_cli_repeated_allowlisted_line_reports_total_count(tmp_path, monkeypatch, capsys):
    path = tmp_path / "tests/a.py"
    path.parent.mkdir()
    line = f'ROOT = "{LITERAL}"'
    digest = lint.line_digest(line)
    monkeypatch.setattr(lint, "ALLOWLIST", (("tests/a.py", "fixture only", f"{digest}:1"),))
    path.write_text(line + "\n  " + line + "\n")
    assert lint.main(["--repo", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "tests/a.py:2" in out and "tests/a.py:1" not in out
    assert f"counted fingerprint={digest}:2" in out
    assert "Merge the fingerprint into the file's existing entry" in out
    assert "literal_tmp_findings=1" in out and LITERAL not in out


def test_prevention_examples_and_worker_preamble_use_managed_lease():
    from scripts import delegate
    from scripts.review import integration_check
    from scripts.wiki.diagnostics import retrieval_probe_9233

    prompt = delegate._augment_prompt_with_worktree("test", Path.cwd(), mode="workspace-write")
    assert "use `$TMPDIR`, the managed lease, never a literal system temp path" in prompt
    for parser in (integration_check.build_parser(), retrieval_probe_9233.build_parser()):
        help_text = parser.format_help()
        assert "$TMPDIR/" in help_text
        assert LITERAL.split("fixture")[0] not in help_text
