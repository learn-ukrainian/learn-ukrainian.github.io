from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build.convergence_loop import (
    ConvergenceContext,
    MutationSummary,
    ReviewObservation,
    run_convergence_loop,
)
from build.module_memory import module_memory_path


def test_convergence_loop_marks_plan_revision_terminal(tmp_path: Path) -> None:
    finding = {
        "dimension": "Plan Adherence",
        "severity": "major",
        "location": "## Intro",
        "issue": "The planned dialogue beat is missing.",
        "fix": "Revise the plan before another writer attempt.",
    }

    def review_round(_writer: str) -> ReviewObservation:
        return ReviewObservation(
            passed=False,
            score=8.0,
            review_text="Verdict: REVISE",
            findings=(finding,),
            dim_floor_dimensions=(),
            content_hash="hash-1",
        )

    context = ConvergenceContext(
        level="a1",
        slug="contract-flow",
        writer="gemini-tools",
        review_round=review_round,
        patch_round=lambda _observation: MutationSummary(False, 0, "no patch"),
        refresh_sidecars=lambda _strategy: True,
        memory_path=module_memory_path(tmp_path / "curriculum" / "l2-uk-en", "a1", "contract-flow"),
        terminal_dir=tmp_path / "terminal",
        stuck_modules_path=tmp_path / "curriculum" / "l2-uk-en" / "stuck-modules.yaml",
        plan_hash="plan-hash",
        plan_version=1,
        sources_hash="sources-hash",
    )

    result = run_convergence_loop(context)

    assert result.terminal == "plan_revision_request"
    assert result.artifact_path is not None and result.artifact_path.exists()
    payload = yaml.safe_load(result.artifact_path.read_text("utf-8"))
    assert payload["level"] == "a1"
    assert payload["slug"] == "contract-flow"
