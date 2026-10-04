"""Driver-verified quick-fix receipts for the operator-approved quick-fix path (#9719).

A quick fix restores existing approved behavior without a separate model review.
This module records the exact-head evidence that path requires — the inspected
diff, a regression command that fails with the fix reverted and passes at the
head, and the accountable driver's eligibility judgment — and validates such
receipts for the read-only lifecycle gate. Canonical contract:
``agents_extensions/shared/rules/workflow.md`` § Quick-fix path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any

from scripts.guardrails.worktree_containment import is_dispatch_worktree
from scripts.review.security_paths import is_security_sensitive_change

SCHEMA_VERSION = "quick-fix-receipt.v1"
EXCLUSIONS = (
    "credentials",
    "authorization",
    "permission_or_sandbox_enforcement",
    "security_boundary",
    "review_or_merge_authority",
    "destructive_behavior",
    "architecture",
    "material_uncertainty",
)
# Rules and the code that implements review, landing or this gate are policy and
# review/merge authority by construction; a change there always takes review.
AUTHORITY_PATHS = (
    ".github/workflows/**",
    "agents_extensions/shared/rules/**",
    "agents_extensions/shared/schemas/task-lifecycle.v1.schema.json",
    "scripts/review/**",
    "scripts/publish/**",
    "scripts/orchestration/task_lifecycle.py",
    "scripts/orchestration/task_closeout.py",
    "scripts/orchestration/merge_closeout.py",
)
# 126/127 mean the command never ran, which reproduces nothing.
NOT_RUNNABLE_EXIT_CODES = frozenset({126, 127})
OUTPUT_TAIL_CHARS = 4000
DEFAULT_TIMEOUT_SECONDS = 900.0
_SHA_RE = re.compile(r"[0-9a-f]{40}")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")


class QuickFixError(ValueError):
    """The quick-fix evidence is missing, stale, malformed or disqualified."""


def _git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False, timeout=120)


def _git_text(repo: Path, args: Sequence[str]) -> str:
    completed = _git(repo, args)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise QuickFixError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.decode("utf-8", "replace").strip()


def resolve_sha(repo: Path, ref: str) -> str:
    return _git_text(repo, ["rev-parse", "--verify", f"{ref}^{{commit}}"])


def exact_diff(repo: Path, base_sha: str, head_sha: str) -> bytes:
    completed = _git(
        repo,
        ["diff", "--no-ext-diff", "--no-color", "--no-renames", "--full-index", "--binary", base_sha, head_sha],
    )
    if completed.returncode != 0:
        raise QuickFixError("cannot compute the exact diff between base and head")
    return completed.stdout


def diff_sha256(repo: Path, base_sha: str, head_sha: str) -> str:
    return hashlib.sha256(exact_diff(repo, base_sha, head_sha)).hexdigest()


def changed_paths(repo: Path, base_sha: str, head_sha: str) -> list[str]:
    raw = _git_text(repo, ["diff", "--no-renames", "--name-only", "-z", base_sha, head_sha])
    return sorted(path for path in raw.split("\0") if path)


def authority_paths(paths: Iterable[str]) -> list[str]:
    return sorted(path for path in paths if any(fnmatchcase(path, pattern) for pattern in AUTHORITY_PATHS))


def sensitive_paths(paths: Iterable[str]) -> list[str]:
    return sorted(path for path in paths if is_security_sensitive_change([path]))


def _run_command(command: Sequence[str], cwd: Path, timeout: float) -> dict[str, Any]:
    # Both runs rewrite fix paths within the same second; bytecode cached by one
    # run (mtime + size match) must never stand in for the other's source.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise QuickFixError(f"regression command is not runnable: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise QuickFixError(f"regression command exceeded {timeout:g}s; a timeout proves nothing") from exc
    output = completed.stdout or b""
    return {
        "exit_code": completed.returncode,
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "output_tail": output.decode("utf-8", "replace")[-OUTPUT_TAIL_CHARS:],
    }


def _status(repo: Path) -> str:
    return _git_text(repo, ["status", "--porcelain", "--untracked-files=all"])


def _require_clean(repo: Path, head_sha: str, when: str) -> None:
    if resolve_sha(repo, "HEAD") != head_sha:
        raise QuickFixError(f"checkout HEAD moved {when}; nothing was restored or discarded")
    dirty = _status(repo)
    if dirty:
        raise QuickFixError(f"checkout is not clean {when}; changes left untouched: {' | '.join(dirty.splitlines())}")


def _require_dispatch_worktree(repo: Path) -> None:
    if not is_dispatch_worktree(repo):
        raise QuickFixError(
            "record runs only in a .worktrees/dispatch/<agent>/<task>/ checkout of the exact head, never the primary"
        )


def _blob(repo: Path, rev: str, path: str) -> str | None:
    completed = _git(repo, ["rev-parse", "--verify", "--quiet", f"{rev}:{path}"])
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("utf-8", "replace").strip()


def _holds(repo: Path, path: str, blob: str | None) -> bool:
    """True while ``path`` holds exactly ``blob`` (``None``: absent) in the working tree."""
    target = repo / path
    if blob is None:
        return not os.path.lexists(target)
    return target.is_file() and not target.is_symlink() and _git_text(repo, ["hash-object", "--", path]) == blob


def _restore_fix_paths(repo: Path, *, head_sha: str, reverted: Mapping[str, str | None]) -> None:
    """Put back only fix paths still holding exactly the reverted content; never discard anything else."""
    if resolve_sha(repo, "HEAD") != head_sha:
        raise QuickFixError("checkout HEAD moved during the reproduction run; fix paths were left reverted")
    ours = [path for path, blob in reverted.items() if _holds(repo, path, blob)]
    if ours:
        _git_text(repo, ["restore", f"--source={head_sha}", "--worktree", "--", *ours])
    _require_clean(repo, head_sha, "after the reproduction run")


def _run_without_fix(
    repo: Path, *, base_sha: str, head_sha: str, fix_paths: Sequence[str], command: Sequence[str], timeout: float
) -> dict[str, Any]:
    """Run the command with the fix paths at base and the regression tests at head.

    Only the working-tree copies of the fix paths change; the index stays at head. Afterwards a
    fix path is restored only while it still holds the reverted content, so tracked or untracked
    changes made by the command, or concurrently, are preserved and refuse the receipt.
    """
    reverted = {path: _blob(repo, base_sha, path) for path in fix_paths}
    at_base = [path for path, blob in reverted.items() if blob is not None]
    try:
        if at_base:
            _git_text(repo, ["restore", f"--source={base_sha}", "--worktree", "--", *at_base])
        for path, blob in reverted.items():
            if blob is None:
                (repo / path).unlink()
        outcome = _run_command(command, repo, timeout)
    except BaseException as exc:
        try:
            _restore_fix_paths(repo, head_sha=head_sha, reverted=reverted)
        except QuickFixError as restore_error:
            raise QuickFixError(f"{exc}; {restore_error}") from exc
        raise
    _restore_fix_paths(repo, head_sha=head_sha, reverted=reverted)
    return outcome


def _named_paths(command: Sequence[str]) -> set[str]:
    """Relative paths the command's arguments name directly (``path`` or ``path::node``)."""
    named = {Path(arg.split("::", 1)[0]).as_posix().removeprefix("./") for arg in command[1:]}
    return {path for path in named if not path.startswith("/")}


def _require_relative_repo_arguments(repo: Path, command: Sequence[str]) -> None:
    root = repo.resolve()
    for arg in command[1:]:
        candidate = Path(arg.split("::", 1)[0])
        if candidate.is_absolute() and candidate.resolve().is_relative_to(root):
            raise QuickFixError(f"name repository files in the regression command by relative path: {arg}")


def _split_regression(
    repo: Path, *, head_sha: str, paths: Sequence[str], test_paths: Sequence[str], command: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Return (regression tests held at head in both runs, fix paths reverted for the reproduction)."""
    tests = sorted({path.strip().removeprefix("./") for path in test_paths if path.strip()})
    if not tests:
        raise QuickFixError("at least one regression test path is required")
    missing = [
        path
        for path in tests
        if _git(repo, ["cat-file", "-t", f"{head_sha}:{path}"]).stdout.decode("utf-8", "replace").strip() != "blob"
    ]
    if missing:
        raise QuickFixError(f"regression test paths must be tracked files at the head: {', '.join(missing)}")
    _require_relative_repo_arguments(repo, command)
    fix_paths = [path for path in paths if path not in tests]
    error = _regression_split_error(command, tests, fix_paths)
    if error:
        raise QuickFixError(error)
    return tests, fix_paths


def _regression_split_error(command: Sequence[str], tests: Sequence[str], fix_paths: Sequence[str]) -> str | None:
    """Why the held regression cannot isolate the reverted fix, or ``None``."""
    named = _named_paths(command)
    unnamed = [path for path in tests if path not in named]
    if unnamed:
        return f"the regression command must name each regression test path: {', '.join(unnamed)}"
    if not fix_paths:
        return "the proof cannot distinguish the correction: every changed path is a regression test held at head"
    run_fix = sorted(set(fix_paths) & named)
    if run_fix:
        return (
            "the regression command runs changed fix paths directly, so the proof cannot distinguish the "
            f"correction from the check: {', '.join(run_fix)}"
        )
    return None


def record_receipt(
    repo: Path,
    *,
    repository: str,
    issue: int,
    base: str,
    command: Sequence[str],
    test_paths: Sequence[str],
    author: str,
    driver: str,
    inspected_diff_sha256: str,
    defect: str,
    qualification: str,
    attest_no_exclusions: bool,
    sensitive_path_rationale: str | None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    now: str | None = None,
) -> dict[str, Any]:
    """Run the reproduction and regression at the exact head and build a receipt."""
    if not attest_no_exclusions:
        raise QuickFixError("the driver must attest that no excluded change category applies")
    author, driver = author.strip(), driver.strip()
    if not author or not driver or author == driver:
        raise QuickFixError("the accountable driver, not the author, decides quick-fix eligibility")
    if not command:
        raise QuickFixError("a regression command is required")
    _require_dispatch_worktree(repo)
    head_sha = resolve_sha(repo, "HEAD")
    _require_clean(repo, head_sha, "before recording")
    base_sha = resolve_sha(repo, base)
    if base_sha == head_sha or _git(repo, ["merge-base", "--is-ancestor", base_sha, head_sha]).returncode != 0:
        raise QuickFixError("base must be a strict ancestor of the head")
    digest = diff_sha256(repo, base_sha, head_sha)
    if inspected_diff_sha256 != digest:
        raise QuickFixError("driver-inspected diff digest does not match the exact base..head diff")
    paths = changed_paths(repo, base_sha, head_sha)
    tests, fix_paths = _split_regression(repo, head_sha=head_sha, paths=paths, test_paths=test_paths, command=command)
    authority = authority_paths(paths)
    if authority:
        raise QuickFixError(f"review/merge-authority paths require independent review: {', '.join(authority)}")
    sensitive = sensitive_paths(paths)
    rationale = " ".join((sensitive_path_rationale or "").split()) or None
    if sensitive and not rationale:
        raise QuickFixError(
            "security-sensitive paths changed; record why the actual change alters no authority boundary: "
            + ", ".join(sensitive)
        )
    reproduction = _run_without_fix(
        repo, base_sha=base_sha, head_sha=head_sha, fix_paths=fix_paths, command=command, timeout=timeout
    )
    regression = _run_command(command, repo, timeout)
    _require_clean(repo, head_sha, "after the regression run")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "repository": repository,
        "issue": issue,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "diff_sha256": digest,
        "changed_paths": paths,
        "regression_test_paths": tests,
        "fix_paths": fix_paths,
        "sensitive_paths": sensitive,
        "sensitive_path_rationale": rationale,
        "command": list(command),
        "reproduction": reproduction,
        "regression": regression,
        "author": {"agent": author},
        "driver": {
            "agent": driver,
            "inspected_diff_sha256": inspected_diff_sha256,
            "defect": " ".join(defect.split()),
            "qualification": " ".join(qualification.split()),
            "exclusions": dict.fromkeys(EXCLUSIONS, False),
        },
        "recorded_at": now or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    error = receipt_error(
        receipt, repository=repository, issue=issue, head_sha=head_sha, input_sha256=digest, observed_paths=paths
    )
    if error:
        raise QuickFixError(error)
    return receipt


def receipt_error(
    receipt: Any,
    *,
    repository: str,
    issue: int,
    head_sha: str,
    input_sha256: str,
    observed_paths: Sequence[str] | None = None,
) -> str | None:
    """Return why a receipt cannot carry the quick-fix gate, or ``None``."""
    if not isinstance(receipt, Mapping) or receipt.get("schema_version") != SCHEMA_VERSION:
        return "quick-fix reference is not a quick-fix-receipt.v1 receipt"
    if receipt.get("repository") != repository or receipt.get("issue") != issue:
        return "quick-fix receipt repository/issue does not match the task identity"
    if receipt.get("head_sha") != head_sha:
        return "quick-fix receipt head SHA does not match the evidence reference"
    if receipt.get("diff_sha256") != input_sha256:
        return "quick-fix receipt diff digest does not match the evidence reference"
    base_sha = receipt.get("base_sha")
    if not isinstance(base_sha, str) or not _SHA_RE.fullmatch(base_sha) or base_sha == head_sha:
        return "quick-fix receipt base SHA is malformed"
    paths = receipt.get("changed_paths")
    tests = receipt.get("regression_test_paths")
    fixes = receipt.get("fix_paths")
    if not all(isinstance(value, list) and all(isinstance(p, str) for p in value) for value in (paths, tests, fixes)):
        return "quick-fix receipt path lists are malformed"
    if not tests or not fixes or sorted(set(paths) - set(tests)) != fixes:
        return "quick-fix receipt does not separate regression tests from a non-empty fix"
    authority = authority_paths(paths)
    if authority:
        return f"quick-fix receipt changes review/merge-authority paths: {', '.join(authority)}"
    if sensitive_paths(paths) and not str(receipt.get("sensitive_path_rationale") or "").strip():
        return "quick-fix receipt changes security-sensitive paths without the driver's rationale"
    if observed_paths and sorted(set(observed_paths)) != sorted(set(paths)):
        return "quick-fix receipt changed paths differ from the observed PR diff"
    command = receipt.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(arg, str) and arg for arg in command):
        return "quick-fix receipt has no regression command"
    split_error = _regression_split_error(command, tests, fixes)
    if split_error:
        return f"quick-fix receipt: {split_error}"
    runs = (receipt.get("reproduction"), receipt.get("regression"))
    if not all(
        isinstance(run, Mapping)
        and isinstance(run.get("exit_code"), int)
        and _HEX64_RE.fullmatch(str(run.get("output_sha256") or ""))
        for run in runs
    ):
        return "quick-fix receipt run records are malformed"
    reproduction, regression = runs
    if reproduction["exit_code"] == 0 or reproduction["exit_code"] in NOT_RUNNABLE_EXIT_CODES:
        return "quick-fix receipt does not reproduce the defect with the fix reverted"
    if regression["exit_code"] != 0:
        return "quick-fix receipt regression command does not pass at the head"
    author = receipt.get("author") or {}
    driver = receipt.get("driver") or {}
    if not isinstance(author, Mapping) or not isinstance(driver, Mapping):
        return "quick-fix receipt author/driver records are malformed"
    author_agent = str(author.get("agent") or "").strip()
    driver_agent = str(driver.get("agent") or "").strip()
    if not author_agent or not driver_agent or author_agent == driver_agent:
        return "quick-fix receipt lacks an accountable driver distinct from the author"
    if driver.get("inspected_diff_sha256") != input_sha256:
        return "quick-fix receipt driver did not inspect this exact diff"
    if not str(driver.get("defect") or "").strip() or not str(driver.get("qualification") or "").strip():
        return "quick-fix receipt lacks the reproduced defect or the driver's qualification"
    if driver.get("exclusions") != dict.fromkeys(EXCLUSIONS, False):
        return "quick-fix receipt does not exclude every disqualifying change category"
    return None


def write_receipt(path: Path, receipt: Mapping[str, Any]) -> str:
    """Write the receipt once and return its ``sha256:`` file digest."""
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def cmd_show(args: argparse.Namespace) -> int:
    repo = args.repo_root
    base_sha, head_sha = resolve_sha(repo, args.base), resolve_sha(repo, args.head)
    diff = exact_diff(repo, base_sha, head_sha)
    sys.stdout.write(diff.decode("utf-8", "replace"))
    print(f"\nbase_sha: {base_sha}\nhead_sha: {head_sha}\ndiff_sha256: {hashlib.sha256(diff).hexdigest()}")
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    if not out.is_absolute():
        raise QuickFixError("--out must be an absolute path")
    receipt = record_receipt(
        args.repo_root,
        repository=args.repository,
        issue=args.issue,
        base=args.base,
        command=shlex.split(args.regression_command),
        test_paths=args.test_path,
        author=args.author,
        driver=args.driver,
        inspected_diff_sha256=args.inspected_diff_sha256,
        defect=args.defect,
        qualification=args.qualification,
        attest_no_exclusions=args.attest_no_exclusions,
        sensitive_path_rationale=args.sensitive_path_rationale,
        timeout=args.timeout,
    )
    receipt_sha256 = write_receipt(out, receipt)
    reference = {
        "receipt_path": str(out),
        "receipt_sha256": receipt_sha256,
        "input_sha256": receipt["diff_sha256"],
        "target_sha": receipt["head_sha"],
    }
    print(json.dumps({"quick_fix_receipt": reference}, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Record exact-head evidence for a driver-verified quick fix (no separate model review).\n"
            "Use only for a reproduced repair of existing approved behavior; authority, security and "
            "architecture changes take independent review."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.review.quick_fix show --base origin/main
  .venv/bin/python -m scripts.review.quick_fix record --repository owner/repo --issue 9712 \\
      --base origin/main --test-path tests/test_x.py \\
      --regression-command '.venv/bin/python -m pytest tests/test_x.py -q' \\
      --author claude/fix-9712 --driver codex-devops --inspected-diff-sha256 <hex from show> \\
      --defect 'launcher drops the stream' --qualification 'restores the documented argument' \\
      --attest-no-exclusions --out /abs/path/quick-fix-9712.json

Run record from a clean .worktrees/dispatch/<agent>/<task>/ checkout of the exact head, never the
primary. Regression test paths are tracked files at HEAD (new, changed or pre-existing) named by
relative path in the command; they stay at HEAD in both runs, so the fix must lie elsewhere.

Outputs: show prints the exact diff and its digest. record runs the regression command with the
working-tree copies of the fix paths reverted to base (must fail) and at HEAD (must pass), then
restores only fix paths still holding the reverted content; any other change, by the command or
concurrently, is left in place and refuses the receipt. It writes the receipt once and prints the
task_closeout add-evidence --details reference.
Exit codes: 0 success; 2 refused (primary, dirty or moved checkout, digest mismatch, missing
reproduction, failing regression, unisolated regression, changed files, authority paths or missing
attestation).
Related: agents_extensions/shared/rules/workflow.md § Quick-fix path, #9719""",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Checkout of the exact head (default: cwd).")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show", help="Print the exact base..head diff and its sha256 for driver inspection.")
    show.add_argument("--base", default="origin/main", help="Base ref (default: origin/main).")
    show.add_argument("--head", default="HEAD", help="Head ref (default: HEAD).")
    show.set_defaults(func=cmd_show)

    record = sub.add_parser("record", help="Run reproduction and regression at the exact head and write a receipt.")
    record.add_argument("--repository", required=True, help="GitHub owner/repo of the task identity.")
    record.add_argument("--issue", type=int, required=True, help="Issue number of the task identity.")
    record.add_argument(
        "--base", default="origin/main", help="Base ref the fix is measured against (default: origin/main)."
    )
    record.add_argument(
        "--test-path",
        action="append",
        required=True,
        help="Regression test file held at HEAD in both runs (new, changed or pre-existing); repeat for several.",
    )
    record.add_argument(
        "--regression-command",
        required=True,
        help="Command run without a shell that names each --test-path, e.g. '.venv/bin/python -m pytest t.py'.",
    )
    record.add_argument("--author", required=True, help="Authoring agent/task id.")
    record.add_argument("--driver", required=True, help="Accountable driver agent id; must differ from --author.")
    record.add_argument(
        "--inspected-diff-sha256", required=True, help="diff_sha256 printed by `show` after inspection."
    )
    record.add_argument("--defect", required=True, help="The concrete reproduced defect.")
    record.add_argument("--qualification", required=True, help="Why the actual change qualifies as a quick fix.")
    record.add_argument(
        "--attest-no-exclusions",
        action="store_true",
        help="Driver attests no credential, authorization, sandbox, security-boundary, review/merge-authority, "
        "destructive, architecture or material-uncertainty change.",
    )
    record.add_argument(
        "--sensitive-path-rationale", help="Required when security-sensitive paths change: why no boundary moves."
    )
    record.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Per-run timeout seconds (default: 900)."
    )
    record.add_argument("--out", required=True, help="Absolute receipt path; existing files are never overwritten.")
    record.set_defaults(func=cmd_record)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (QuickFixError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
