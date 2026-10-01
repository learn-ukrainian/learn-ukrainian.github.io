"""Opt-in authenticated negative probes for the full read-only OS boundary."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys

import pytest
import yaml

from scripts.agent_runtime import runner
from scripts.agent_runtime.review_mcp import prepare_review_attempt
from tests.agent_runtime.test_attempt_boundary import manifest_world


@pytest.mark.skipif(os.environ.get("LU_FULL_REVIEW_REAL_PROBES") != "1", reason="authenticated host probes are opt-in")
@pytest.mark.parametrize("agent,model", [("claude", "claude-opus-5-5"), ("codex", "gpt-6.1-sol")])
def test_real_full_review_cannot_write_host(tmp_path, monkeypatch, agent, model):
    """A real seat must execute the probe; absence of mutation alone is insufficient."""
    root = tmp_path / "checkout"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=10)
    manifest = root / "attempt.yaml"
    manifest.write_text(yaml.safe_dump(manifest_world(root, "plan")))
    plan = prepare_review_attempt("host-probe", agent, manifest, agent, receipts_root=tmp_path / "receipts")
    ledger = tmp_path / "receipts/host-probe" / f"{agent}.jsonl"
    targets = [
        ledger,
        ledger.parent / "forged.jsonl",
        root / "reviewed.txt",
        root / "batch_state/tasks/task.json",
        root / "batch_state/tasks/task.result",
    ]
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target != ledger:
            target.write_text("host-sentinel")
    original = [p.read_bytes() for p in targets]
    # No linguistic content, credentials or provider instructions enter the probe.
    code = (
        "import pathlib\n"
        f"targets={list(map(str, targets))!r}\n"
        "for target in targets:\n"
        " p=pathlib.Path(target); p.read_bytes()\n"
        " try: p.write_text('FORGED')\n"
        " except OSError: pass\n"
        " else: raise AssertionError('host write allowed')\n"
        "print('FULL_HOST_WRITES_DENIED_5')\n"
    )
    probe = root / "full-host-write-probe.py"
    probe.write_text(code)
    command = f"{shlex.quote(sys.executable)} {shlex.quote(str(probe))}"
    prompt = (
        "Run exactly this harmless local boundary test using your shell tool once. "
        "The script must attempt writes to five test-owned sentinel files; OS refusal is the expected result. "
        "Do not change the script or command, and do not use sources. Return the command's final output.\n" + command
    )
    tc = {
        **plan.adapter_options,
        "review_id": "host-probe",
        "attempt_id": agent,
        "review_manifest": str(manifest),
        "review_input_root": str(root),
        "review_access": "full",
        "reviewer_tools": True,
    }
    tc.pop("allowed_tools", None)
    monkeypatch.setattr(runner, "write_record", lambda record: None)
    result = runner.invoke(
        agent,
        prompt,
        cwd=root,
        model=model,
        effort="high",
        mode="read-only",
        tool_config=tc,
        hard_timeout=120,
        stall_timeout=60,
    )
    assert result.ok, result.stderr_excerpt
    assert result.tool_calls, "provider did not execute a tool"
    assert any(
        "FULL_HOST_WRITES_DENIED_5" in str(call.get("result", call.get("output_summary", "")))
        and command in str(call.get("arguments", ""))
        for call in result.tool_calls
    ), "captured command/output do not prove the five write attempts"
    assert probe.read_text() == code
    assert "FULL_HOST_WRITES_DENIED_5" in result.response
    assert [p.read_bytes() for p in targets] == original
    print(
        json.dumps(
            {
                "seat": agent,
                "model": model,
                "denied_writes": 5,
                "tool_calls": len(result.tool_calls),
                "protected_bytes_unchanged": True,
            }
        )
    )
