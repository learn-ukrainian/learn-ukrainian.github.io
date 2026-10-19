"""CI gate and behavior tests for Python CLI help (#10955)."""

from __future__ import annotations

import ast
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.hygiene import lint_cli_help as checker

PASSING = '''import argparse
parser = argparse.ArgumentParser(
    description="Describe the fixture. Use to check help, never for analysis.",
    epilog="Examples:\\n  fixture.py --name sample\\nExit codes: 0 = success; 1 = failure.",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument("--name", default="sample", help="Name to print (default: sample), e.g. alice.")
if __name__ == "__main__":
    parser.parse_args()
'''
VIOLATOR = 'if __name__ == "__main__":\n    raise RuntimeError("must never execute this script")\n'


def fixture_root(tmp_path: Path, source: str = PASSING) -> tuple[Path, Path]:
    script = tmp_path / "scripts" / "fixture.py"
    script.parent.mkdir()
    script.write_text(source)
    baseline = tmp_path / checker.BASELINE_PATH
    baseline.parent.mkdir()
    baseline.write_text("")
    return tmp_path, script


def pin(root: Path, script: Path) -> None:
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    (root / checker.BASELINE_PATH).write_text(f"{digest}  {script.relative_to(root).as_posix()}\n")


@pytest.mark.timeout(600)
def test_repository_cli_help_gate() -> None:
    errors, failures = checker.find_violations()
    assert errors == [], "\n".join(errors)
    assert len(failures) == 970


def test_passing_help(tmp_path: Path) -> None:
    root, _ = fixture_root(tmp_path)
    assert checker.find_violations(root) == ([], {})


def test_source_manifest_help_does_not_read_schema_data() -> None:
    script = checker.REPO_ROOT / "scripts/projects/open_model_data/source_completeness_manifest.py"
    assert checker.probe_help(script, checker.REPO_ROOT) is None


def test_word_card_rehearsal_help_does_not_read_schema_data() -> None:
    script = checker.REPO_ROOT / "scripts/projects/open_model_data/word_cards/rehearsal.py"
    assert checker.probe_help(script, checker.REPO_ROOT) is None


@pytest.mark.parametrize("base", ["argparse.ArgumentParser", "ArgumentParser"])
@pytest.mark.parametrize("source, expected", [
    (PASSING, None),
    (PASSING.replace(
        'description="Describe the fixture. Use to check help, never for analysis."',
        'description=""',
    ), "--help lacks a description"),
    (PASSING.replace(', help="Name to print (default: sample), e.g. alice."', ""),
     "argument lacks help"),
    (PASSING.replace("Examples:", "Example:"), "epilog must name"),
    ('import argparse\nparser = argparse.ArgumentParser()\n'
     'if __name__ == "__main__":\n    parser.parse_args()\n',
     "parser lacks description or epilog"),
])
def test_subclass_parser_help(
    tmp_path: Path, base: str, source: str, expected: str | None,
) -> None:
    source = "from argparse import ArgumentParser\n" + source.replace(
        "parser = argparse.ArgumentParser(",
        f"class EvidenceArgumentParser({base}):\n    pass\n\n"
        "parser = EvidenceArgumentParser(",
    )
    root, _ = fixture_root(tmp_path, source)
    errors, failures = checker.find_violations(root)
    if expected is None:
        assert (errors, failures) == ([], {})
    else:
        assert len(errors) == 1
        assert expected in errors[0]
        assert list(failures) == ["scripts/fixture.py"]


@pytest.mark.parametrize("database_present", [False, True])
@pytest.mark.parametrize("layout", ["snapshot", "full", "shallow", "linked"])
def test_review_issues_help_is_independent_of_checkout_layout(
    tmp_path: Path, database_present: bool, layout: str,
) -> None:
    root = tmp_path / "checkout"
    shutil.copytree(checker.REPO_ROOT / "scripts", root / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if layout == "linked":
        (root / ".git").write_text(f"gitdir: {tmp_path / 'primary/.git/worktrees/fixture'}\n")
    elif layout in {"full", "shallow"}:
        git(root, "init", "-q")
        git(root, "add", "scripts/audit/check_review_issues.py")
        git(root, "-c", "core.hooksPath=/dev/null", "-c", "user.name=CLI fixture",
            "-c", "user.email=cli@example.test", "commit", "-qm", "fixture")
        if layout == "shallow":
            commit = git(root, "rev-parse", "HEAD").strip()
            (root / ".git/shallow").write_text(commit + "\n")
            assert git(root, "rev-parse", "--is-shallow-repository").strip() == "true"
    if database_present:
        (root / "data").mkdir()
        (root / "data/vesum.db").write_bytes(b"fixture, never opened")
    assert checker.probe_help(root / "scripts/audit/check_review_issues.py", root) is None


def test_review_issues_audit_resolves_interpreter_when_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.audit import check_review_issues as audit

    calls = []
    interpreter = tmp_path / "project-python"
    monkeypatch.setattr(audit, "project_interpreter", lambda: interpreter)

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "PASS\n", "")

    monkeypatch.setattr(audit.subprocess, "run", run)
    module = tmp_path / "module.md"
    assert audit._run_audit(module) == (True, "PASS\n")
    assert calls == [([
        str(interpreter), str(audit.PROJECT_ROOT / "scripts/audit_module.py"), str(module),
    ], {
        "capture_output": True, "text": True, "cwd": str(audit.PROJECT_ROOT),
        "timeout": 60.0,
    })]


@pytest.mark.parametrize("database_present", [False, True])
@pytest.mark.parametrize("help_flag", ["--help", "-h"])
def test_rag_config_help_does_not_discover_database(
    tmp_path: Path, database_present: bool, help_flag: str,
) -> None:
    config_path = tmp_path / "scripts/rag/config.py"
    source = (
        "import runpy, sys\n"
        f"sys.argv = ['fixture.py', {help_flag!r}]\n"
        f"config = runpy.run_path({str(config_path)!r})\n"
        "assert config['VESUM_DB_PATH'] == config['DATA_DIR'] / 'vesum.db'\n"
        + PASSING
    )
    root, script = fixture_root(tmp_path, source)
    config_path.parent.mkdir()
    config_path.write_bytes((checker.REPO_ROOT / "scripts/rag/config.py").read_bytes())
    if database_present:
        (root / "data").mkdir()
        (root / "data/vesum.db").write_bytes(b"fixture, never opened")
    assert checker.probe_help(script, root) is None


def test_repository_gate_is_pinned_to_full_history_shard() -> None:
    from scripts.ci.split_tests import DEFAULT_HISTORY, assign, read_list

    target = "tests/test_cli_help_ratchet.py"
    history = read_list(DEFAULT_HISTORY)
    assert target in history
    files = [*history, "tests/test_shallow_fixture.py"]
    shards = assign(files, {target: 1000.0}, 16, pinned=history)
    assert target in shards[0]
    assert all(target not in shard for shard in shards[1:])


def test_new_violator_is_never_run(tmp_path: Path) -> None:
    root, _ = fixture_root(tmp_path, VIOLATOR)
    errors, failures = checker.find_violations(root)
    assert len(errors) == 1
    assert "new or changed CLI" in errors[0]
    assert "not executed" in errors[0]
    assert list(failures) == ["scripts/fixture.py"]


def test_changed_violator_loses_exemption(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, VIOLATOR)
    pin(root, script)
    assert checker.find_violations(root)[0] == []
    script.write_text(VIOLATOR + "# changed\n")
    errors, _ = checker.find_violations(root)
    assert len(errors) == 1
    assert "new or changed CLI" in errors[0]


@pytest.mark.parametrize("state", ["fixed", "gone", "library"])
def test_stale_baseline(tmp_path: Path, state: str) -> None:
    root, script = fixture_root(tmp_path, VIOLATOR)
    pin(root, script)
    if state == "fixed":
        script.write_text(PASSING)
    elif state == "gone":
        script.unlink()
    else:
        script.write_text("value = 1\n")
    errors, _ = checker.find_violations(root)
    assert len(errors) == 1
    assert "stale baseline entry" in errors[0]


@pytest.mark.parametrize("source, expected", [
    (PASSING.replace(', help="Name to print (default: sample), e.g. alice."', ""), "argument lacks help"),
    (PASSING.replace("Examples:", "Usage:"), "epilog must name"),
    (PASSING.replace("Exit codes:", "Statuses:"), "epilog must name"),
    (PASSING.replace('description="Describe the fixture. Use to check help, never for analysis."',
                     'description=""'), "lacks a description"),
    (PASSING.replace('parser.parse_args()', 'raise SystemExit(2)'), "did not exit 0"),
    (PASSING.replace('parser.parse_args()', 'print("fake help")'), "did not print parser help"),
    (PASSING.replace('parser.parse_args()', 'print("Analyzing..."); parser.parse_args()'), "outside parser help"),
])
def test_incomplete_help(tmp_path: Path, source: str, expected: str) -> None:
    root, _ = fixture_root(tmp_path, source)
    errors, _ = checker.find_violations(root)
    assert len(errors) == 1
    assert expected in errors[0]


@pytest.mark.parametrize("work, event", [
    ('open("unexpected.txt", "w").write("bad")', "open"),
    ('import os; os.mkdir("unexpected")', "os.mkdir"),
    ('import os; list(os.scandir("."))', "os.scandir"),
    ('import subprocess; subprocess.run(["true"])', "subprocess.Popen"),
    ('import socket; socket.socket()', "socket.__new__"),
    ('import sqlite3; sqlite3.connect(":memory:")', "sqlite3.connect"),
])
def test_help_denies_work_before_it_happens(tmp_path: Path, work: str, event: str) -> None:
    root, script = fixture_root(tmp_path, PASSING.replace('parser.parse_args()', work))
    problem = checker.probe_help(script, root)
    assert problem == f"--help attempted work or writes (denied): {event}"
    assert not (root / "unexpected.txt").exists()
    assert not (root / "unexpected").exists()


def test_help_denies_absolute_writes(tmp_path: Path) -> None:
    sentinel = tmp_path / "untouched.txt"
    sentinel.write_text("original")
    root, script = fixture_root(tmp_path, PASSING.replace(
        'parser.parse_args()', f'open({str(sentinel)!r}, "w").write("bad")',
    ))
    assert "denied" in checker.probe_help(script, root)
    assert sentinel.read_text() == "original"


def test_help_times_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, script = fixture_root(tmp_path, PASSING.replace('parser.parse_args()', 'while True: pass'))
    monkeypatch.setattr(checker, "HELP_TIMEOUT", 0.1)
    assert checker.probe_help(script, root) == "--help exceeded 5 seconds"


@pytest.mark.parametrize("managed_lease", [False, True])
def test_probe_uses_temporary_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, managed_lease: bool,
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    if managed_lease:
        monkeypatch.setenv("TMPDIR", str(scratch))
        monkeypatch.setattr(checker, "ensure_scratch_root", lambda: pytest.fail("lease already exists"))
    else:
        monkeypatch.delenv("TMPDIR", raising=False)
        monkeypatch.setattr(checker, "ensure_scratch_root", lambda: scratch)
    root, script = fixture_root(tmp_path, PASSING.replace(
        'parser.parse_args()',
        'import os; assert os.path.dirname(os.getcwd()) == ' + repr(str(scratch)) + '; parser.parse_args()',
    ))
    assert checker.probe_help(script, root) is None
    assert list(scratch.iterdir()) == []


@pytest.mark.parametrize("help_flag", ["--help", "-h"])
def test_analyze_dead_code_help_does_not_start_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, help_flag: str,
) -> None:
    output_dir = tmp_path / "analysis-output"
    output_dir.mkdir()
    script = checker.REPO_ROOT / "scripts/tools/analyze_dead_code.py"
    monkeypatch.delenv("TMPDIR", raising=False)
    assert checker.probe_help(script, checker.REPO_ROOT) is None
    monkeypatch.setenv("TMPDIR", str(output_dir))
    result = subprocess.run(
        [sys.executable, str(script), help_flag], cwd=output_dir,
        capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode == 0
    assert "Identify scripts" in result.stdout
    assert "Examples:" in result.stdout
    assert "Exit codes:" in result.stdout
    assert "Analyzing" not in result.stdout
    assert not (output_dir / "dead_code_report.json").exists()
    assert list(output_dir.iterdir()) == []


@pytest.mark.parametrize("invocation", [
    ["-m", "scripts.hygiene.lint_cli_help"],
    [str(Path(checker.__file__).resolve())],
])
def test_checker_help_and_entry_point(tmp_path: Path, invocation: list[str]) -> None:
    assert checker.probe_help(Path(checker.__file__), checker.REPO_ROOT) is None
    result = subprocess.run(
        [sys.executable, *invocation, "--help"],
        cwd=checker.REPO_ROOT if invocation[0] == "-m" else tmp_path,
        capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode == 0
    assert "Examples:" in result.stdout
    assert "Exit codes:" in result.stdout


def test_main_reports_failures_and_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(checker, "find_violations", lambda: (["broken CLI"], {}))
    assert checker.main([]) == 1
    assert capsys.readouterr().err == "broken CLI\n"
    monkeypatch.setattr(checker, "find_violations", lambda: ([], {}))
    assert checker.main([]) == 0
    assert capsys.readouterr().out == "OK: CLI help standard and shrink-only baseline pass\n"


def test_main_reports_invalid_baseline(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    def fail():
        raise ValueError("invalid baseline")
    monkeypatch.setattr(checker, "find_violations", fail)
    assert checker.main([]) == 1
    assert "ValueError" in capsys.readouterr().err


def test_main_detection_and_library_exclusion(tmp_path: Path) -> None:
    assert checker.has_main(ast.parse("if '__main__' == __name__: pass"))
    assert not checker.has_main(ast.parse("text = '__main__'"))
    root, _ = fixture_root(tmp_path, "value = 1\n")
    assert checker.find_violations(root) == ([], {})


@pytest.mark.parametrize("text", ["invalid", "a" * 64 + "  ../evil.py", ("a" * 64 + "  scripts/x.py\n") * 2])
def test_malformed_baseline(text: str) -> None:
    with pytest.raises(ValueError, match="invalid or duplicate"):
        checker.load_baseline(text)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True, timeout=30).stdout


def test_baseline_may_only_shrink(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, VIOLATOR)
    pin(root, script)
    git(root, "init", "-q")
    git(root, "config", "user.name", "CLI fixture")
    git(root, "config", "user.email", "cli@example.test")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
    baseline = checker.load_baseline((root / checker.BASELINE_PATH).read_text())
    assert checker.baseline_policy_violations(root, baseline) == []
    assert checker.baseline_policy_violations(root, {}) == []
    changed = {**baseline, "scripts/new.py": "a" * 64}
    assert "may only remove" in checker.baseline_policy_violations(root, changed)[0]
    changed = {"scripts/fixture.py": "b" * 64}
    assert "may only remove" in checker.baseline_policy_violations(root, changed)[0]
    (root / "scripts/new.py").write_text(VIOLATOR)
    assert root / "scripts/new.py" in checker.scan_paths(root)


def test_package_main_without_guard(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, 'raise RuntimeError("not a help command")\n')
    script.rename(script.with_name("__main__.py"))
    errors, _ = checker.find_violations(root)
    assert len(errors) == 1
    assert "new or changed CLI" in errors[0]


def test_stale_baseline_already_passing(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path)
    pin(root, script)
    errors, _ = checker.find_violations(root)
    assert errors == ["scripts/fixture.py: stale baseline entry; --help now passes"]


def test_new_violation_with_other_exemptions(tmp_path: Path) -> None:
    root, old = fixture_root(tmp_path, VIOLATOR)
    pin(root, old)
    (root / "scripts/new.py").write_text(VIOLATOR)
    errors, _ = checker.find_violations(root)
    assert len(errors) == 1
    assert errors[0].startswith("scripts/new.py:")


def test_swallowed_work_attempt_still_fails(tmp_path: Path) -> None:
    work = "try:\n        open(\"unexpected\", \"w\")\n    except BaseException:\n        pass\n    parser.parse_args()"
    root, script = fixture_root(tmp_path, PASSING.replace('parser.parse_args()', work))
    assert checker.probe_help(script, root) == "--help attempted work or writes (denied): open"


def test_unparseable_source_fails_closed(tmp_path: Path) -> None:
    root, _ = fixture_root(tmp_path, "if __name__ == '__main__': (\n")
    assert checker.find_violations(root)[0] == ["scripts/fixture.py: cannot parse Python source"]


def test_symlink_is_not_executed(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path)
    script.with_name("link.py").symlink_to(script)
    assert checker.find_violations(root)[0] == ["scripts/link.py: script symlinks cannot be safely checked"]


def test_help_denies_data_reads(tmp_path: Path) -> None:
    data = tmp_path / "input.json"
    data.write_text("{}")
    root, script = fixture_root(tmp_path, PASSING.replace(
        'parser.parse_args()', f'open({str(data)!r}).read(); parser.parse_args()',
    ))
    assert checker.probe_help(script, root) == "--help attempted work or writes (denied): open"


def test_shallow_history_fails_closed(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, VIOLATOR)
    pin(root, script)
    git(root, "init", "-q")
    git(root, "config", "user.name", "CLI fixture")
    git(root, "config", "user.email", "cli@example.test")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
    clone = root / "shallow"
    git(root, "clone", "--depth", "1", root.as_uri(), str(clone))
    baseline = checker.load_baseline((clone / checker.BASELINE_PATH).read_text())
    assert checker.baseline_policy_violations(clone, baseline) == [
        f"{checker.BASELINE_PATH}: origin/main or full Git history is required to prove the baseline only shrinks",
    ]


def test_earlier_committed_baseline_growth_still_fails(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, VIOLATOR)
    pin(root, script)
    git(root, "init", "-q")
    git(root, "config", "user.name", "CLI fixture")
    git(root, "config", "user.email", "cli@example.test")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
    baseline = root / checker.BASELINE_PATH
    baseline.write_text(baseline.read_text() + "a" * 64 + "  scripts/new.py\n")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "growth")
    script.write_text(VIOLATOR + "# later change\n")
    git(root, "add", ".")
    git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "later change")
    assert checker.baseline_policy_violations(root, checker.load_baseline(baseline.read_text()))
