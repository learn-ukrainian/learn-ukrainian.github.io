"""Source-blind public CLI behavior using synthetic examples only."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.eval.zno_nmt.__main__ import public_aggregate
from scripts.eval.zno_nmt.core import ExamError
from scripts.eval.zno_nmt.importers import import_zno


def metadata():
    return {
        "title": "Synthetic", "subject": "synthetic", "year": 2026,
        "provenance": {"source_url": "https://example.org/test", "source_revision": "v1",
                       "license": "synthetic", "exposure": "public-exposure-possible"},
        "scoring": {"kind": "benchmark", "policy_url": None, "pass_threshold": None,
                    "expected_items": 1, "expected_points": 1},
    }


def source():
    return [{"test_id": "1", "num_tasks": 1, "tasks": [{
        "task_id": 0, "question": "Choose X.", "answers": [
            {"answer": "A", "text": "X"}, {"answer": "B", "text": "Y"}],
        "answer_vheader": ["A", "B"], "answer_hheader": [], "correct_answer": ["A"],
        "comment": "SECRET EXPLANATION", "with_photo": False,
    }]}]


def test_import_does_not_copy_explanations():
    exam = import_zno(source(), "1", metadata())
    assert "SECRET EXPLANATION" not in json.dumps(exam)
    assert exam["items"][0]["id"] == "1"


def test_complete_import_rejects_images_and_count_drift():
    paper = source()
    paper[0]["tasks"][0]["with_photo"] = True
    with pytest.raises(ExamError, match="image"):
        import_zno(paper, "1", metadata())
    paper = source()
    paper[0]["num_tasks"] = 2
    with pytest.raises(ExamError, match="count"):
        import_zno(paper, "1", metadata())


def test_export_is_allowlisted_and_cannot_copy_text():
    report = {"raw_points": 1, "max_points": 2, "passed": None,
              "items": [{"answer": "private"}], "identity": {"secret": "private"},
              "metrics": {"elapsed_seconds": 2.0, "endpoint": "private"},
              "denominator": {"expected_items": 2, "prompt": "private"},
              "raw_points_delta": "private", "tool_calls": ["private"]}
    result = public_aggregate(report)
    assert "private" not in json.dumps(result)
    assert result["raw_points"] == 1
    assert result["metrics"] == {"elapsed_seconds": 2.0}
    assert "raw_points_delta" not in result


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "scripts.eval.zno_nmt", *map(str, args)],
                          capture_output=True, text=True, timeout=20, cwd=Path(__file__).resolve().parents[2])


def test_cli_separates_key_and_refuses_overwrite(tmp_path):
    exam = tmp_path / "exam.json"
    exam.write_text(json.dumps(import_zno(source(), "1", metadata())))
    packet, key = tmp_path / "questions.json", tmp_path / "key.json"
    result = run_cli("prepare", "--exam", exam, "--questions", packet, "--key", key)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(packet.read_text())
    assert "correct" not in json.dumps(data)
    assert "SECRET" not in packet.read_text()
    assert packet.stat().st_mode & 0o777 == 0o600
    assert key.stat().st_mode & 0o777 == 0o600
    assert run_cli("prepare", "--exam", exam, "--questions", packet, "--key", key).returncode == 2


def test_runner_cli_cannot_accept_key():
    result = run_cli("run", "--key", "private")
    assert result.returncode == 2
