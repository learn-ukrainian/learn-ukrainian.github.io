"""A review attempt refuses when its sources server and prompt templates differ in content (#9163)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.agent_runtime.review_mcp import (
    REVIEW_CONTRACT_PATHS,
    ReviewContractError,
    check_review_contract,
    review_contract_digest,
)
from scripts.common.git_context import sanitized_git_env

SERVER_FILE = ".mcp/servers/sources/server.py"
TEMPLATE_FILE = "scripts/review/prompts/lesson-review.md.j2"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        env=sanitized_git_env(),
        timeout=30,
    )


@pytest.fixture
def checkouts(tmp_path: Path) -> tuple[Path, Path]:
    """A temporary primary checkout and one linked worktree at the same commit: ``(primary, worktree)``."""
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    _git(primary, "config", "user.email", "test@example.com")
    _git(primary, "config", "user.name", "Test")
    files = {
        ".gitignore": ".worktrees/\n__pycache__/\n",
        SERVER_FILE: "print('receipt: <id> (outcome: <value>)')\n",
        ".mcp/servers/sources/TOOL_RESULT_V1.md": "# tool result\n",
        TEMPLATE_FILE: "Copy the outcome printed beside each receipt.\n",
        "scripts/review/prompts/render.py": "RENDER = 1\n",
        "unrelated.txt": "one\n",
    }
    for name, text in files.items():
        (primary / name).parent.mkdir(parents=True, exist_ok=True)
        (primary / name).write_text(text, encoding="utf-8")
    _git(primary, "add", "--", *files)
    _git(primary, "commit", "-q", "-m", "init")
    worktree = primary / ".worktrees" / "dispatch" / "claude" / "task"
    _git(primary, "worktree", "add", "-q", "-b", "claude/task", str(worktree))
    return primary.resolve(), worktree.resolve()


def test_matched_checkouts_proceed_and_record_both_digests(checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts

    record = check_review_contract(worktree, server_checkout=primary)

    assert record["server_checkout"] == str(primary)
    assert record["prompt_checkout"] == str(worktree)
    assert record["server_digest"] == record["prompt_digest"]
    assert record["server_digest"].startswith("sha256:")
    assert record["paths"] == list(REVIEW_CONTRACT_PATHS)


def test_changed_server_file_in_primary_refuses_with_both_digests_and_the_fix(checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts
    # Uncommitted: a dirty tree must not hide the difference behind an unchanged commit.
    (primary / SERVER_FILE).write_text("print('receipt: <id>')\n", encoding="utf-8")
    server_digest = check_review_contract(primary, server_checkout=primary)["server_digest"]
    prompt_digest = check_review_contract(worktree, server_checkout=worktree)["server_digest"]

    with pytest.raises(ReviewContractError) as refused:
        check_review_contract(worktree, server_checkout=primary)

    message = str(refused.value)
    assert "review_contract_mismatch" in message
    assert "differ in .mcp/servers/sources\n" in message
    assert f"{primary} digest {server_digest}" in message
    assert f"{worktree} digest {prompt_digest}" in message
    assert server_digest != prompt_digest
    assert "pull the primary checkout to origin/main, then retry" in message


def test_changed_review_template_refuses(checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts
    (worktree / TEMPLATE_FILE).write_text("Copy the outcome the server prints.\n", encoding="utf-8")
    _git(worktree, "commit", "-q", "-am", "template change")

    with pytest.raises(ReviewContractError, match=r"differ in scripts/review/prompts\n"):
        check_review_contract(worktree, server_checkout=primary)


def test_new_untracked_template_refuses(checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts
    (worktree / "scripts/review/prompts/plan-review.md.j2").write_text("new\n", encoding="utf-8")

    with pytest.raises(ReviewContractError, match=r"scripts/review/prompts"):
        check_review_contract(worktree, server_checkout=primary)


def test_difference_outside_the_contract_paths_does_not_refuse(checkouts: tuple[Path, Path]) -> None:
    primary, worktree = checkouts
    (worktree / "unrelated.txt").write_text("two\n", encoding="utf-8")
    _git(worktree, "commit", "-q", "-am", "unrelated change")
    (primary / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
    # Ignored build output inside a contract path is not part of the contract either.
    (primary / ".mcp/servers/sources/__pycache__").mkdir()
    (primary / ".mcp/servers/sources/__pycache__/server.cpython-312.pyc").write_bytes(b"\x00bytecode")

    record = check_review_contract(worktree, server_checkout=primary)

    assert record["server_digest"] == record["prompt_digest"]


def test_digest_is_deterministic_and_sees_a_deleted_file(checkouts: tuple[Path, Path]) -> None:
    primary, _worktree = checkouts
    before = review_contract_digest(primary, ".mcp/servers/sources")
    assert review_contract_digest(primary, ".mcp/servers/sources") == before

    (primary / ".mcp/servers/sources/TOOL_RESULT_V1.md").unlink()

    assert review_contract_digest(primary, ".mcp/servers/sources") != before


def test_a_checkout_git_cannot_list_refuses_by_name(tmp_path: Path, checkouts: tuple[Path, Path]) -> None:
    not_a_repo = tmp_path / "plain"
    not_a_repo.mkdir()

    with pytest.raises(ReviewContractError, match=r"cannot list \.mcp/servers/sources in .*plain: git exited"):
        check_review_contract(checkouts[1], server_checkout=not_a_repo)
