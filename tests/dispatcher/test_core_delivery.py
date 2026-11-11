"""Trusted rules at the final ordinary-launch boundary, without provider requests."""

import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.dispatcher import runtime_context
from scripts.dispatcher.providers import PROVIDERS, agy
from scripts.dispatcher.types import TaskSpec
from scripts.lib import rules_core


def spec_at(tmp_path, provider):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    brief = tmp_path / "brief"
    brief.write_bytes(b"Original brief\r\n")
    return TaskSpec("delivery", provider, "gpt-6.1-sol", "high", "workspace-write", checkout, brief, tmp_path / "result")


@pytest.mark.parametrize("provider", PROVIDERS)
def test_missing_core_refuses_before_adapter_side_effects(tmp_path, monkeypatch, provider):
    """Defect class: missing trusted rules permit schema/file creation or provider launch."""
    spec = spec_at(tmp_path, provider)
    missing = tmp_path / "missing-rules"
    monkeypatch.setenv("LEARN_UKRAINIAN_RULES_DIR", str(missing))
    adapter = Mock()
    monkeypatch.setattr(runtime_context.providers, "load", adapter)
    before = sorted(tmp_path.rglob("*"))
    with pytest.raises(rules_core.RulesCoreMissing):
        runtime_context.build(spec, {})
    adapter.assert_not_called()
    assert sorted(tmp_path.rglob("*")) == before


def test_correction_launch_prepares_core_after_selecting_final_prompt(tmp_path):
    """Defect class: a fresh correction launch overwrites its already-prepared rules context."""
    spec = spec_at(tmp_path, "cursor")
    correction = b"Keep the same verdict.\nPrevious reply: valid finding.\r\n"
    invocation = runtime_context.build(spec, {}, launch_prompt=correction)
    assert invocation.stdin.startswith(rules_core.core_block().encode())
    assert invocation.stdin.endswith(correction)
    assert b"Original brief" not in invocation.stdin
    assert spec.prompt_file.read_bytes() == b"Original brief\r\n"
    assert "--force" in invocation.argv


def test_continuation_keeps_conversation_and_refreshes_core_after_selection(tmp_path):
    """Defect class: AGY resume drops machinery rules when it substitutes the continuation turn."""
    spec = spec_at(tmp_path, "agy")
    first = runtime_context.build(spec, {})
    resumed = runtime_context.build(spec, {}, conversation="existing-conversation")
    first_message = json.loads(first.stdin)["message"]["content"][0]["text"]
    next_message = json.loads(resumed.stdin)["message"]["content"][0]["text"]
    assert "--conversation=existing-conversation" in resumed.argv
    assert next_message.startswith(rules_core.core_block())
    assert next_message.endswith(agy._CONTINUE_TEXT)
    assert "Original brief" in first_message and "Original brief" not in next_message
    # The native continuation selects the original conversation; the new turn retains
    # that history by id and resends current trusted rules, not the original task.
    assert [arg for arg in resumed.argv if arg != "--conversation=existing-conversation"] == first.argv
    assert spec.prompt_file.read_bytes() == b"Original brief\r\n"
    binary = tmp_path / "agy"
    binary.write_text(f"#!{sys.executable}\n" + r'''
import json,os,pathlib,sys
state = pathlib.Path(os.environ["CAPTURE"])
history = json.loads(state.read_text()) if state.exists() else []
if history:
    assert "--conversation=existing-conversation" in sys.argv
history.append(json.loads(sys.stdin.read())["message"]["content"][0]["text"])
state.write_text(json.dumps(history))
print(json.dumps(history))
''')
    binary.chmod(0o755)
    env = {"PATH": str(tmp_path) + os.pathsep + os.defpath, "CAPTURE": str(tmp_path / "history")}
    for invocation in (first, resumed):
        captured = subprocess.run(invocation.argv, input=invocation.stdin, env=env, cwd=spec.worktree,
                                  capture_output=True, timeout=10)
        assert captured.returncode == 0, captured.stderr.decode()
    assert json.loads(captured.stdout) == [first_message, next_message]


def test_launch_reads_current_core_instead_of_preflight_snapshot(tmp_path, monkeypatch):
    """Defect class: a changed or removed core after preflight launches stale instructions."""
    spec = replace(spec_at(tmp_path, "muse"), mode="read-only")
    source = tmp_path / "rules" / "core.md"
    source.parent.mkdir()
    source.write_text("First trusted core\n")
    monkeypatch.setenv("LEARN_UKRAINIAN_RULES_DIR", str(source.parent))
    rules_core.require_core()
    source.write_text("Current trusted core\n")
    invocation = runtime_context.build(spec, {})
    launch_file = Path(invocation.argv[invocation.argv.index("--prompt-file") + 1])
    assert "Current trusted core" in launch_file.read_text()
    assert "First trusted core" not in launch_file.read_text()
    source.write_text("")
    prior = launch_file.read_bytes()
    with pytest.raises(rules_core.RulesCoreMissing):
        runtime_context.build(spec, {})
    assert launch_file.read_bytes() == prior


def test_dispatch_uses_preflight_content_seat_despite_sanitized_child_environment(tmp_path, monkeypatch):
    """Defect class: sanitizing provider env silently downgrades the preflight's content seat."""
    from scripts.common.repo_root import PRODUCT_MARKER
    from scripts.dispatcher.environment import child_env

    spec = spec_at(tmp_path, "cursor")
    marker = tmp_path / PRODUCT_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("product fixture\n")
    addendum = tmp_path / rules_core.CONTENT_ADDENDUM_REL
    addendum.parent.mkdir(parents=True)
    addendum.write_text("Content-seat trusted addendum\n")
    monkeypatch.setenv("LU_PRODUCT_ROOT", str(tmp_path))
    monkeypatch.setenv("LU_RULES_SEAT", "content")
    assert rules_core.require_core() == "content"
    env = child_env(spec)
    assert "LU_RULES_SEAT" not in env
    invocation = runtime_context.build(spec, env)
    assert invocation.stdin.startswith(rules_core.core_block("content").encode())
    assert b"Content-seat trusted addendum" in invocation.stdin


@pytest.mark.parametrize("provider", PROVIDERS)
def test_dry_run_constructs_context_transport_without_writes(tmp_path, provider):
    """Defect class: planning a file-backed core transport writes files or requires a task directory."""
    spec = spec_at(tmp_path, provider)
    if provider == "muse":
        spec = replace(spec, mode="read-only")
    spec = replace(spec, final_file=tmp_path / "absent-tasks" / "result", options={"dry_run": "True"})
    before = sorted(tmp_path.rglob("*"))
    invocation = runtime_context.build(spec, {})
    assert sorted(tmp_path.rglob("*")) == before
    if provider == "claude":
        assert "--append-system-prompt-file" in invocation.argv
    if provider == "muse":
        assert "--prompt-file" in invocation.argv
