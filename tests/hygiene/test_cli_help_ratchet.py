"""CLI --help ratchet (#10955): standard help passes, violators stay frozen, the baseline only shrinks."""

from __future__ import annotations

import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.hygiene import lint_cli_help as lint
from scripts.tools import analyze_dead_code

GOOD = '''
import argparse

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Do one thing.\\nUse it for fixtures only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\\n  good.py --name x\\n\\nExit codes:\\n  0 = ok; 1 = failure",
    )
    parser.add_argument("--name", default="x", help="Name to greet (default: x).")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="Show the name.")
    parser.parse_args(argv)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''

BAD = '''
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Undocumented flags.")
    parser.add_argument("--level")
    parser.parse_args()
'''


def _tree(tmp_path: Path, scripts: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    for rel, source in {"scripts/__init__.py": "", **scripts}.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    return root


def _baseline(root: Path, entries: list[lint.Entry]) -> Path:
    path = root / "scripts" / "hygiene" / "cli_help_baseline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lint.dump_baseline(entries), encoding="utf-8")
    return path


def _pin(root: Path, rel: str) -> lint.Entry:
    return lint.Entry(rel, lint.file_sha256(root / rel), "frozen violator")


def _violations(root: Path, baseline: Path | None = None, *, recheck_frozen: bool = False) -> list[str]:
    return lint.find_violations(root, baseline or root / "missing.json", jobs=2, check_growth=False,
                                recheck_frozen=recheck_frozen)


def test_standard_help_passes(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/good.py": GOOD, "scripts/library.py": "VALUE = 1\n"})
    assert lint.evaluate(root, "scripts/good.py") is None
    assert _violations(root) == []


def test_new_violator_fails(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/good.py": GOOD, "scripts/bad.py": BAD})
    [violation] = _violations(root)
    assert violation.startswith("scripts/bad.py: --help fails the CLI help standard:")
    assert "1 argument(s) without help: --level" in violation
    assert "epilog lacks Examples and Exit codes" in violation


def test_unchanged_violator_is_frozen_but_a_changed_one_must_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _tree(tmp_path, {"scripts/bad.py": BAD})
    baseline = _baseline(root, [_pin(root, "scripts/bad.py")])
    assert _violations(root, baseline, recheck_frozen=True) == []
    with monkeypatch.context() as patch:
        patch.setattr(lint, "probe", lambda *_: pytest.fail("a byte-identical frozen entry was executed"))
        assert _violations(root, baseline) == []

    (root / "scripts/bad.py").write_text(BAD + "# touched\n", encoding="utf-8")
    [violation] = _violations(root, baseline)
    assert violation.startswith("scripts/bad.py: changed since baselined, so --help must pass:")


def test_stale_baseline_entries_fail(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/good.py": GOOD, "scripts/fixed.py": GOOD, "scripts/gone.py": BAD})
    gone = _pin(root, "scripts/gone.py")
    (root / "scripts/gone.py").unlink()
    fixed = lint.Entry("scripts/fixed.py", "0" * 64, "pinned before its --help was fixed")
    baseline = _baseline(root, [fixed, gone, _pin(root, "scripts/good.py")])
    assert _violations(root, baseline) == [
        "scripts/fixed.py: stale baseline entry: script passes or is no longer a CLI; remove it",
        "scripts/gone.py: stale baseline entry: script is gone; remove it",
    ]
    # A byte-identical entry that passes (say, through a changed import) is stale on recheck.
    assert _violations(root, baseline, recheck_frozen=True) == [
        "scripts/fixed.py: stale baseline entry: script passes or is no longer a CLI; remove it",
        "scripts/good.py: stale baseline entry: script passes or is no longer a CLI; remove it",
        "scripts/gone.py: stale baseline entry: script is gone; remove it",
    ]


def test_cli_without_parser_fails_without_running(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _tree(tmp_path, {"scripts/raw.py": 'import sys\nif __name__ == "__main__":\n    print(sys.argv)\n'})
    monkeypatch.setattr(lint, "probe", lambda *_: pytest.fail("a script that ignores --help was executed"))
    assert lint.evaluate(root, "scripts/raw.py") == "no argparse parser: --help ignored, not executed"


def test_side_effects_are_blocked_and_fail(tmp_path: Path) -> None:
    marker = tmp_path / "written.txt"
    script = GOOD.replace("import argparse\n", f"import argparse\nopen({str(marker)!r}, 'w').close()\n", 1)
    root = _tree(tmp_path, {"scripts/writer.py": script})
    reason = lint.evaluate(root, "scripts/writer.py")
    assert reason is not None and reason.startswith("side effect during --help: open '<path>'")
    assert str(tmp_path) not in reason
    assert not marker.exists()


def test_shutdown_writes_are_blocked_and_fail(tmp_path: Path) -> None:
    marker = tmp_path / "at-exit.txt"
    register = f"import argparse, atexit\natexit.register(lambda: open({str(marker)!r}, 'w').close())\n"
    root = _tree(tmp_path, {"scripts/at_exit.py": GOOD.replace("import argparse\n", register, 1)})
    # A plain run of this --help prints compliant help, then writes the file on shutdown.
    done = subprocess.run([sys.executable, str(root / "scripts/at_exit.py"), "--help"], cwd=tmp_path,
                          capture_output=True, text=True, timeout=5)
    assert done.returncode == 0 and "Exit codes:" in done.stdout and marker.exists()
    marker.unlink()

    reason = lint.evaluate(root, "scripts/at_exit.py")
    assert reason == "side effect during --help: open '<path>'"
    assert not marker.exists()


def test_packages_absent_from_ci_are_refused_on_every_host(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/heavy.py": GOOD.replace("import argparse\n", "import argparse\nimport torch\n", 1)})
    reason = lint.evaluate(root, "scripts/heavy.py")
    assert reason is not None and "No module named 'torch' (not installed in CI)" in reason

    action = (lint.REPO_ROOT / ".github/actions/python-ci-env/action.yml").read_text(encoding="utf-8")
    [excluded] = re.findall(r"\^\(([\w|]+)\)==", action)
    assert set(excluded.split("|")) == set(lint.CI_ABSENT_IMPORTS)


def test_timeout_fails(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/slow.py": GOOD.replace("import argparse\n", "import argparse, time\ntime.sleep(3)\n", 1)})
    assert lint.probe(root, "scripts/slow.py", timeout=0.5) == [f"{lint.TIMEOUT_PREFIX} 0.5s"]


@pytest.mark.parametrize(
    ("parser", "expected"),
    [
        ({"to_stdout": True, "description": "", "epilog": "Examples: x\nExit codes: 0", "undocumented": []},
         ["missing description"]),
        ({"to_stdout": True, "description": "d", "epilog": "Examples: x", "undocumented": ["show"]},
         ["1 argument(s) without help: show", "epilog lacks Exit codes"]),
        ({"to_stdout": False, "description": "d", "epilog": "Examples: x\nExit codes: 0", "undocumented": []},
         ["help was not printed to stdout", "epilog lacks Examples and Exit codes"]),
    ],
)
def test_help_failures_name_each_gap(parser: dict, expected: list[str]) -> None:
    stdout = parser["epilog"] if parser["to_stdout"] else ""
    assert lint.help_failures({"events": [], "exit": 0, "error": "", "parser": parser}, stdout) == expected


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args],
        cwd=root, check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def test_baseline_may_only_shrink_against_merge_base(tmp_path: Path) -> None:
    root = _tree(tmp_path, {"scripts/a.py": BAD, "scripts/b.py": BAD})
    _git(root, "init", "-q", "-b", "main")
    baseline = _baseline(root, [_pin(root, "scripts/a.py")])
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    _git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    a, b = _pin(root, "scripts/a.py"), _pin(root, "scripts/b.py")
    rel = "scripts/hygiene/cli_help_baseline.json"

    assert lint.growth_violations(root, baseline, {"scripts/a.py": a}) == []
    assert lint.growth_violations(root, baseline, {}) == []
    assert lint.growth_violations(root, baseline, {"scripts/a.py": a, "scripts/b.py": b}) == [
        f"{rel}: baseline may only shrink; scripts/b.py is new or re-pinned against the merge base"]
    repinned = lint.Entry("scripts/a.py", "0" * 64, "frozen violator")
    assert lint.growth_violations(root, baseline, {"scripts/a.py": repinned}) == [
        f"{rel}: baseline may only shrink; scripts/a.py is new or re-pinned against the merge base"]

    _git(root, "update-ref", "-d", "refs/remotes/origin/main")
    [missing] = lint.growth_violations(root, baseline, {"scripts/a.py": a})
    assert "cannot verify shrink-only baseline" in missing


def test_analyze_dead_code_help_returns_before_analysis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = lint.REPO_ROOT / "scripts/tools/analyze_dead_code.py"
    done = subprocess.run([sys.executable, str(script), "--help"], cwd=tmp_path, capture_output=True,
                          text=True, timeout=5)
    assert done.returncode == 0, done.stderr
    assert "Examples:" in done.stdout and "Exit codes:" in done.stdout
    assert "Analyzing" not in done.stdout and list(tmp_path.iterdir()) == []

    monkeypatch.setattr(analyze_dead_code.DeadCodeAnalyzer, "analyze_all",
                        lambda self: pytest.fail("--help started the analysis"))
    with pytest.raises(SystemExit) as exc:
        analyze_dead_code.main(["--help"])
    assert exc.value.code == 0
    assert lint.evaluate(lint.REPO_ROOT, "scripts/tools/analyze_dead_code.py") is None


@pytest.mark.repo_wide
@pytest.mark.timeout(600)
def test_repository_clis_meet_help_standard_or_stay_frozen() -> None:
    """The gate: every scripts/ CLI passes or is a byte-identical entry, and the baseline only shrinks."""
    assert lint.find_violations() == []


@pytest.mark.slow
@pytest.mark.timeout(1800)
def test_no_frozen_entry_passes_through_a_changed_import() -> None:
    """Nightly: probe byte-identical entries too, so one fixed by a shared helper is reported stale."""
    assert lint.find_violations(check_growth=False, recheck_frozen=True) == []
