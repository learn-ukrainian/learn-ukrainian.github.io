"""Tests for the per-dimension v6 reviewer and MIN-score aggregation."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from audit.checks import review_validation
from build import v6_build


def _write_module_tree(tmp_path: Path, *, level: str = "a2", slug: str = "at-the-cafe") -> tuple[Path, Path]:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    plan_path = curriculum_root / "plans" / level / f"{slug}.yaml"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": 1,
                "slug": slug,
                "level": level,
                "sequence": 1,
                "title": "At the Cafe",
                "word_target": 2000,
                "phase": f"{level.upper()}.1",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    content_path = curriculum_root / level / f"{slug}.md"
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content_path.write_text(
        "## Intro\n"
        "Марта заходить до кав'ярні й замовляє каву.\n\n"
        "## Dialogue\n"
        "Марта: Доброго дня.\n"
        "Бариста: Доброго дня. Що будете?\n",
        "utf-8",
    )
    return curriculum_root, content_path


def _dimension_response(
    *,
    dim_id: str,
    dim_name: str,
    score: float,
    verdict: str,
    evidence: str = "Українською: перевірено на конкретному уривку.",
    finding: str = "None.",
    fixes: list[dict] | None = None,
) -> str:
    fixes_block = ""
    if fixes:
        fixes_block = (
            "\n<fixes>\n"
            + yaml.safe_dump(fixes, sort_keys=False, allow_unicode=True).rstrip()
            + "\n</fixes>\n"
        )
    return (
        "## Dimension\n"
        f"id: {dim_id}\n"
        f"name: {dim_name}\n"
        f"score: {score:.1f}/10\n"
        f"verdict: {verdict}\n\n"
        "## Evidence\n"
        f"- {evidence}\n"
        "  English: verified against the cited passage.\n\n"
        "## Findings\n"
        f"{finding}\n\n"
        "## Verdict Reason\n"
        "Scoped to this dimension only.\n"
        f"{fixes_block}"
    )


def _style_review_yaml(score: float = 9.0) -> str:
    return (
        "phase: review-style\n"
        "verdict: PASS\n"
        "pass: true\n"
        f"overall_score: {score:.1f}\n"
        "scores:\n"
        f"  - key: pragmatic_authenticity\n    score: {score:.1f}\n"
        f"  - key: stylistic_consistency\n    score: {score:.1f}\n"
        f"  - key: culture_and_register\n    score: {score:.1f}\n"
        f"  - key: naturalness\n    score: {score:.1f}\n"
    )


def test_step_review_fans_out_aggregates_min_and_collects_all_fixes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    curriculum_root, content_path = _write_module_tree(tmp_path)
    level = "a2"
    slug = "at-the-cafe"
    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)
    monkeypatch.setattr(v6_build, "_ensure_contract_artifacts", lambda *args, **kwargs: ({}, []))
    monkeypatch.setattr(v6_build, "_format_contract_prompt_artifacts", lambda *args, **kwargs: ("{}", "[]"))
    monkeypatch.setattr(v6_build, "_build_monitor_prompt_context", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_build_vesum_report", lambda *args, **kwargs: "")
    monkeypatch.setattr(v6_build, "_determine_reviewer", lambda *args, **kwargs: ("claude", "claude"))

    active = 0
    max_active = 0
    calls: list[str] = []
    lock = threading.Lock()

    def fake_dispatch(prompt: str, *, reviewer: str, reviewer_agent: str, orch_dir: Path, phase: str):
        nonlocal active, max_active
        dim_id = phase.removeprefix("review-")
        calls.append(dim_id)
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1

        score = 9.5
        verdict = "PASS"
        finding = "None."
        fixes = None
        if dim_id == "language":
            score = 6.5
            verdict = "REVISE"
            finding = (
                "[LANGUAGE] [SEVERITY: critical]\n"
                "Location: «приймати участь»\n"
                "Issue: Українською: калька з російської; природно: «брати участь».\n"
                "English: calque; use the idiomatic Ukrainian form.\n"
                "Fix: Замінити на «брати участь»."
            )
            fixes = [{"find": "приймати участь", "replace": "брати участь"}]
        elif dim_id == "honesty":
            score = 8.2
            verdict = "PASS"
            finding = (
                "[HONESTY] [SEVERITY: major]\n"
                "Location: «вигаданий приклад без джерела»\n"
                "Issue: Українською: приклад подано без маркера невпевненості.\n"
                "English: unsupported certainty should be marked for verification.\n"
                "Fix: Додати <!-- VERIFY -->."
            )
            fixes = [
                {
                    "find": "вигаданий приклад без джерела",
                    "replace": "вигаданий приклад без джерела <!-- VERIFY -->",
                }
            ]
        label = next(spec["label"] for spec in v6_build.REVIEW_DIMENSIONS if spec["id"] == dim_id)
        return True, _dimension_response(
            dim_id=dim_id,
            dim_name=label,
            score=score,
            verdict=verdict,
            finding=finding,
            fixes=fixes,
        )

    monkeypatch.setattr(v6_build, "_dispatch_review_prompt", fake_dispatch)

    passed, score, review_text = v6_build.step_review(
        content_path,
        level,
        1,
        slug,
        writer="claude",
    )

    assert passed is False
    assert score == 6.5
    assert len(calls) == 9
    assert set(calls) == {spec["id"] for spec in v6_build.REVIEW_DIMENSIONS}
    assert max_active > 1
    assert "## Verdict: REVISE" in review_text
    assert len(v6_build._parse_review_fixes(review_text)) == 2

    review_dir = curriculum_root / level / "review"
    aggregate = yaml.safe_load((review_dir / f"{slug}-review-aggregate.yaml").read_text("utf-8"))
    assert aggregate["verdict"] == "REVISE"
    assert aggregate["verdict_score"] == 6.5
    assert aggregate["weighted_average"] > aggregate["verdict_score"]
    assert aggregate["dim_scores"]["language"] == 6.5
    # GH #1526 item 2: proposed fixes now live under ``fixes_available``;
    # ``fixes_applied`` starts empty and is populated by the post-apply step.
    assert len(aggregate["fixes_available"]) == 2
    assert aggregate["fixes_applied"] == []

    for spec in v6_build.REVIEW_DIMENSIONS:
        assert (review_dir / f"{slug}-review-{spec['id']}.yaml").exists()

    structured = yaml.safe_load((orch_dir / "review-structured-r1.yaml").read_text("utf-8"))
    issue = structured["findings"][0]["issue"]
    assert issue.startswith("Українською:")
    assert "\nEnglish:" in issue


def test_review_verdict_thresholds_follow_min_score_gate() -> None:
    assert v6_build._review_verdict_from_score(8.0) == "PASS"
    assert v6_build._review_verdict_from_score(7.99) == "REVISE"
    assert v6_build._review_verdict_from_score(6.0) == "REVISE"
    assert v6_build._review_verdict_from_score(5.99) == "REJECT"


def test_review_validation_prefers_aggregate_verdict_score(tmp_path: Path) -> None:
    module_dir = tmp_path / "a1"
    module_dir.mkdir(parents=True, exist_ok=True)
    module_file = module_dir / "sample.md"
    module_file.write_text("# Sample\n", "utf-8")

    review_dir = module_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    orch_dir = module_dir / "orchestration" / "sample"
    orch_dir.mkdir(parents=True, exist_ok=True)
    (orch_dir / "review-structured-style-r1.yaml").write_text(_style_review_yaml(9.0), "utf-8")

    aggregate_payload = {
        "slug": "sample",
        "round": 1,
        "verdict": "PASS",
        "verdict_score": 7.9,
        "weighted_average": 9.4,
        "scores": [{"dimension": 1, "name": "Language", "score": 9.4, "evidence": "clean"}],
        "findings": [],
    }
    (review_dir / "sample-review-aggregate.yaml").write_text(
        yaml.safe_dump(aggregate_payload, sort_keys=False, allow_unicode=True),
        "utf-8",
    )

    violations = review_validation.check_v6_review_validity(str(module_file), "A1", "sample")
    assert any("7.9 < 8.0" in item["message"] for item in violations)

    aggregate_payload["verdict_score"] = 8.0
    (review_dir / "sample-review-aggregate.yaml").write_text(
        yaml.safe_dump(aggregate_payload, sort_keys=False, allow_unicode=True),
        "utf-8",
    )
    violations = review_validation.check_v6_review_validity(str(module_file), "A1", "sample")
    assert not any(item["type"] == "STRUCTURED_REVIEW_BELOW_THRESHOLD" for item in violations)


# ---------- GH #1526 item 2: fixes_applied honesty ----------


def _per_dim_result(
    *,
    dim_id: str,
    dim_name: str,
    score: float,
    fixes: list[dict] | None = None,
    findings: list[dict] | None = None,
) -> v6_build.PerDimensionReviewResult:
    return v6_build.PerDimensionReviewResult(
        dimension_id=dim_id,
        dimension_name=dim_name,
        score=score,
        verdict="PASS" if score >= 8.0 else "REVISE",
        evidence="synthetic evidence",
        review_text=f"score: {score:.1f}/10\nverdict: {'PASS' if score >= 8.0 else 'REVISE'}",
        findings=tuple(findings or ()),
        fixes=tuple(fixes or ()),
    )


def test_aggregate_payload_starts_with_empty_fixes_applied_and_populates_available() -> None:
    """Regression guard: the aggregate-YAML builder must NOT populate
    ``fixes_applied`` from the reviewer's proposed fix count. Before GH #1526
    item 2 the payload field ``fixes_applied`` carried proposed counts, which
    was a lie because the apply step may not run (convergence escalated to
    plan_revision_request before ``_apply_review_fixes`` fired) or every fix
    may be skipped (bad anchors). Now:

      * ``fixes_available`` holds the reviewer's proposed fix counts (truth:
        these were emitted by the reviewer; applying is a separate step).
      * ``fixes_applied`` starts as ``[]`` and is populated post-apply by
        ``_update_aggregate_with_applied_fixes``.
    """
    results = [
        _per_dim_result(
            dim_id=spec["id"],
            dim_name=spec["label"],
            score=9.0 if spec["id"] != "factual" else 6.5,
            fixes=(
                [{"find": "x", "replace": "y"}] * 5
                if spec["id"] == "factual"
                else []
            ),
        )
        for spec in v6_build.REVIEW_DIMENSIONS
    ]
    payload = v6_build._build_review_aggregate_payload(
        slug="sample",
        round_num=1,
        verdict="REVISE",
        verdict_score=6.5,
        weighted_average=8.5,
        results=results,
        content_filename="sample.md",
    )
    # Proposed fixes → fixes_available, not fixes_applied.
    assert payload["fixes_applied"] == []
    assert len(payload["fixes_available"]) == 1
    assert payload["fixes_available"][0]["dim"] == "factual"
    assert payload["fixes_available"][0]["count"] == 5


def test_update_aggregate_with_applied_fixes_rewrites_count_post_apply(
    tmp_path: Path, monkeypatch,
) -> None:
    """The post-apply helper rewrites ``fixes_applied`` with the real landed
    count — independent of how many fixes the reviewer proposed in
    ``fixes_available``. Covers the a1/1 2026-04-24 empirical case:
    5 proposed, 0 landed (because convergence escalated before apply).
    """
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    level = "a1"
    slug = "sample"
    review_dir = curriculum_root / level / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    initial_payload = {
        "slug": slug,
        "round": 1,
        "verdict": "REVISE",
        "verdict_score": 6.5,
        "weighted_average": 8.5,
        "scores": [],
        "findings": [],
        "fixes_available": [{"dim": "factual", "count": 5, "files": ["sample.md"]}],
        "fixes_applied": [],
        "passed": False,
    }
    dumped = yaml.safe_dump(initial_payload, sort_keys=False, allow_unicode=True)
    (review_dir / f"{slug}-review-aggregate-r1.yaml").write_text(dumped, "utf-8")
    (review_dir / f"{slug}-review-aggregate.yaml").write_text(dumped, "utf-8")

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    # Case 1: apply landed zero fixes (the a1/1 empirical case).
    v6_build._update_aggregate_with_applied_fixes(
        level=level,
        slug=slug,
        round_num=1,
        applied_count=0,
        content_filename="sample.md",
    )
    after_zero = yaml.safe_load((review_dir / f"{slug}-review-aggregate-r1.yaml").read_text("utf-8"))
    assert after_zero["fixes_applied"] == [{"count": 0, "files": ["sample.md"]}]
    # fixes_available unchanged — reviewer's proposal count is preserved.
    assert after_zero["fixes_available"] == [{"dim": "factual", "count": 5, "files": ["sample.md"]}]

    # Case 2: apply landed 3 fixes — honest count lands in fixes_applied.
    v6_build._update_aggregate_with_applied_fixes(
        level=level,
        slug=slug,
        round_num=1,
        applied_count=3,
        content_filename="sample.md",
    )
    after_three = yaml.safe_load((review_dir / f"{slug}-review-aggregate-r1.yaml").read_text("utf-8"))
    assert after_three["fixes_applied"] == [{"count": 3, "files": ["sample.md"]}]
    # Unversioned alias stays in sync.
    unversioned = yaml.safe_load((review_dir / f"{slug}-review-aggregate.yaml").read_text("utf-8"))
    assert unversioned["fixes_applied"] == [{"count": 3, "files": ["sample.md"]}]
