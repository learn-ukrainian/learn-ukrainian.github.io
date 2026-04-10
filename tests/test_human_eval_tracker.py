"""Tests for scripts/eval/human_eval_tracker.py (#1084)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from eval.human_eval_tracker import (
    DIMENSIONS,
    HumanEval,
    _canonical_dimension,
    build_summary,
    compute_correlation,
    format_report,
    load_evaluations,
    load_llm_scores,
    pearson,
)

# ---------- pearson helper ----------

class TestPearson:
    def test_perfect_positive(self):
        assert pearson([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)

    def test_perfect_negative(self):
        assert pearson([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)

    def test_uncorrelated(self):
        # Constant y series → undefined correlation
        assert pearson([1, 2, 3, 4], [5, 5, 5, 5]) is None

    def test_mismatched_length_is_none(self):
        assert pearson([1, 2], [1, 2, 3]) is None

    def test_single_point_is_none(self):
        assert pearson([1], [1]) is None

    def test_partial_correlation(self):
        r = pearson([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
        assert r is not None
        assert 0.5 < r < 0.9


# ---------- dimension normalization ----------

class TestCanonicalDimension:
    def test_snake_case_pass_through(self):
        assert _canonical_dimension("linguistic_accuracy") == "linguistic_accuracy"

    def test_space_separated(self):
        assert _canonical_dimension("engagement and tone") == "engagement_and_tone"

    def test_ampersand(self):
        assert _canonical_dimension("engagement & tone") == "engagement_and_tone"

    def test_short_alias(self):
        assert _canonical_dimension("linguistic") == "linguistic_accuracy"
        assert _canonical_dimension("vocabulary") == "vocabulary_coverage"
        assert _canonical_dimension("exercise") == "exercise_quality"

    def test_unknown_dimension_returns_none(self):
        assert _canonical_dimension("made_up_dimension") is None


# ---------- loading ----------

class TestLoadEvaluations:
    def _write_eval(self, tmpdir: Path, name: str, data: dict) -> Path:
        path = tmpdir / name
        path.write_text(yaml.safe_dump(data))
        return path

    def test_empty_dir_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            assert load_evaluations(Path(tmp)) == []

    def test_missing_dir_returns_empty_list(self):
        assert load_evaluations(Path("/nonexistent/path")) == []

    def test_load_single_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            self._write_eval(tmpdir, "tetiana-2026-04-10-a1-my-family.yaml", {
                "reviewer": "Tetiana",
                "reviewer_role": "native teacher",
                "evaluated_on": "2026-04-10",
                "module": {"level": "a1", "slug": "my-family"},
                "scores": {
                    "plan_adherence": 9,
                    "linguistic_accuracy": 10,
                    "pedagogical_quality": 8,
                },
                "overall": "Solid.",
                "publishable": True,
            })
            evals = load_evaluations(tmpdir)
            assert len(evals) == 1
            ev = evals[0]
            assert ev.reviewer == "Tetiana"
            assert ev.level == "a1"
            assert ev.slug == "my-family"
            assert ev.module_id == "a1/my-family"
            assert ev.scores["linguistic_accuracy"] == 10
            assert ev.average == pytest.approx(9.0)

    def test_malformed_yaml_is_skipped(self, capsys):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "bad.yaml").write_text("::: not yaml :::\n  - [broken")
            evals = load_evaluations(tmpdir)
            assert evals == []
            captured = capsys.readouterr()
            assert "YAML error" in captured.err


# ---------- summary ----------

class TestBuildSummary:
    def _make(self, slug: str, reviewer: str, scores: dict[str, int]) -> HumanEval:
        return HumanEval(
            path=Path("/dev/null"),
            reviewer=reviewer,
            reviewer_role="native teacher",
            evaluated_on="2026-04-10",
            level="a1",
            slug=slug,
            scores=scores,
        )

    def test_empty(self):
        s = build_summary([])
        assert s["count"] == 0
        assert s["golden_reference"] == []

    def test_golden_reference_at_9(self):
        evals = [
            self._make("a", "T", {d: 10 for d in DIMENSIONS}),
            self._make("b", "T", {d: 9 for d in DIMENSIONS}),
            self._make("c", "T", {d: 8 for d in DIMENSIONS}),
        ]
        s = build_summary(evals)
        assert s["count"] == 3
        assert "a1/a" in s["golden_reference"]
        assert "a1/b" in s["golden_reference"]
        assert "a1/c" not in s["golden_reference"]

    def test_fix_candidates_at_7(self):
        evals = [
            self._make("a", "T", {d: 7 for d in DIMENSIONS}),
            self._make("b", "T", {d: 6 for d in DIMENSIONS}),
            self._make("c", "T", {d: 8 for d in DIMENSIONS}),
        ]
        s = build_summary(evals)
        assert "a1/a" in s["fix_candidates"]
        assert "a1/b" in s["fix_candidates"]
        assert "a1/c" not in s["fix_candidates"]

    def test_reviewers_deduped(self):
        evals = [
            self._make("a", "Tetiana", {d: 8 for d in DIMENSIONS}),
            self._make("b", "Tetiana", {d: 9 for d in DIMENSIONS}),
            self._make("c", "Alona", {d: 7 for d in DIMENSIONS}),
        ]
        s = build_summary(evals)
        assert s["reviewers"] == ["Alona", "Tetiana"]

    def test_mean_overall_correct(self):
        evals = [
            self._make("a", "T", {d: 8 for d in DIMENSIONS}),
            self._make("b", "T", {d: 10 for d in DIMENSIONS}),
        ]
        s = build_summary(evals)
        assert s["mean_overall"] == pytest.approx(9.0)


# ---------- correlation ----------

class TestComputeCorrelation:
    def test_missing_llm_scores_tracked(self):
        ev = HumanEval(
            path=Path("/dev/null"),
            reviewer="T",
            reviewer_role="native teacher",
            evaluated_on="2026-04-10",
            level="a1",
            slug="no-such-module",
            scores={"linguistic_accuracy": 9},
        )
        with patch("eval.human_eval_tracker.load_llm_scores", return_value=None):
            c = compute_correlation([ev])
        assert "a1/no-such-module" in c["missing_llm_scores"]
        assert c["per_dimension"]["linguistic_accuracy"]["n"] == 0

    def test_correlation_computed_when_llm_present(self):
        evals = [
            HumanEval(
                path=Path("/dev/null"),
                reviewer="T",
                reviewer_role="native teacher",
                evaluated_on="2026-04-10",
                level="a1",
                slug=f"m{i}",
                scores={"linguistic_accuracy": s},
            )
            for i, s in enumerate([8, 9, 10])
        ]
        fake_llm = {"a1/m0": 8.0, "a1/m1": 9.0, "a1/m2": 10.0}

        def fake_loader(level: str, slug: str) -> dict[str, float]:
            return {"linguistic_accuracy": fake_llm[f"{level}/{slug}"]}

        with patch("eval.human_eval_tracker.load_llm_scores", side_effect=fake_loader):
            c = compute_correlation(evals)
        assert c["per_dimension"]["linguistic_accuracy"]["n"] == 3
        assert c["per_dimension"]["linguistic_accuracy"]["pearson_r"] == pytest.approx(1.0)


# ---------- report formatting ----------

class TestFormatReport:
    def test_empty_report_explains_next_step(self):
        summary = build_summary([])
        correlation = {"per_dimension": {}, "per_module": [], "missing_llm_scores": []}
        text = format_report(summary, correlation)
        assert "No evaluations loaded" in text
        assert "docs/eval/human-eval-rubric.md" in text

    def test_non_empty_report_has_sections(self):
        ev = HumanEval(
            path=Path("/dev/null"),
            reviewer="Tetiana",
            reviewer_role="native teacher",
            evaluated_on="2026-04-10",
            level="a1",
            slug="my-family",
            scores={d: 9 for d in DIMENSIONS},
        )
        summary = build_summary([ev])
        with patch("eval.human_eval_tracker.load_llm_scores", return_value=None):
            correlation = compute_correlation([ev])
        text = format_report(summary, correlation)
        assert "HUMAN EVALUATION TRACKER" in text
        assert "Tetiana" in text
        assert "a1/my-family" in text
        assert "Golden reference" in text


# ---------- LLM score loading ----------

class TestLoadLlmScores:
    def test_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("eval.human_eval_tracker.CURRICULUM_ROOT", Path(tmp)):
                assert load_llm_scores("a1", "no-such") is None
