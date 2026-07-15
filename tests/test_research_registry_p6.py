"""P6 real-record pilot regressions for ADR-011.

The checker is intentionally run against the real three-record registry.  Its
API harness freezes only response-local time and disables response telemetry;
it does not inspect mutable consumption events or live task state.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import check_research_registry_pilot as pilot


def test_real_seeded_pilot_checker_is_green() -> None:
    report = pilot.run(Path(__file__).resolve().parents[1])

    assert report["metrics"] == {"tp": 3, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0}
    assert report["state_manifest_bytes"] == {"disabled": 912, "enabled": 1031}
    assert report["warm_reads"] == {
        "quality_manifest": [200, 342, 304, 0],
        "record_body": [200, 2630, 304, 0],
    }


def test_json_cli_output_is_a_single_parseable_document(capsys: pytest.CaptureFixture[str]) -> None:
    assert pilot.main(["--json"]) == 0

    output = capsys.readouterr().out
    report = json.loads(output)

    assert report["ok"] is True
    assert report["metrics"] == {"tp": 3, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0}


def test_known_role_bootstrap_contract_is_explicit_in_source() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "agents_extensions/shared/rules/workflow.md"
    content = source.read_text(encoding="utf-8")

    assert 'MonitorClient().bootstrap(role="quality")' in content
    assert "Generic or genuinely role-unknown startup stays pointer-free:" in content
    assert "MonitorClient().bootstrap()" in content
    assert "http://localhost:8765/api/knowledge/cold-start?role=quality" in content
    assert "replace `quality` with the assigned role" in content
    assert "Generic or genuinely role-unknown session: skip the role-scoped request; remain pointer-free." in content
    assert "curl -s http://localhost:8765/api/orient                 # always-fresh, has meta" in content
    assert "/api/orient?role=" not in content

    # Deployment is verified separately by scripts/check_rules_deployment.sh;
    # this source assertion prevents future edits from dropping either behavior.
    assert content.index('MonitorClient().bootstrap(role="quality")') < content.index(
        "Generic or genuinely role-unknown startup stays pointer-free:"
    )


def test_orchestrator_dispatch_duty_reaches_every_agent_entry_point() -> None:
    root = Path(__file__).resolve().parents[1]
    required_flags = (
        "--research-role",
        "--research-task-family",
        "--research-track",
        "--research-owned-path",
    )
    entry_points = (
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        "agents_extensions/shared/rules/workflow.md",
        "docs/SCRIPTS.md",
    )

    for relative_path in entry_points:
        content = (root / relative_path).read_text(encoding="utf-8")
        normalized = " ".join(content.lower().split())
        assert "Project Research Registry" in content, f"{relative_path} lost registry awareness"
        assert "orchestrator" in normalized, f"{relative_path} lost orchestrator ownership"
        for flag in required_flags:
            assert flag in content, f"{relative_path} lost {flag}"
        assert "genuinely generic or unknown" in normalized, (
            f"{relative_path} lost the deliberate pointer-free classification"
        )
        assert "surfaced pointer is not proof of consumption" in normalized, (
            f"{relative_path} now conflates surfacing with consumption"
        )

    workflow = (root / "agents_extensions/shared/rules/workflow.md").read_text(encoding="utf-8")
    workflow_normalized = " ".join(workflow.split())
    assert "never the provider or agent identity" in workflow_normalized
    assert "Classification is mandatory; delivery remains fail-open." in workflow
    assert workflow.index("Before **every** `delegate.py dispatch`") < workflow.index(
        "**Genuinely generic or unknown:**"
    )

    scripts_doc = (root / "docs/SCRIPTS.md").read_text(encoding="utf-8")
    assert (
        "--agent {codex|claude|agy|grok|grok-build|grok-hermes|deepseek|cursor}"
        in scripts_doc
    )
    assert "--worktree .worktrees/<agent>-<task-id>" not in scripts_doc
    assert "--worktree .worktrees/codex-issue-1383-smoke" not in scripts_doc
    assert "GET /api/knowledge/record/{id}?task=<task-id>" in scripts_doc
