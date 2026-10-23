"""Tests for scripts/eval/human_eval_tracker.py (#1084)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.reads_content

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from eval.human_eval_tracker import (
    load_evaluations,
)

# ---------- pearson helper ----------


# ---------- dimension normalization ----------


# ---------- loading ----------

class TestLoadEvaluations:
    def _write_eval(self, tmpdir: Path, name: str, data: dict) -> Path:
        path = tmpdir / name
        path.write_text(yaml.safe_dump(data))
        return path

    def test_load_single_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            self._write_eval(tmpdir, "reviewer-a-2026-04-10-a1-my-family.yaml", {
                "reviewer": "ReviewerA",
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
            assert ev.reviewer == "ReviewerA"
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


# ---------- correlation ----------


# ---------- report formatting ----------


# ---------- LLM score loading ----------
