from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build import module_memory, v6_build
from build.convergence_loop import (
    ConvergenceContext,
    MutationSummary,
    RecoverableValidationError,
    ReviewObservation,
    prioritize_findings,
    run_convergence_loop,
)
from build.module_memory import module_memory_path


def _finding(
    *,
    dimension: str,
    severity: str,
    location: str,
    issue: str,
    fix: str,
) -> dict:
    return {
        "dimension": dimension,
        "severity": severity,
        "location": location,
        "issue": issue,
        "fix": fix,
    }


def _observation(
    *,
    score: float,
    findings: list[dict],
    content_hash: str,
    passed: bool = False,
    patch_available: bool = False,
    dim_floor_dimensions: tuple[str, ...] = (),
    review_text: str = "Verdict",
    artifacts: dict[str, str] | None = None,
) -> ReviewObservation:
    return ReviewObservation(
        passed=passed,
        score=score,
        review_text=review_text,
        findings=tuple(findings),
        dim_floor_dimensions=dim_floor_dimensions,
        content_hash=content_hash,
        patch_available=patch_available,
        reviewer="claude",
        writer_model_version="gemini-3.1-pro-preview",
        reviewer_model_version="claude-opus-4-6",
        artifacts={} if artifacts is None else dict(artifacts),
    )


class Harness:
    def __init__(self, observations: list[ReviewObservation], tmp_path: Path) -> None:
        self.observations = observations
        self.index = 0
        self.patch_calls = 0
        self.section_calls = 0
        self.full_calls = 0
        self.swap_calls = 0
        self.style_calls = 0
        self.tmp_path = tmp_path

    def review_round(self, _writer: str) -> ReviewObservation:
        observation = self.observations[min(self.index, len(self.observations) - 1)]
        self.index += 1
        return observation

    def patch_round(self, _observation: ReviewObservation) -> MutationSummary:
        self.patch_calls += 1
        return MutationSummary(True, 1, "patched")

    def section_rewrite_round(self, _findings, _writer: str) -> MutationSummary:
        self.section_calls += 1
        return MutationSummary(True, 1, "section rewrite")

    def full_rewrite_round(self, _findings, _writer: str) -> MutationSummary:
        self.full_calls += 1
        return MutationSummary(True, 1, "full rewrite")

    def writer_swap_round(self, _findings, _writer: str) -> tuple[str | None, MutationSummary]:
        self.swap_calls += 1
        return "claude-tools", MutationSummary(True, 1, "writer swap")

    def refresh_sidecars(self, _strategy: str) -> bool:
        return True

    def style_review_after_swap(self, _writer: str) -> None:
        self.style_calls += 1

    def context(self) -> ConvergenceContext:
        curriculum_root = self.tmp_path / "curriculum" / "l2-uk-en"
        memory_path = module_memory_path(curriculum_root, "a1", "demo")
        return ConvergenceContext(
            level="a1",
            slug="demo",
            writer="gemini-tools",
            review_round=self.review_round,
            patch_round=self.patch_round,
            section_rewrite_round=self.section_rewrite_round,
            full_rewrite_round=self.full_rewrite_round,
            writer_swap_round=self.writer_swap_round,
            refresh_sidecars=self.refresh_sidecars,
            memory_path=memory_path,
            terminal_dir=memory_path.parent,
            stuck_modules_path=curriculum_root / "stuck-modules.yaml",
            plan_hash="plan-hash",
            plan_version=1,
            sources_hash="sources-hash",
            style_review_after_swap=self.style_review_after_swap,
        )


class FailingSectionRewriteHarness(Harness):
    def section_rewrite_round(self, _findings, _writer: str) -> MutationSummary:
        raise RuntimeError("section rewrite exploded")


class RecoverableSidecarHarness(Harness):
    """Refresh_sidecars raises RecoverableValidationError the first time a
    configured strategy fires, succeeds on subsequent calls.
    """

    def __init__(
        self,
        observations: list[ReviewObservation],
        tmp_path: Path,
        *,
        fail_on_strategies: tuple[str, ...] = ("full_rewrite",),
        validator_findings: tuple[dict, ...] | None = None,
    ) -> None:
        super().__init__(observations, tmp_path)
        self.fail_on = set(fail_on_strategies)
        self.refresh_calls_by_strategy: dict[str, int] = {}
        self.validator_findings = validator_findings or (
            {
                "dimension": "Plan Adherence",
                "severity": "critical",
                "location": "## whole module / vocabulary sidecar",
                "issue": (
                    "missing vocabulary: the regenerated vocabulary sidecar is missing "
                    "required terms: кольори, олівець"
                ),
                "fix": (
                    "Regenerate the module so every required-vocabulary term from the "
                    "plan appears in the vocabulary YAML."
                ),
            },
        )

    def refresh_sidecars(self, strategy: str) -> bool:
        self.refresh_calls_by_strategy[strategy] = (
            self.refresh_calls_by_strategy.get(strategy, 0) + 1
        )
        if (
            strategy in self.fail_on
            and self.refresh_calls_by_strategy[strategy] == 1
        ):
            raise RecoverableValidationError(
                "plan-sidecar validation failed: missing vocabulary кольори, олівець",
                findings=list(self.validator_findings),
            )
        return True


def test_tier_one_patch_fires_on_local_findings(tmp_path: Path) -> None:
    harness = Harness(
        [
            _observation(
                score=8.5,
                findings=[
                    _finding(
                        dimension="Linguistic Accuracy",
                        severity="major",
                        location="## Intro / paragraph 1 / sentence 1",
                        issue="The sentence mislabels [=] as a dash.",
                        fix="Change the sentence only.",
                    )
                ],
                content_hash="hash-1",
                patch_available=True,
            ),
            _observation(score=9.2, findings=[], content_hash="hash-2", passed=True),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.terminal == "pass"
    assert result.trace[0]["strategy"] == "patch"
    assert harness.patch_calls == 1


def test_section_rewrite_tier_fires(tmp_path: Path) -> None:
    harness = Harness(
        [
            _observation(
                score=8.4,
                findings=[
                    _finding(
                        dimension="Pedagogical Quality",
                        severity="major",
                        location="## Привіт!",
                        issue="The section teaches one register rule and models the opposite.",
                        fix="Rewrite that section only.",
                    )
                ],
                content_hash="hash-1",
            ),
            _observation(score=9.1, findings=[], content_hash="hash-2", passed=True),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.trace[0]["strategy"] == "section_rewrite"
    assert harness.section_calls == 1


def test_full_rewrite_tier_fires_on_cross_section_findings(tmp_path: Path) -> None:
    harness = Harness(
        [
            _observation(
                score=8.2,
                findings=[
                    _finding(
                        dimension="Exercise Quality",
                        severity="major",
                        location="## Intro and ## Practice",
                        issue="Activity order and vocabulary pacing drift across multiple sections.",
                        fix="Resequence the module.",
                    )
                ],
                content_hash="hash-1",
            ),
            _observation(score=9.0, findings=[], content_hash="hash-2", passed=True),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.trace[0]["strategy"] == "full_rewrite"
    assert harness.full_calls == 1


def test_writer_swap_tier_fires_after_full_rewrite_targets_repeat(tmp_path: Path) -> None:
    finding = _finding(
        dimension="Exercise Quality",
        severity="major",
        location="## Intro and ## Practice",
        issue="Activity order and vocabulary pacing drift across multiple sections.",
        fix="Resequence the module.",
    )
    harness = Harness(
        [
            _observation(score=8.2, findings=[finding], content_hash="hash-1"),
            _observation(score=8.3, findings=[finding], content_hash="hash-2"),
            _observation(score=9.2, findings=[], content_hash="hash-3", passed=True),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.trace[0]["strategy"] == "full_rewrite"
    assert result.trace[1]["strategy"] == "writer_swap"
    assert harness.swap_calls == 1
    assert harness.style_calls == 1


def test_hard_floor_priority_reorders_findings() -> None:
    observation = _observation(
        score=8.0,
        findings=[
            _finding(
                dimension="Plan Adherence",
                severity="major",
                location="## Intro and ## Practice",
                issue="Activity order drifts across sections.",
                fix="Resequence the module.",
            ),
            _finding(
                dimension="Linguistic Accuracy",
                severity="minor",
                location="## Intro / paragraph 1",
                issue="The sentence mislabels [=] as a dash.",
                fix="Change the sentence only.",
            ),
        ],
        content_hash="hash-1",
        dim_floor_dimensions=("linguistic_accuracy",),
    )

    prioritized = prioritize_findings(observation, growth_log_path=None)

    assert prioritized[0]["dimension"] == "linguistic_accuracy"
    assert prioritized[0]["effective_severity"] == "critical"


def test_five_attempt_cap_emits_budget_exhausted_and_appends_stuck_modules(tmp_path: Path) -> None:
    observations = [
        _observation(
            score=8.0,
            findings=[
                _finding(
                    dimension="Exercise Quality",
                    severity="major",
                    location=f"## Section {index} and ## Practice",
                    issue=f"Activity order drift variant {index}.",
                    fix="Resequence the module.",
                )
            ],
            content_hash=f"hash-{index}",
        )
        for index in range(1, 7)
    ]
    harness = Harness(observations, tmp_path)

    result = run_convergence_loop(harness.context())

    stuck_modules = yaml.safe_load(
        (tmp_path / "curriculum" / "l2-uk-en" / "stuck-modules.yaml").read_text("utf-8")
    )
    assert result.terminal == "budget_exhausted"
    assert result.artifact_path is not None and result.artifact_path.exists()
    assert stuck_modules[0]["terminal"] == "budget_exhausted"


def test_plan_level_fasts_to_tier5_after_tier3(tmp_path: Path) -> None:
    finding = _finding(
        dimension="Plan Adherence",
        severity="major",
        location="## Приголосні звуки",
        issue="The contracted consonant beat stays undercovered.",
        fix="Change the plan rather than the prose.",
    )
    harness = Harness(
        [
            _observation(score=8.1, findings=[finding], content_hash="hash-1"),
            _observation(score=8.0, findings=[finding], content_hash="hash-2"),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.trace[0]["strategy"] == "full_rewrite"
    assert result.terminal == "plan_revision_request"
    assert result.artifact_path is not None and result.artifact_path.exists()


def test_happy_path_populates_memory_with_one_history_entry(tmp_path: Path) -> None:
    harness = Harness(
        [_observation(score=9.2, findings=[], content_hash="hash-1", passed=True)],
        tmp_path,
    )
    context = harness.context()

    result = run_convergence_loop(context)
    memory, _ = module_memory.load_module_memory(
        context.memory_path,
        expected_plan_hash="plan-hash",
        expected_plan_version=1,
        expected_sources_hash="sources-hash",
    )

    assert result.terminal == "pass"
    assert len(memory["history"]) == 1
    assert memory["constraints"] == []
    history_entry = memory["history"][0]
    assert history_entry["timestamps"]["started"]
    assert history_entry["timestamps"]["finished"]
    assert history_entry["cost"] == {
        "input_tokens": None,
        "output_tokens": None,
        "wall_clock_s": history_entry["cost"]["wall_clock_s"],
    }
    assert isinstance(history_entry["cost"]["wall_clock_s"], float)


def test_local_findings_patch_converges_to_pass(tmp_path: Path) -> None:
    harness = Harness(
        [
            _observation(
                score=8.6,
                findings=[
                    _finding(
                        dimension="Linguistic Accuracy",
                        severity="major",
                        location="## Intro / paragraph 1 / sentence 1",
                        issue="The sentence mislabels [=] as a dash.",
                        fix="Change the sentence only.",
                    )
                ],
                content_hash="hash-1",
                patch_available=True,
            ),
            _observation(score=9.1, findings=[], content_hash="hash-2", passed=True),
        ],
        tmp_path,
    )

    result = run_convergence_loop(harness.context())

    assert result.terminal == "pass"
    assert result.trace[0]["strategy"] == "patch"


def test_prompt_hash_is_deterministic_for_same_prompt_across_runs(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("same prompt bytes", "utf-8")
    harness = Harness(
        [
            _observation(
                score=8.6,
                findings=[
                    _finding(
                        dimension="Linguistic Accuracy",
                        severity="major",
                        location="## Intro / paragraph 1 / sentence 1",
                        issue="The sentence mislabels [=] as a dash.",
                        fix="Change the sentence only.",
                    )
                ],
                content_hash="hash-1",
                patch_available=True,
                review_text="Reviewer output A",
                artifacts={"prompt_path": str(prompt_path)},
            ),
            _observation(
                score=9.1,
                findings=[],
                content_hash="hash-2",
                passed=True,
                review_text="Reviewer output B",
                artifacts={"prompt_path": str(prompt_path)},
            ),
        ],
        tmp_path,
    )
    context = harness.context()

    run_convergence_loop(context)
    memory, _ = module_memory.load_module_memory(
        context.memory_path,
        expected_plan_hash="plan-hash",
        expected_plan_version=1,
        expected_sources_hash="sources-hash",
    )

    assert len(memory["history"]) == 2
    assert memory["history"][0]["prompt_hash"] == memory["history"][1]["prompt_hash"]


def test_exception_in_mutation_emits_budget_exhausted_terminal(tmp_path: Path) -> None:
    harness = FailingSectionRewriteHarness(
        [
            _observation(
                score=8.4,
                findings=[
                    _finding(
                        dimension="Pedagogical Quality",
                        severity="major",
                        location="## Привіт!",
                        issue="The section teaches one register rule and models the opposite.",
                        fix="Rewrite that section only.",
                    )
                ],
                content_hash="hash-1",
            ),
        ],
        tmp_path,
    )
    context = harness.context()

    result = run_convergence_loop(context)
    budget_payload = yaml.safe_load(result.artifact_path.read_text("utf-8"))
    memory, _ = module_memory.load_module_memory(
        context.memory_path,
        expected_plan_hash="plan-hash",
        expected_plan_version=1,
        expected_sources_hash="sources-hash",
    )

    assert result.terminal == "budget_exhausted"
    assert budget_payload["exception"]["type"] == "RuntimeError"
    assert budget_payload["exception"]["message"] == "section rewrite exploded"
    assert "section rewrite exploded" in budget_payload["exception"]["traceback"]
    assert memory["history"][-1]["decision_reason"] == "exception"
    assert memory["history"][-1]["exception_type"] == "RuntimeError"
    assert memory["history"][-1]["exception_message"] == "section rewrite exploded"


def test_end_to_end_stuck_a1_m1_uses_cached_reviews_without_budget_exhausted(tmp_path: Path) -> None:
    review_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "a1" / "review"
    cached_reviews = [
        review_dir / "sounds-letters-and-hello-review-r2.md",
        review_dir / "sounds-letters-and-hello-review-r3.md",
    ]

    observations = []
    for index, review_path in enumerate(cached_reviews, start=1):
        review_text = review_path.read_text("utf-8")
        parsed = v6_build._parse_review_result(review_text)
        observations.append(
            ReviewObservation(
                passed=parsed.passed,
                score=parsed.score,
                review_text=review_text,
                findings=tuple(v6_build._extract_structured_findings(review_text)),
                dim_floor_dimensions=tuple(
                    v6_build._normalized_dimension_name(item.get("name", ""))
                    for item in parsed.parsed_scores
                    if int(item.get("score", 10) or 10) < v6_build.REVIEW_TARGET_SCORE
                ),
                content_hash=f"cached-hash-{index}",
                patch_available=bool(v6_build._parse_review_fixes(review_text)),
                parsed_scores=tuple(parsed.parsed_scores),
                reviewer="claude",
                writer_model_version="gemini-3.1-pro-preview",
                reviewer_model_version="claude-opus-4-6",
            )
        )
    observations.append(observations[-1])

    harness = Harness(observations, tmp_path)
    result = run_convergence_loop(harness.context())

    assert result.terminal in {"pass", "plan_revision_request"}
    assert result.terminal != "budget_exhausted"


def test_recoverable_validation_error_does_not_collapse_budget(tmp_path: Path) -> None:
    """Sidecar validator raising RecoverableValidationError must not terminate the
    convergence budget. Its findings become the next iteration's prioritized findings,
    and the escalation loop continues at a higher tier.
    """
    cross_section_finding = _finding(
        dimension="Exercise Quality",
        severity="major",
        location="## Intro and ## Practice",
        issue="Activity order and vocabulary pacing drift across multiple sections.",
        fix="Resequence the module.",
    )
    harness = RecoverableSidecarHarness(
        [
            _observation(score=8.2, findings=[cross_section_finding], content_hash="hash-1"),
            _observation(score=9.1, findings=[], content_hash="hash-3", passed=True),
        ],
        tmp_path,
        fail_on_strategies=("full_rewrite",),
    )
    context = harness.context()

    result = run_convergence_loop(context)
    memory, _ = module_memory.load_module_memory(
        context.memory_path,
        expected_plan_hash="plan-hash",
        expected_plan_version=1,
        expected_sources_hash="sources-hash",
    )

    assert result.terminal == "pass"
    # The first full_rewrite failed sidecar validation. Loop must have escalated
    # to another strategy instead of collapsing: either a second full_rewrite or
    # a writer_swap depending on stall detection.
    assert harness.full_calls + harness.swap_calls >= 2
    sidecar_rounds = [
        entry
        for entry in memory["history"]
        if entry.get("reviewer") == "sidecar_validator"
    ]
    assert len(sidecar_rounds) == 1
    assert sidecar_rounds[0]["decision_reason"].startswith("sidecar validation failed")
    assert sidecar_rounds[0]["tier"] == 3
    assert "missing_vocab" in {
        item["error_class"] for item in sidecar_rounds[0]["prioritized_findings"]
    }


def test_recoverable_validation_error_respects_escalation_budget(
    tmp_path: Path,
) -> None:
    """A recoverable validator failure consumes one escalation of the five-attempt
    budget — it is a legitimate mutation round, not a free retry. This guards against
    runaway retries when the writer keeps producing sidecar-invalid content: the
    loop still terminates in bounded time (via plan_revision_request once the stall
    detector bumps past writer_swap, or via budget_exhausted if it runs out of
    escalations first).
    """
    cross_section_finding = _finding(
        dimension="Exercise Quality",
        severity="major",
        location="## Intro and ## Practice",
        issue="Activity order and vocabulary pacing drift across multiple sections.",
        fix="Resequence the module.",
    )

    class AlwaysFailingSidecarHarness(RecoverableSidecarHarness):
        def refresh_sidecars(self, strategy: str) -> bool:
            self.refresh_calls_by_strategy[strategy] = (
                self.refresh_calls_by_strategy.get(strategy, 0) + 1
            )
            raise RecoverableValidationError(
                "plan-sidecar validation failed: missing vocabulary кольори",
                findings=list(self.validator_findings),
            )

    observations = [
        _observation(score=8.2, findings=[cross_section_finding], content_hash=f"hash-{i}")
        for i in range(1, 8)
    ]
    harness = AlwaysFailingSidecarHarness(observations, tmp_path)
    context = harness.context()

    result = run_convergence_loop(context)
    memory, _ = module_memory.load_module_memory(
        context.memory_path,
        expected_plan_hash="plan-hash",
        expected_plan_version=1,
        expected_sources_hash="sources-hash",
    )

    assert result.terminal in {"budget_exhausted", "plan_revision_request"}
    assert len(memory["history"]) <= 1 + context.max_escalations
    sidecar_rounds = [
        entry
        for entry in memory["history"]
        if entry.get("reviewer") == "sidecar_validator"
    ]
    # Every mutation that got as far as refresh_sidecars failed validation
    assert len(sidecar_rounds) >= 1
    # No generic-exception round should appear — validator failures are their own path
    exception_rounds = [
        entry for entry in memory["history"] if entry.get("decision_reason") == "exception"
    ]
    assert exception_rounds == []


def test_unrecoverable_runtime_error_still_collapses_budget(tmp_path: Path) -> None:
    """Generic exceptions (pipeline/tooling failures) should still terminate the
    budget early with an exception-context entry.
    """
    harness = FailingSectionRewriteHarness(
        [
            _observation(
                score=8.4,
                findings=[
                    _finding(
                        dimension="Pedagogical Quality",
                        severity="major",
                        location="## Привіт!",
                        issue="The section teaches one register rule and models the opposite.",
                        fix="Rewrite that section only.",
                    )
                ],
                content_hash="hash-1",
            ),
        ],
        tmp_path,
    )
    context = harness.context()

    result = run_convergence_loop(context)
    budget_payload = yaml.safe_load(result.artifact_path.read_text("utf-8"))

    assert result.terminal == "budget_exhausted"
    assert budget_payload["exception"]["type"] == "RuntimeError"
    assert "section rewrite exploded" in budget_payload["exception"]["message"]


def test_budget_exhausted_payload_has_no_exception_for_reviewer_disagreement(
    tmp_path: Path,
) -> None:
    """When budget exhausts through legitimate reviewer disagreement (no
    exceptions raised), the terminal payload must not claim an exception fired.
    """
    observations = [
        _observation(
            score=8.0,
            findings=[
                _finding(
                    dimension="Exercise Quality",
                    severity="major",
                    location=f"## Section {index} and ## Practice",
                    issue=f"Activity order drift variant {index}.",
                    fix="Resequence the module.",
                )
            ],
            content_hash=f"hash-{index}",
        )
        for index in range(1, 8)
    ]
    harness = Harness(observations, tmp_path)

    result = run_convergence_loop(harness.context())
    budget_payload = yaml.safe_load(result.artifact_path.read_text("utf-8"))

    assert result.terminal == "budget_exhausted"
    assert "exception" not in budget_payload
    assert len(budget_payload["history"]) == 1 + harness.context().max_escalations
