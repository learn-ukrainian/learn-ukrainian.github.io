from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter
from agent_runtime.usage import _iter_usage_records


def test_claude_success_text_with_rate_limited_phrase_is_not_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="Done.\nThe previous soft warning said rate limited, but the task completed.",
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert result.rate_limited is False
    assert result.ok is True


def test_claude_stderr_rate_limit_failure_is_still_rate_limited():
    adapter = ClaudeAdapter()

    result = adapter.parse_response(
        stdout="",
        stderr="Error: rate limit reached, try again later.",
        returncode=1,
        output_file=None,
    )

    assert result.rate_limited is True
    assert result.ok is False


def test_saved_success_record_with_rate_limit_warning_remains_readable(tmp_path):
    record = {
        "task_id": "historical-success",
        "returncode": 0,
        "stderr_excerpt": "Done. The previous soft warning said rate limited, but work finished.",
    }
    path = tmp_path / "usage_fixture.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    unreadable = {"files": 0, "lines": 0, "records": 0}

    assert list(_iter_usage_records(path, unreadable)) == [record]
    assert unreadable == {"files": 0, "lines": 0, "records": 0}
    result = ClaudeAdapter().parse_response(
        stdout=record["stderr_excerpt"],
        stderr="",
        returncode=record["returncode"],
        output_file=None,
    )
    assert result.ok is True
    assert result.rate_limited is False
    assert json.loads(path.read_text(encoding="utf-8")) == record
