"""Shared imports preserve direct-file and sibling-module reader entry points."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonl_reader_cases import VALUE

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "path",
    [
        "scripts/audit/_judge_eval_lib.py",
        "scripts/audit/opencode_judge_calibration.py",
        "scripts/audit/score_judge_calibration.py",
        "scripts/audit/bakeoff_aggregate.py",
        "scripts/ai_agent_bridge/_opencode.py",
        "scripts/ai_agent_bridge/_ui_agy.py",
        "scripts/ai_agent_bridge/_ui_codex.py",
        "scripts/atlas/lexical_projection.py",
        "scripts/dataset/audit_literary_poltava_candidate.py",
        "scripts/eval/zno_nmt/mcp_proxy.py",
        "scripts/projects/open_model_data/correction_factory.py",
        "scripts/projects/open_model_data/v5_pretraining_contradiction_audit.py",
        "scripts/projects/open_model_data/validate_source_records.py",
        "scripts/projects/open_model_data/v5_evaluation_harness.py",
        "scripts/projects/ua_eval_harness/build_v02_review_packet.py",
        "scripts/projects/ua_eval_harness/run_codex_baseline.py",
        "scripts/projects/ua_eval_harness/run_model_batch.py",
        "scripts/projects/ua_open_weight_eval/hf_jobs_worker.py",
    ],
)
def test_supported_reader_import_entrypoint(path):
    source = ROOT / path
    statement = f"import {source.stem}"
    if source.stem == "_opencode":
        # This transport has always been package-only; its relative imports
        # are resolved by the bridge launcher, not sibling-module import.
        statement = f"import sys; sys.path.insert(0, {str(ROOT)!r}); import scripts.ai_agent_bridge._opencode"
    result = subprocess.run(
        [sys.executable, "-c", statement],
        cwd=source.parent,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("ending", ["\n", "\r\n", ""], ids=["LF", "CRLF", "unterminated"])
def test_flat_worker_preserves_unicode_records(ending, tmp_path):
    worker = tmp_path / "hf_jobs_worker.py"
    worker.write_bytes((ROOT / "scripts/projects/ua_open_weight_eval/hf_jobs_worker.py").read_bytes())
    record = {"probe": VALUE, "prediction": VALUE}
    (tmp_path / "fixture.jsonl").write_bytes((json.dumps(record, ensure_ascii=False) + ending).encode("utf-8"))
    statement = (
        "from pathlib import Path; import hf_jobs_worker; "
        f"assert hf_jobs_worker.read_jsonl(Path('fixture.jsonl')) == {[record]!r}"
    )
    result = subprocess.run(
        [sys.executable, "-c", statement], cwd=tmp_path, capture_output=True, text=True, timeout=30, check=False
    )
    assert result.returncode == 0, result.stderr


def test_flat_worker_cli_entrypoint(tmp_path):
    worker = tmp_path / "hf_jobs_worker.py"
    worker.write_bytes((ROOT / "scripts/projects/ua_open_weight_eval/hf_jobs_worker.py").read_bytes())
    result = subprocess.run(
        [sys.executable, str(worker), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
