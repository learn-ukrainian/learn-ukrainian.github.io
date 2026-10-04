"""Quick-fix receipts are produced by real before/after runs and refuse ineligible evidence (#9719)."""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.review import quick_fix

REPOSITORY = "org/repo"
ISSUE = 42
BUGGY = "def add(a, b):\n    return a - b\n"
FIXED = "def add(a, b):\n    return a + b\n"
REGRESSION = "import calc\n\nassert calc.add(2, 3) == 5\n"
COMMAND = [sys.executable, "test_calc.py"]


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True, timeout=30)
    return completed.stdout.strip()


def make_repo(
    tmp_path: Path, *, fix: dict[str, str | None] | None = None, base_files: dict[str, str] | None = None
) -> tuple[Path, str, str]:
    """Commit a buggy base, then a head with the given changes; return (repo, base, head)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "quick-fix@example.invalid")
    _git(repo, "config", "user.name", "quick-fix test")
    (repo / ".gitignore").write_text("__pycache__/\n.worktrees/\n", encoding="utf-8")
    (repo / "calc.py").write_text(BUGGY, encoding="utf-8")
    (repo / "test_existing.py").write_text(REGRESSION, encoding="utf-8")
    for relative, content in (base_files or {}).items():
        (repo / relative).write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    for relative, content in (fix if fix is not None else {"calc.py": FIXED, "test_calc.py": REGRESSION}).items():
        path = repo / relative
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fix")
    head = _git(repo, "rev-parse", "HEAD")
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "fix-42"
    _git(repo, "worktree", "add", "-q", "-b", "codex/fix-42", str(worktree), head)
    return worktree, base, head


def record(repo: Path, base: str, **overrides):
    kwargs = {
        "repository": REPOSITORY,
        "issue": ISSUE,
        "base": base,
        "command": COMMAND,
        "test_paths": ["test_calc.py"],
        "author": "claude/fix-42",
        "driver": "codex-devops",
        "inspected_diff_sha256": quick_fix.diff_sha256(repo, base, _git(repo, "rev-parse", "HEAD")),
        "defect": "add() subtracts its operands",
        "qualification": "restores the documented addition; one bounded correction",
        "attest_no_exclusions": True,
        "sensitive_path_rationale": None,
        "now": "2026-10-04T22:00:00Z",
    }
    kwargs.update(overrides)
    return quick_fix.record_receipt(repo, **kwargs)


def write_reference(path: Path, receipt: dict) -> dict:
    digest = quick_fix.write_receipt(path, receipt)
    return {
        "receipt_path": str(path),
        "receipt_sha256": digest,
        "input_sha256": receipt["diff_sha256"],
        "target_sha": receipt["head_sha"],
    }


def _check(receipt: dict, **overrides) -> str | None:
    kwargs = {
        "repository": REPOSITORY,
        "issue": ISSUE,
        "head_sha": receipt["head_sha"],
        "input_sha256": receipt["diff_sha256"],
        "observed_paths": receipt["changed_paths"],
    }
    kwargs.update(overrides)
    return quick_fix.receipt_error(receipt, **kwargs)


def test_record_proves_reproduction_and_regression_and_restores_checkout(tmp_path: Path) -> None:
    repo, base, head = make_repo(tmp_path)

    receipt = record(repo, base)

    assert receipt["head_sha"] == head and receipt["base_sha"] == base
    assert receipt["reproduction"]["exit_code"] != 0
    assert "AssertionError" in receipt["reproduction"]["output_tail"]
    assert receipt["regression"]["exit_code"] == 0
    assert receipt["fix_paths"] == ["calc.py"] and receipt["regression_test_paths"] == ["test_calc.py"]
    assert receipt["driver"]["exclusions"] == dict.fromkeys(quick_fix.EXCLUSIONS, False)
    assert _check(receipt) is None
    assert _git(repo, "rev-parse", "HEAD") == head
    assert _git(repo, "status", "--porcelain") == ""
    assert (repo / "calc.py").read_text(encoding="utf-8") == FIXED


def test_record_reverts_added_fix_files_and_restores_them(tmp_path: Path) -> None:
    repo, base, _ = make_repo(
        tmp_path,
        fix={
            "calc.py": "from helper import plus as add\n",
            "helper.py": "def plus(a, b):\n    return a + b\n",
            "test_calc.py": REGRESSION,
        },
    )

    receipt = record(repo, base)

    assert receipt["fix_paths"] == ["calc.py", "helper.py"]
    assert receipt["reproduction"]["exit_code"] != 0
    assert (repo / "helper.py").is_file()
    assert _git(repo, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("fix", "overrides", "message"),
    (
        (None, {"attest_no_exclusions": False}, "attest"),
        (None, {"driver": "claude/fix-42"}, "not the author"),
        (None, {"command": []}, "regression command is required"),
        (None, {"inspected_diff_sha256": "0" * 64}, "inspected diff digest"),
        (None, {"test_paths": ["missing_test.py"]}, "regression test paths"),
        ({"test_calc.py": REGRESSION}, {}, "no correction beyond"),
        (
            {"calc.py": FIXED, "test_calc.py": REGRESSION, "scripts/review/gate.py": "X = 1\n"},
            {},
            "review/merge-authority",
        ),
        (
            {"calc.py": FIXED, "test_calc.py": REGRESSION, "scripts/lib/launch.sh": "echo ok\n"},
            {},
            "security-sensitive",
        ),
        ({"calc.py": BUGGY + "# touched\n", "test_calc.py": REGRESSION}, {}, "does not pass at the head"),
        ({"calc.py": FIXED, "test_calc.py": "import calc\n"}, {}, "does not reproduce"),
        (None, {"command": ["/nonexistent/quick-fix-command"]}, "not runnable"),
    ),
)
def test_record_refuses_ineligible_or_unproven_fixes(
    tmp_path: Path, fix: dict | None, overrides: dict, message: str
) -> None:
    repo, base, head = make_repo(tmp_path, fix=fix)

    with pytest.raises(quick_fix.QuickFixError, match=message):
        record(repo, base, **overrides)

    assert _git(repo, "rev-parse", "HEAD") == head
    assert _git(repo, "status", "--porcelain") == ""


def test_record_accepts_sensitive_path_only_with_driver_rationale(tmp_path: Path) -> None:
    repo, base, _ = make_repo(
        tmp_path, fix={"calc.py": FIXED, "test_calc.py": REGRESSION, "scripts/lib/launch.sh": "echo ok\n"}
    )

    receipt = record(repo, base, sensitive_path_rationale="argument plumbing only; no boundary moves")

    assert receipt["sensitive_paths"] == ["scripts/lib/launch.sh"]
    assert _check(receipt) is None
    without = deepcopy(receipt)
    without["sensitive_path_rationale"] = None
    assert "rationale" in str(_check(without))


def test_record_refuses_dirty_checkout_and_non_ancestor_base(tmp_path: Path) -> None:
    repo, base, head = make_repo(tmp_path)
    (repo / "calc.py").write_text(FIXED + "# local edit\n", encoding="utf-8")
    with pytest.raises(quick_fix.QuickFixError, match="not clean"):
        record(repo, base)
    _git(repo, "checkout", "-q", "--", "calc.py")

    with pytest.raises(quick_fix.QuickFixError, match="strict ancestor"):
        record(repo, head)


def test_policy_and_gate_paths_are_authority_but_ordinary_code_is_not() -> None:
    assert quick_fix.authority_paths(
        ["agents_extensions/shared/rules/core.md", "scripts/orchestration/task_lifecycle.py", "scripts/build/x.py"]
    ) == ["agents_extensions/shared/rules/core.md", "scripts/orchestration/task_lifecycle.py"]
    assert quick_fix.sensitive_paths(["scripts/launchers/codex.sh", "scripts/build/x.py"]) == [
        "scripts/launchers/codex.sh"
    ]


def test_timeout_is_refused_not_counted_as_reproduction(tmp_path: Path) -> None:
    with pytest.raises(quick_fix.QuickFixError, match="timeout proves nothing"):
        quick_fix._run_command([sys.executable, "-c", "import time; time.sleep(5)"], tmp_path, 0.2)


def _mutations() -> list[tuple[str, object]]:
    def set_path(*keys: str, value: object):
        def apply(receipt: dict) -> None:
            target = receipt
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value

        return apply

    def drop_exclusion(receipt: dict) -> None:
        del receipt["driver"]["exclusions"]["architecture"]

    def add_fix_path(path: str):
        def apply(receipt: dict) -> None:
            receipt["changed_paths"] = sorted([*receipt["changed_paths"], path])
            receipt["fix_paths"] = sorted([*receipt["fix_paths"], path])

        return apply

    return [
        ("not a quick-fix-receipt", set_path("schema_version", value="code-review-receipt.v1")),
        ("repository/issue", set_path("issue", value=7)),
        ("head SHA", set_path("head_sha", value="f" * 40)),
        ("diff digest does not match", set_path("diff_sha256", value="0" * 64)),
        ("base SHA is malformed", set_path("base_sha", value="main")),
        ("path lists are malformed", set_path("changed_paths", value="calc.py")),
        ("separate regression tests", set_path("fix_paths", value=[])),
        ("differ from the observed", add_fix_path("other.py")),
        ("authority paths", add_fix_path("scripts/publish/merge.py")),
        ("no regression command", set_path("command", value=[])),
        ("run records are malformed", set_path("regression", "output_sha256", value="x")),
        ("does not reproduce", set_path("reproduction", "exit_code", value=0)),
        ("does not reproduce", set_path("reproduction", "exit_code", value=127)),
        ("does not pass at the head", set_path("regression", "exit_code", value=1)),
        ("author/driver records are malformed", set_path("driver", value=["codex-devops"])),
        ("distinct from the author", set_path("driver", "agent", value="claude/fix-42")),
        ("did not inspect this exact diff", set_path("driver", "inspected_diff_sha256", value="0" * 64)),
        ("reproduced defect", set_path("driver", "qualification", value=" ")),
        ("every disqualifying", drop_exclusion),
        ("every disqualifying", set_path("driver", "exclusions", "credentials", value=True)),
    ]


@pytest.mark.parametrize(("message", "mutate"), _mutations())
def test_receipt_validation_refuses_tampered_or_incomplete_evidence(tmp_path: Path, message: str, mutate) -> None:
    repo, base, _ = make_repo(tmp_path)
    receipt = record(repo, base)
    expected = {"head_sha": receipt["head_sha"], "input_sha256": receipt["diff_sha256"]}
    mutate(receipt)

    error = _check(receipt, **expected, observed_paths=["calc.py", "test_calc.py"])

    assert error is not None and message in error


def test_cli_show_and_record_round_trip(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo, base, head = make_repo(tmp_path)
    assert quick_fix.main(["--repo-root", str(repo), "show", "--base", base]) == 0
    shown = capsys.readouterr().out
    digest = shown.rsplit("diff_sha256: ", 1)[1].strip()
    assert "+    return a + b" in shown and f"head_sha: {head}" in shown

    out = tmp_path / "receipts" / "quick-fix-42.json"
    argv = [
        "--repo-root", str(repo), "record", "--repository", REPOSITORY, "--issue", str(ISSUE),
        "--base", base, "--test-path", "test_calc.py",
        "--regression-command", shlex.join(COMMAND),
        "--author", "claude/fix-42", "--driver", "codex-devops", "--inspected-diff-sha256", digest,
        "--defect", "add() subtracts", "--qualification", "restores addition",
        "--attest-no-exclusions", "--out", str(out),
    ]  # fmt: skip
    assert quick_fix.main(argv) == 0
    reference = json.loads(capsys.readouterr().out)["quick_fix_receipt"]
    assert reference["target_sha"] == head and reference["input_sha256"] == digest
    assert reference["receipt_sha256"] == "sha256:" + hashlib.sha256(out.read_bytes()).hexdigest()

    assert quick_fix.main(argv) == 2, "an existing receipt is never overwritten"
    assert quick_fix.main([*argv[:-1], "relative.json"]) == 2
    assert "absolute" in capsys.readouterr().err


def test_cli_help_documents_examples_outputs_and_exit_codes() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.review.quick_fix", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0
    for term in ("Examples:", "Outputs:", "Exit codes:", "Related:", "workflow.md § Quick-fix path"):
        assert term in completed.stdout


def test_existing_unchanged_regression_proves_source_only_fix(tmp_path: Path) -> None:
    repo, base, _ = make_repo(tmp_path, fix={"calc.py": FIXED})
    receipt = record(repo, base, test_paths=["test_existing.py"], command=[sys.executable, "test_existing.py"])
    assert receipt["changed_paths"] == ["calc.py"]
    assert receipt["reproduction"]["exit_code"] == 1
    assert receipt["regression"]["exit_code"] == 0
    assert _check(receipt) is None


def test_test_only_correction_with_constant_external_probe(tmp_path: Path) -> None:
    # Deterministically model a test that accidentally depends on a scheduling detail.
    repo, base, _ = make_repo(
        tmp_path,
        base_files={"test_existing.py": "def check(values):\n    assert values['sync'] == 1\n"},
        fix={"test_existing.py": "def check(values):\n    assert values['async'] == 1\n"},
    )
    probe = tmp_path / "probe.py"
    probe.write_text("import runpy\nns = runpy.run_path('test_existing.py')\nns['check']({'async': 1})\n")
    original_probe = probe.read_bytes()
    receipt = record(
        repo,
        base,
        test_paths=["test_existing.py"],
        revert_test_paths=["test_existing.py"],
        command=[sys.executable, str(probe)],
    )
    assert receipt["changed_paths"] == receipt["fix_paths"] == receipt["reverted_test_paths"] == ["test_existing.py"]
    assert "KeyError: 'sync'" in receipt["reproduction"]["output_tail"]
    assert receipt["regression"]["exit_code"] == 0
    assert probe.read_bytes() == original_probe
    assert _check(receipt) is None
    malformed = deepcopy(receipt)
    malformed["reverted_test_paths"] = ["other.py"]
    assert "separate regression tests" in str(_check(malformed))
    malformed["reverted_test_paths"] = "test_existing.py"
    assert "malformed" in str(_check(malformed))


def test_primary_refusal_leaves_clean_primary_untouched(tmp_path: Path) -> None:
    _repo, base, head = make_repo(tmp_path)
    primary = tmp_path / "repo"
    before = (primary / "calc.py").read_bytes()
    with pytest.raises(quick_fix.QuickFixError, match="never the primary"):
        record(primary, base)
    assert (primary / "calc.py").read_bytes() == before
    assert _git(primary, "rev-parse", "HEAD") == head
    assert not _git(primary, "status", "--porcelain")


@pytest.mark.parametrize("target", ["calc.py", "test_existing.py", "new.txt"])
def test_reproduction_command_writes_are_preserved_and_refused(tmp_path: Path, target: str) -> None:
    repo, base, head = make_repo(tmp_path)
    command = [
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({target!r}).write_text('command edit'); raise SystemExit(1)",
    ]
    with pytest.raises(quick_fix.QuickFixError, match="changes left untouched"):
        record(repo, base, command=command)
    assert (repo / target).read_text() == "command edit"
    assert _git(repo, "rev-parse", "HEAD") == head
    if target != "calc.py":
        assert (repo / "calc.py").read_text() == FIXED


def test_reproduction_mode_change_is_preserved(tmp_path: Path) -> None:
    repo, base, _ = make_repo(tmp_path)
    command = [sys.executable, "-c", "from pathlib import Path; Path('calc.py').chmod(0o755); raise SystemExit(1)"]
    with pytest.raises(quick_fix.QuickFixError, match="changes left untouched"):
        record(repo, base, command=command)
    assert (repo / "calc.py").stat().st_mode & 0o111
    assert (repo / "calc.py").read_text() == BUGGY


def test_timeout_restores_only_owned_reversion(tmp_path: Path) -> None:
    repo, base, _ = make_repo(tmp_path)
    with pytest.raises(quick_fix.QuickFixError, match="timeout proves nothing"):
        record(repo, base, command=[sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
    assert (repo / "calc.py").read_text() == FIXED
    assert not _git(repo, "status", "--porcelain")


def test_moved_head_refuses_restoration_and_receipt(tmp_path: Path) -> None:
    repo, base, head = make_repo(tmp_path)
    command = ["git", "checkout", "--detach", base]
    with pytest.raises(quick_fix.QuickFixError, match="HEAD moved"):
        record(repo, base, command=command)
    assert _git(repo, "rev-parse", "HEAD") != head


def test_fixed_run_writes_are_preserved_and_refused(tmp_path: Path) -> None:
    repo, base, _ = make_repo(tmp_path)
    command = [
        sys.executable,
        "-c",
        "import calc; from pathlib import Path; "
        "Path('test_existing.py').write_text('command edit') if calc.add(2,3)==5 else None; "
        "raise SystemExit(0 if calc.add(2,3)==5 else 1)",
    ]
    with pytest.raises(quick_fix.QuickFixError, match="after the regression run"):
        record(repo, base, command=command)
    assert (repo / "test_existing.py").read_text() == "command edit"
    assert (repo / "calc.py").read_text() == FIXED


def test_bad_reverted_test_selection_is_refused(tmp_path: Path) -> None:
    repo, base, _ = make_repo(tmp_path)
    with pytest.raises(quick_fix.QuickFixError, match="changed files named"):
        record(repo, base, revert_test_paths=["calc.py"])
    with pytest.raises(quick_fix.QuickFixError, match="at least one"):
        record(repo, base, test_paths=[])
