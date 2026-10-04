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


def make_repo(tmp_path: Path, *, fix: dict[str, str | None] | None = None) -> tuple[Path, str, str]:
    """Commit a buggy base, then a head with the given changes; return (repo, base, head)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "quick-fix@example.invalid")
    _git(repo, "config", "user.name", "quick-fix test")
    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (repo / "calc.py").write_text(BUGGY, encoding="utf-8")
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
    return repo, base, _git(repo, "rev-parse", "HEAD")


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
