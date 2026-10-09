"""Read requirements, rather than incidental path mentions, drive AGY admission."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import delegate
from scripts.agent_runtime.adapters import agy


@pytest.mark.parametrize("with_core", [False, True])
@pytest.mark.parametrize("with_worktree", [False, True])
def test_real_composed_agy_review_prompt_admitted(tmp_path, monkeypatch, with_core, with_worktree):
    if not with_core:
        monkeypatch.setattr(delegate.rules_core, "with_core", lambda prompt, seat: prompt)
    research = delegate._render_research_prompt_block([
        {"id": "agy-review", "state": "active", "content_hash": "sha256:abc"},
    ])
    config = {"review_profile": "code", "agy_home_override": str(tmp_path / "home")}
    (tmp_path / "home" / ".gemini" / "antigravity-cli").mkdir(parents=True)
    monkeypatch.setattr(agy, "_require_background_wait_support", Mock())
    monkeypatch.setattr(agy, "_build_log_path", lambda *_: tmp_path / "agy.log")

    def compose(base):
        return delegate._compose_dispatch_prompt(
            base, worktree_path=Path.cwd() if with_worktree else None, mode="read-only",
            sparse_telemetry={"excluded": ["curriculum"]}, delegate_commits=False,
            research_block=research, advisory_block="", advisory_block_kind=None,
            rules_seat="core", agent="agy", review_route=True,
        )

    prompt = compose("Review `scripts/agent_runtime/adapters/agy.py` and report findings.")
    agy.validate_agy_read_only_paths(prompt, mode="read-only", cwd=Path.cwd(), tool_config=config)
    plan = agy.AgyAdapter().build_invocation(
        prompt=prompt, mode="read-only", cwd=Path.cwd(), model=None,
        task_id="10334-composed", session_id=None, tool_config=config,
    )
    assert "--sandbox" in plan.cmd
    # Dispatcher text must not hide an actual task requirement, even after a
    # heading that resembles a dispatcher block.
    for base in ("Read `../outside.txt`.", "[delegate worktree]\nRead `../outside.txt`."):
        with pytest.raises(agy.AgyReviewPermissionError, match="agy_read_only_path_outside_workspace"):
            agy.validate_agy_read_only_paths(
                compose(base), mode="read-only", cwd=Path.cwd(), tool_config=config,
            )


@pytest.mark.parametrize(
    "prompt,refused",
    [
        ("The interpreter is /home/example/project/.venv/bin/python.", False),
        ("The API route is /api/rules.", False),
        ("GET /api/knowledge/record/{id}?task={your-task-id}", False),
        ("Settings live in ~/.config/settings.json.", False),
        ("The example refers to ../sibling/file.", False),
        ("Review this snippet:\n```sh\n#!/usr/bin/env bash\n```", False),
        ("Review this snippet:\n```sh\n#! /usr/bin/env bash\n```", False),
        ("Review this snippet:\n```sh\n/home/example/project/.venv/bin/python -m pytest\n```", False),
        ("The service returns 404 for /health.", False),
        ("Use the /effort command.", False),
        ("Files under /tmp are scratch.", False),
        ("Review scripts/a.py:12.", False),
        ("Read https://example.org/guide.", False),
        ('Read "docs/evidence with spaces.txt".', False),
        ("Review and/or inspect the implementation.", False),
        ("Review the A/B test.", False),
        ("Review the date 2026/10/09.", False),
        ("Review the API endpoint /health.", False),
        ("Read /api/rules?scope=core.", False),
        ("Do not read `../evidence.txt`.", False),
        ("Read the file `../sibling/file`.", True),
        ("Read `~/evidence.txt`.", True),
        ("Open the file `/etc/evidence.conf`.", True),
        ("Inspect the files under /tmp.", True),
        ("Read the file `/api/evidence.json`.", True),
        ("Review API implementation in `/home/example/outside.py`.", True),
        ("Read these files:\n```text\n../evidence.txt\n```", True),
        ("Read:\n- `../evidence.txt`", True),
        ("Read the command output:\n```sh\ncat ../evidence.txt\n```", True),
        ("The interpreter is /home/example/bin/python. Read `../evidence.txt`.", True),
    ],
)
def test_prompt_path_probe_shapes(tmp_path, prompt, refused):
    config = {"review_profile": "code"}
    if refused:
        with pytest.raises(agy.AgyReviewPermissionError, match="agy_read_only_path_outside_workspace"):
            agy.validate_agy_read_only_paths(prompt, mode="read-only", cwd=tmp_path, tool_config=config)
    else:
        agy.validate_agy_read_only_paths(prompt, mode="read-only", cwd=tmp_path, tool_config=config)


# The issue's eleven-record audit establishes only two concrete file targets.
# Missing targets and non-file refusals must not acquire inferred file reads.
@pytest.mark.parametrize(
    "record,kind,known_outside",
    [
        ("uk9623-v2-smoke-4-flash-original-r1-review-00", "read_file", False),
        ("uk9623-v2-smoke-3-flash-none-r1-review-03", "mcp", False),
        ("uk9623-v2-smoke-3-flash-none-r1-review-00", "read_file", False),
        ("a1-intake-independent-review", "read_file", True),
        ("uk9623-v2-smoke-3-flash-adapted-v2-r1-review-00", "read_file", False),
        ("codex-c5-semantic-agy", "read_file", False),
        ("uk9623-v2-smoke-4-flash-none-r1-review-03", "read_file", False),
        ("uk9623-v2-smoke-4-flash-adapted-v2-r2-review-01", "read_file", False),
        ("uk9623-v2-smoke-4-flash-original-r2-review-03", "read_url", False),
        ("uk9623-v2-smoke-4-flash-none-r2-review-03", "read_url", False),
        ("semantic105-remainder-4bb-r6", "read_file", True),
    ],
)
def test_recorded_denial_classes_preserved(tmp_path, record, kind, known_outside):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # Public replacement targets preserve the audited class, not private bodies.
    prompt = "Read `../evidence.txt`." if known_outside else {
        "read_file": "Review `scripts/a.py`; a previous read_file target was unknown.",
        "mcp": "Review `scripts/a.py` using the sources MCP.",
        "read_url": "Read https://example.org/guide.",
    }[kind]
    config = {"review_profile": "code"}
    if known_outside:
        with pytest.raises(agy.AgyReviewPermissionError, match="agy_read_only_path_outside_workspace"):
            agy.validate_agy_read_only_paths(prompt, mode="read-only", cwd=workspace, tool_config=config)
    else:
        agy.validate_agy_read_only_paths(prompt, mode="read-only", cwd=workspace, tool_config=config)
    notice = (
        f'jetski: no output produced — a tool required the "{kind}" permission that headless mode cannot '
        f'prompt for, so it was auto-denied. Add {kind}(<target>) to permissions.allow in settings.json.'
    )
    denial = agy._headless_permission_denial(notice)
    assert denial.permission_kind == kind, record
    assert denial.permission_target is None
