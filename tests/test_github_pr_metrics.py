"""GitHub PR metrics (mocked gh)."""

from __future__ import annotations

import json
from unittest.mock import patch

from scripts.fleet_comms.github_pr_metrics import collect_github_pr_metrics


def test_github_metrics_no_content(monkeypatch=None) -> None:
    payload = {
        "number": 1,
        "title": "SECRET TITLE SHOULD NOT APPEAR",
        "createdAt": "2026-07-21T10:00:00Z",
        "mergedAt": "2026-07-21T10:10:00Z",
        "additions": 10,
        "deletions": 2,
        "changedFiles": 3,
    }

    class Proc:
        returncode = 0
        stdout = json.dumps([payload])
        stderr = ""

    with patch("scripts.fleet_comms.github_pr_metrics.subprocess.run", return_value=Proc()):
        out = collect_github_pr_metrics(limit=5)
    assert out["ok"] is True
    assert out["content_included"] is False
    assert out["n"] == 1
    assert out["open_to_merge_seconds"]["avg"] == 600.0
    sample = out["samples"][0]
    assert "title" not in sample
    assert sample["number"] == 1
    assert "SECRET" not in json.dumps(out)
