"""End-to-end contract tests for the non-blocking primary-ref audit hook."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HOOKS_DIRECTORY = REPOSITORY_ROOT / ".githooks"


def run_git(repository: Path, *arguments: str, hooks_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = ["git"]
    if hooks_path is not None:
        command.extend(["-c", f"core.hooksPath={hooks_path}"])
    command.extend(arguments)
    return subprocess.run(command, cwd=repository, check=True, capture_output=True, text=True)


def initialise_repository(tmp_path: Path) -> tuple[Path, str, str]:
    repository = tmp_path / "primary"
    repository.mkdir()
    run_git(repository, "init")
    run_git(repository, "config", "user.name", "Tripwire Test")
    run_git(repository, "config", "user.email", "tripwire@example.test")

    fixture = repository / "fixture.txt"
    fixture.write_text("first\n", encoding="utf-8")
    run_git(repository, "add", "fixture.txt")
    run_git(repository, "commit", "-m", "first")
    first = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    fixture.write_text("second\n", encoding="utf-8")
    run_git(repository, "commit", "-am", "second")
    second = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    run_git(repository, "update-ref", "refs/heads/audit-target", first)
    run_git(repository, "config", "core.hooksPath", str(HOOKS_DIRECTORY))
    return repository, first, second


def audit_records(repository: Path) -> list[dict[str, object]]:
    audit_file = repository / ".agent" / "primary-ref-audit.jsonl"
    return [json.loads(line) for line in audit_file.read_text(encoding="utf-8").splitlines()]


def test_committed_primary_branch_update_is_recorded(tmp_path: Path) -> None:
    repository, first, second = initialise_repository(tmp_path)

    run_git(repository, "update-ref", "refs/heads/audit-target", second, first)

    record = next(record for record in audit_records(repository) if record["ref"] == "refs/heads/audit-target")
    assert record["old"] == first
    assert record["new"] == second
    assert record["cwd"] == str(repository)
    assert record["pid"]
    assert record["argv"]


def test_nul_delimited_payload_is_recorded(tmp_path: Path) -> None:
    repository, first, second = initialise_repository(tmp_path)
    hook = HOOKS_DIRECTORY / "reference-transaction"

    subprocess.run(
        [str(hook), "committed"],
        cwd=repository,
        check=True,
        input=f"{first} {second} refs/heads/nul-payload\0",
        text=True,
        env=os.environ.copy(),
    )

    record = next(record for record in audit_records(repository) if record["ref"] == "refs/heads/nul-payload")
    assert record["old"] == first
    assert record["new"] == second


def test_log_write_failure_does_not_block_a_ref_update(tmp_path: Path) -> None:
    repository, first, second = initialise_repository(tmp_path)
    (repository / ".agent").write_text("not a directory\n", encoding="utf-8")

    run_git(repository, "update-ref", "refs/heads/audit-target", second, first)

    assert run_git(repository, "rev-parse", "refs/heads/audit-target").stdout.strip() == second


def test_linked_worktree_update_is_not_recorded(tmp_path: Path) -> None:
    repository, first, second = initialise_repository(tmp_path)
    linked_worktree = tmp_path / "linked-worktree"
    run_git(
        repository,
        "worktree",
        "add",
        "--detach",
        str(linked_worktree),
        second,
        hooks_path=Path("/dev/null"),
    )

    audit_file = repository / ".agent" / "primary-ref-audit.jsonl"
    audit_file.unlink(missing_ok=True)
    run_git(linked_worktree, "update-ref", "refs/heads/audit-target", second, first)

    assert not audit_file.exists()
    assert run_git(repository, "rev-parse", "refs/heads/audit-target").stdout.strip() == second


def test_hooks_path_bypass_succeeds_without_an_audit_record(tmp_path: Path) -> None:
    repository, first, second = initialise_repository(tmp_path)

    run_git(repository, "update-ref", "refs/heads/audit-target", second, first, hooks_path=Path("/dev/null"))

    assert not (repository / ".agent" / "primary-ref-audit.jsonl").exists()
