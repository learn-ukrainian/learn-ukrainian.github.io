"""CI gate and behavior tests for Python CLI help (#10955)."""

from __future__ import annotations

import ast
import hashlib
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
    errors, _ = checker.find_violations()
    assert errors == [], "\n".join(errors)


def test_passing_help(tmp_path: Path) -> None:
    root, _ = fixture_root(tmp_path)
    assert checker.find_violations(root) == ([], {})


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


def test_probe_uses_temporary_cwd(tmp_path: Path) -> None:
    root, script = fixture_root(tmp_path, PASSING.replace(
        'parser.parse_args()', 'import os; assert os.getcwd() != ' + repr(str(tmp_path)) + '; parser.parse_args()',
    ))
    assert checker.probe_help(script, root) is None


def test_analyze_dead_code_help_does_not_start_analysis(tmp_path: Path) -> None:
    script = checker.REPO_ROOT / "scripts/tools/analyze_dead_code.py"
    assert checker.probe_help(script, checker.REPO_ROOT) is None
    result = subprocess.run(
        [sys.executable, str(script), "--help"], cwd=tmp_path,
        capture_output=True, text=True, timeout=5, check=False,
    )
    assert result.returncode == 0
    assert "Identify scripts" in result.stdout
    assert "Examples:" in result.stdout
    assert "Exit codes:" in result.stdout
    assert "Analyzing" not in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_checker_help_and_entry_point(tmp_path: Path) -> None:
    assert checker.probe_help(Path(checker.__file__), checker.REPO_ROOT) is None
    result = subprocess.run(
        [sys.executable, "-m", "scripts.hygiene.lint_cli_help", "--help"],
        cwd=checker.REPO_ROOT, capture_output=True, text=True, timeout=5, check=False,
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
