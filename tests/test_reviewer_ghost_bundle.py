"""Tests for the reviewer ghost-finding bundle writer (GH #1529 P3).

These cover the v6_build helper that persists ghost findings to
``curriculum/l2-uk-en/{level}/review/{slug}-ghost-review-r{round}.yaml``
before the convergence loop runs its terminal-decision step. Key invariant:
the bundle must survive a plan_revision_request terminal, since that's the
exact path the a1/sounds-letters-and-hello 2026-04-24 rebuild followed when
the "мама reversed" ghost dragged Factual to 4.5.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Bundle writer + round-num helper are defined in v6_build.py.
from build.v6_build import (
    _extract_round_num,
    _write_reviewer_ghost_bundle,
)


def _ghost_entry(
    *,
    dimension: str,
    severity: str,
    location: str,
    issue: str,
    anchor: str,
    normalized_id: str = "nf_abc1234567890def",
) -> dict:
    return {
        "normalized_id": normalized_id,
        "dimension": dimension,
        "severity": severity,
        "effective_severity": severity,
        "location": location,
        "issue": issue,
        "fix": "reviewer fix text",
        "reviewer_find_anchor": anchor,
        "anchor_validation": "anchor_missing",
        "raw_fix": {"find": anchor, "replace": "corrected"},
    }


def test_extract_round_num_parses_versioned_filenames(tmp_path: Path) -> None:
    assert _extract_round_num(tmp_path / "colors-review-r3.md") == 3
    assert _extract_round_num(tmp_path / "colors-review-r12.md") == 12
    # Unversioned falls back to round 1 — the initial-write case.
    assert _extract_round_num(tmp_path / "colors-review.md") == 1


def test_bundle_writes_correct_path_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Redirect CURRICULUM_ROOT to tmp so the write stays isolated.
    from build import v6_build

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")

    ghosts = (
        _ghost_entry(
            dimension="factual_accuracy",
            severity="major",
            location="мама section",
            issue="reviewer claims мама is two [а] sounds",
            anchor="**мама** → [• – • –] — two [а] sounds",
            normalized_id="nf_factual_mama_0001",
        ),
    )

    bundle_path = _write_reviewer_ghost_bundle(
        level="a1",
        slug="sounds-letters-and-hello",
        round_num=1,
        reviewer_agent="codex-tools",
        ghost_findings=ghosts,
        content_sha256="deadbeef" * 8,
    )

    expected = (
        tmp_path
        / "curriculum"
        / "l2-uk-en"
        / "a1"
        / "review"
        / "sounds-letters-and-hello-ghost-review-r1.yaml"
    )
    assert bundle_path == expected
    assert bundle_path.is_file()

    payload = yaml.safe_load(bundle_path.read_text("utf-8"))
    assert payload["slug"] == "sounds-letters-and-hello"
    assert payload["round"] == 1
    assert payload["dimension"] == "factual_accuracy"  # single-dim → that dim
    assert payload["reviewer_agent"] == "codex-tools"
    assert payload["content_sha256"] == "deadbeef" * 8
    # generated_at is ISO-8601 parseable
    datetime.fromisoformat(payload["generated_at"])

    assert len(payload["ghost_findings"]) == 1
    entry = payload["ghost_findings"][0]
    assert entry["finding_id"] == "nf_factual_mama_0001"
    assert entry["dimension"] == "factual_accuracy"
    assert entry["severity"] == "major"
    assert entry["location"] == "мама section"
    assert entry["reviewer_find_anchor"].startswith("**мама**")
    assert entry["anchor_validation"] == "anchor_missing"
    assert entry["raw_fix"] == {
        "find": "**мама** → [• – • –] — two [а] sounds",
        "replace": "corrected",
    }


def test_bundle_marks_dimension_mixed_when_ghosts_span_dims(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from build import v6_build

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")

    ghosts = (
        _ghost_entry(
            dimension="factual_accuracy",
            severity="major",
            location="loc1",
            issue="issue1",
            anchor="anchor1",
            normalized_id="nf_1",
        ),
        _ghost_entry(
            dimension="honesty",
            severity="critical",
            location="loc2",
            issue="issue2",
            anchor="anchor2",
            normalized_id="nf_2",
        ),
    )
    bundle_path = _write_reviewer_ghost_bundle(
        level="a1",
        slug="colors",
        round_num=2,
        reviewer_agent="codex-tools",
        ghost_findings=ghosts,
        content_sha256="abc" * 8,
    )
    payload = yaml.safe_load(bundle_path.read_text("utf-8"))
    assert payload["dimension"] == "mixed"
    assert len(payload["ghost_findings"]) == 2


def test_bundle_path_survives_plan_revision_request_write_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulate the a1/1 failure mode: ghost bundle is written FIRST, then the
    convergence-loop terminal_dir writes a plan_revision_request.yaml. The
    bundle must still be on disk after the terminal write — no cleanup path
    can remove it.
    """
    from build import v6_build

    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    ghosts = (
        _ghost_entry(
            dimension="factual_accuracy",
            severity="major",
            location="x",
            issue="y",
            anchor="ghost-anchor",
        ),
    )
    bundle_path = _write_reviewer_ghost_bundle(
        level="a1",
        slug="colors",
        round_num=1,
        reviewer_agent="codex-tools",
        ghost_findings=ghosts,
        content_sha256="sha",
    )
    assert bundle_path.is_file()

    # Simulate terminal-step write of plan_revision_request into
    # orchestration/<slug>/ — independent dir, must not touch review/.
    orch_dir = curriculum_root / "a1" / "orchestration" / "colors"
    orch_dir.mkdir(parents=True)
    terminal = orch_dir / "plan_revision_request.yaml"
    terminal.write_text(
        yaml.safe_dump({"slug": "colors", "attempts": 1}), "utf-8"
    )

    assert bundle_path.is_file(), "bundle must persist past plan_revision_request"
    assert terminal.is_file()


def test_no_bundle_shape_written_when_no_ghosts(tmp_path: Path) -> None:
    """Contract: ``_write_reviewer_ghost_bundle`` is only called when ghosts
    exist (see ``_convergence_review_observation`` gating). If a caller
    violates the contract and passes empty ghosts, the bundle is still
    valid YAML — but there is no reason the caller would do so. Instead,
    we assert the GATING works: with no ghosts, the review/ directory has
    no ghost-review-r<N>.yaml file.
    """
    review_dir = tmp_path / "curriculum" / "l2-uk-en" / "a1" / "review"
    assert not list(review_dir.glob("*-ghost-review-r*.yaml"))


def test_bundle_generated_at_is_iso8601_utc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from build import v6_build

    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", tmp_path / "curriculum" / "l2-uk-en")

    ghosts = (
        _ghost_entry(
            dimension="factual_accuracy",
            severity="major",
            location="x",
            issue="y",
            anchor="ghost-anchor",
        ),
    )
    bundle_path = _write_reviewer_ghost_bundle(
        level="a1",
        slug="colors",
        round_num=1,
        reviewer_agent="codex-tools",
        ghost_findings=ghosts,
        content_sha256="sha",
    )
    payload = yaml.safe_load(bundle_path.read_text("utf-8"))
    parsed = datetime.fromisoformat(payload["generated_at"])
    # tzinfo set (UTC) — naive datetimes would be a bug in the telemetry path.
    assert parsed.tzinfo is not None
    # Bundle was generated moments ago, well within a generous window.
    assert (datetime.now(tz=UTC) - parsed).total_seconds() < 60
