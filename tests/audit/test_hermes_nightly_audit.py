from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.audit import hermes_nightly_audit as audit

pytestmark = pytest.mark.reads_content


def test_main_writes_only_to_designated_path(tmp_path, monkeypatch):
    # Mock project root to point to tmp_path
    monkeypatch.setattr(audit, "PROJECT_ROOT", tmp_path)

    # Mock run_track_audit to avoid running actual subprocesses during unit tests
    def dummy_run_track_audit(track):
        return {
            "summary": {
                "findings_total": 0,
                "findings_by_severity": {
                    "blocker": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                },
                "modules_selected": 1,
                "modules_built": 1,
                "modules_not_built": 0,
            },
            "findings": [],
        }

    monkeypatch.setattr(audit, "run_track_audit", dummy_run_track_audit)
    monkeypatch.setattr(audit, "get_hermes_insights", lambda cmd: "mocked insights")

    # Mock CLI arguments
    test_args = ["--tracks", "a1", "--insights-cmd", "hermes"]
    with patch("sys.argv", ["scripts/audit/hermes_nightly_audit.py", *test_args]):
        exit_code = audit.main()

    assert exit_code == 0

    # Assert reports are written under tmp_path / "batch_state" / "hermes_cron"
    cron_dir = tmp_path / "batch_state" / "hermes_cron"
    assert cron_dir.exists()

    # Verify latest files exist
    assert (cron_dir / "latest.md").exists()
    assert (cron_dir / "latest.json").exists()

    # Verify we also have timestamped files
    files = list(cron_dir.glob("audit_*.md"))
    assert len(files) == 1

    # Assert NO writes outside batch_state/hermes_cron/
    # All files inside tmp_path must be under batch_state/hermes_cron/
    all_files = [p for p in tmp_path.glob("**/*") if p.is_file()]
    for p in all_files:
        assert p.relative_to(tmp_path).parts[0:2] == ("batch_state", "hermes_cron")
