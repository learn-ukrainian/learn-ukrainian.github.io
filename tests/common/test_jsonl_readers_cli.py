"""Shared imports preserve direct-file and sibling-module reader entry points."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonl_reader_cases import VALUE

ROOT = Path(__file__).resolve().parents[2]


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
