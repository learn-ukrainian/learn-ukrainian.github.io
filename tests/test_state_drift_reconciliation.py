"""Regression tests for state/artifact drift detection and reconciliation (#1304).

Tests:
- _evidence_has_error_keyword negation awareness (dim_floor_fail false positives)
- reconcile_state_artifacts contradiction detection
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build import v6_build

# ---------- _evidence_has_error_keyword tests ----------


class TestEvidenceHasErrorKeyword:
    """Negation-aware keyword matching prevents dim_floor_fail false positives."""

    def test_plain_error_keyword_detected(self) -> None:
        assert v6_build._evidence_has_error_keyword("Contains a factual error in section 3")

    def test_negated_no_prefix_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("No incorrect forms found")

    def test_negated_not_prefix_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Grammar is not wrong in this section")

    def test_negated_without_prefix_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Text is without errors throughout")

    def test_negated_free_of_prefix_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Content is free of mistakes")

    def test_negated_ukrainian_bez_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Текст без помилок")

    def test_negated_ukrainian_ni_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Ні невірних форм")

    def test_negated_absent_prefix_not_detected(self) -> None:
        assert not v6_build._evidence_has_error_keyword("Absent factual issues in the text")

    def test_non_negated_keyword_still_detected_after_negated(self) -> None:
        # "no errors" is negated, but "wrong translation" is not
        assert v6_build._evidence_has_error_keyword(
            "No errors in grammar but has a wrong translation in section 2"
        )

    def test_case_insensitive(self) -> None:
        assert v6_build._evidence_has_error_keyword("Contains an ERROR in the vocabulary")

    def test_empty_evidence(self) -> None:
        assert not v6_build._evidence_has_error_keyword("")

    def test_keyword_at_start_of_string(self) -> None:
        assert v6_build._evidence_has_error_keyword("Incorrect declension used")

    def test_multiple_negated_keywords_all_negated(self) -> None:
        assert not v6_build._evidence_has_error_keyword(
            "No incorrect forms, no wrong translations, without mistakes"
        )

    def test_ukrainian_помилк_detected_without_negation(self) -> None:
        assert v6_build._evidence_has_error_keyword("Знайдено помилки в тексті")

    def test_contradictory_detected(self) -> None:
        assert v6_build._evidence_has_error_keyword("Contains contradictory statements")


class TestDimFloorFailIntegration:
    """_parse_review_result uses negation-aware matching."""

    def _make_review_text(self, dim_score: int, evidence: str) -> str:
        # Format must match the regex in _parse_review_result:
        #   r"\|\s*(\d+)\.\s*([^|]+)\|\s*(\d+)/10\s*\|([^|]*)\|"
        # Need all 9 dimensions for a valid weighted score >= 8.0
        lines = [
            "## Review\n",
            "Verdict: PASS\n",
            "| # | Dimension | Score | Evidence |",
            "|---|-----------|-------|----------|",
        ]
        for i in range(1, 10):
            if i == 2:  # Linguistic accuracy — our test dimension
                lines.append(f"| {i}. Linguistic accuracy | {dim_score}/10 | {evidence} |")
            else:
                lines.append(f"| {i}. Dimension {i} | 10/10 | Excellent |")
        return "\n".join(lines) + "\n"

    def test_negated_evidence_does_not_trigger_dim_floor_fail(self) -> None:
        review_text = self._make_review_text(8, "No incorrect forms found in the text")
        parsed = v6_build._parse_review_result(review_text)
        assert not parsed.dim_floor_fail
        assert parsed.passed  # weighted score >= 8.0, verdict == PASS, no floor fail

    def test_genuine_error_evidence_triggers_dim_floor_fail(self) -> None:
        review_text = self._make_review_text(8, "Incorrect declension of іменник")
        parsed = v6_build._parse_review_result(review_text)
        assert parsed.dim_floor_fail
        assert not parsed.passed


# ---------- reconcile_state_artifacts tests ----------


def _setup_module_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    level: str = "a1",
    slug: str = "test-module",
    state: dict | None = None,
) -> tuple[Path, Path]:
    """Create minimal curriculum structure and return (curriculum_root, orch_dir)."""
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    orch_dir = curriculum_root / level / "orchestration" / slug
    orch_dir.mkdir(parents=True, exist_ok=True)

    if state is not None:
        state_path = orch_dir / "state.json"
        state_path.write_text(json.dumps(state), "utf-8")

    return curriculum_root, orch_dir


class TestReconcileStateArtifacts:
    """reconcile_state_artifacts detects state/artifact contradictions."""

    def test_no_state_file_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_module_state(tmp_path, monkeypatch)
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert contradictions == []

    def test_consistent_state_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "phases": {
                    "write": {"status": "complete", "ts": datetime.now(tz=UTC).isoformat()},
                },
            },
        )
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert contradictions == []

    def test_needs_human_review_state_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "needs_human_review": {"status": True, "ts": "2026-04-17T10:00:00+00:00"},
                "phases": {},
            },
        )
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert len(contradictions) == 1
        assert contradictions[0].kind == "needs_human_review_state_only"

    def test_needs_human_review_artifact_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, orch_dir = _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "phases": {},
            },
        )
        (orch_dir / "needs-human-review.yaml").write_text("slug: test-module\n", "utf-8")
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert len(contradictions) == 1
        assert contradictions[0].kind == "needs_human_review_artifact_only"

    def test_verify_stale_after_content_update(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        old_ts = (datetime.now(tz=UTC) - timedelta(hours=1)).isoformat()
        curriculum_root, _orch_dir = _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "phases": {
                    "verify": {"status": "failed", "ts": old_ts},
                },
            },
        )
        content_path = curriculum_root / "a1" / "test-module.md"
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_text("# Updated content\n", "utf-8")

        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert any(c.kind == "verify_stale_after_content_update" for c in contradictions)

    def test_review_complete_no_artifact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "phases": {
                    "review": {
                        "status": "complete",
                        "ts": datetime.now(tz=UTC).isoformat(),
                    },
                },
            },
        )
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert any(c.kind == "review_complete_no_artifact" for c in contradictions)

    def test_failed_phase_plan_hash_drift(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        curriculum_root, _orch_dir = _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "phases": {
                    "write": {
                        "status": "failed",
                        "ts": datetime.now(tz=UTC).isoformat(),
                        "plan_hash": "old_hash_000000000000",
                    },
                },
            },
        )
        # Create a plan so _current_plan_hash returns something different
        plan_dir = curriculum_root / "plans" / "a1"
        plan_dir.mkdir(parents=True, exist_ok=True)
        (plan_dir / "test-module.yaml").write_text("version: '2.0'\ntitle: Updated\n", "utf-8")

        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        assert any(c.kind == "failed_phase_plan_hash_drift" for c in contradictions)

    def test_no_contradiction_when_both_needs_review_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _, orch_dir = _setup_module_state(
            tmp_path,
            monkeypatch,
            state={
                "mode": "v6",
                "track": "a1",
                "slug": "test-module",
                "needs_human_review": {"status": True, "ts": "2026-04-17T10:00:00+00:00"},
                "phases": {},
            },
        )
        (orch_dir / "needs-human-review.yaml").write_text("slug: test-module\n", "utf-8")
        contradictions = v6_build.reconcile_state_artifacts("a1", "test-module")
        # Both present → consistent, no contradiction
        assert not any(c.kind.startswith("needs_human_review") for c in contradictions)
