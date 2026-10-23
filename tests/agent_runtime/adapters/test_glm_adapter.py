"""Tests for GlmAdapter — the opencode Z.AI dispatch lane.

#8514 sibling coverage: the opencode dispatch adapters pin ``--format json``
and parse the NDJSON event stream because under the runner's PTY spawn,
opencode 1.18.x writes the formatted transcript to stderr and leaves stdout
empty.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.glm import GlmAdapter

FAKE_OPENCODE = "/usr/local/bin/opencode"


def _build(prompt: str, tmp_path: Path, monkeypatch, **kw):
    # The China-egress guard refuses under CI env markers; scrub them so the
    # invocation shape is testable anywhere (the guard itself is exercised by
    # the routing-guard/CI-refusal test suite).
    for var in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(var, raising=False)
    with patch("agent_runtime.adapters.glm.shutil.which", return_value=FAKE_OPENCODE):
        return GlmAdapter().build_invocation(
            prompt=prompt,
            mode=kw.pop("mode", "read-only"),
            cwd=tmp_path,
            model=kw.pop("model", None),
            task_id=kw.pop("task_id", None),
            session_id=kw.pop("session_id", None),
            tool_config=kw.pop("tool_config", None),
            effort=kw.pop("effort", None),
        )


def test_default_dispatch_plan_pins_ndjson_format(tmp_path, monkeypatch):
    plan = _build("Review this diff.", tmp_path, monkeypatch)

    assert plan.cmd[1] == "run"
    assert plan.cmd[plan.cmd.index("--model") + 1] == "zai/glm-5.3-flash"
    assert plan.cmd[plan.cmd.index("--format") + 1] == "json"
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "high"


def test_parse_response_extracts_last_assistant_text_from_ndjson(tmp_path):
    plan = None
    stdout = "\n".join(
        json.dumps(e)
        for e in (
            {"type": "step_start", "sessionID": "ses_g", "part": {"type": "step-start"}},
            {"type": "text", "sessionID": "ses_g", "part": {"type": "text", "text": "Let me check…"}},
            {
                "type": "tool_use",
                "sessionID": "ses_g",
                "part": {"type": "tool", "tool": "read", "state": {"status": "completed"}},
            },
            {"type": "text", "sessionID": "ses_g", "part": {"type": "text", "text": "Final answer."}},
            {"type": "step_finish", "sessionID": "ses_g", "part": {"type": "step_finish", "reason": "stop"}},
        )
    )

    result = GlmAdapter().parse_response(stdout=stdout, stderr="", returncode=0, plan=plan)

    assert result.ok is True
    assert result.response == "Final answer."
    assert result.session_id == "ses_g"


def test_parse_response_fails_closed_on_pty_empty_stdout(tmp_path):
    """Edge case from #8514: PTY-spawned opencode 1.18.x leaves stdout empty
    (banner+reply on stderr) — the parse must fail closed, never invent a
    response from the stderr transcript."""
    result = GlmAdapter().parse_response(
        stdout="",
        stderr="\x1b[0m\n> build · glm-5.3-flash\n\x1b[0m\nOK\n\x1b[0m",
        returncode=0,
        plan=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt
