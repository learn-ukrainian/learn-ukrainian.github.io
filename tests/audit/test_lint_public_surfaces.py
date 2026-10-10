"""Publication surfaces reject infrastructure text the file scanner never sees."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts.audit.lint_public_surfaces import scan_text
from scripts.opsec.needles import Needles

_NEEDLES = Needles()
_ROOT = Path(__file__).resolve().parents[2]
_SECRET_PATH = "/home/example/repo"


def test_host_path_file_uri_private_host_and_private_ip_are_findings() -> None:
    private_ip = ".".join(("10", "1", "2", "3"))
    text = "\n".join(
        (
            f"built at {_SECRET_PATH}",
            "log file:///var/run/app",
            "db.internal",
            f"peer {private_ip}",
        )
    )
    rules = {item.rule for item in scan_text(text, field="body", needles=_NEEDLES)}
    assert rules == {"host-path", "file-uri", "private-host", "private-ipv4"}


def test_clean_learner_text_has_no_findings() -> None:
    assert scan_text("Fix the learner card for module 3.", field="title", needles=_NEEDLES) == []


def test_cli_reports_the_rule_and_not_the_matched_text(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PR_TITLE"] = f"wip {_SECRET_PATH}"
    env["PR_BODY"] = ""
    env["PR_BRANCH"] = "cursor/example"
    completed = subprocess.run(
        [sys.executable, "scripts/audit/lint_public_surfaces.py"],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 1
    assert "title host-path" in completed.stdout
    assert _SECRET_PATH not in completed.stdout
    assert _SECRET_PATH not in completed.stderr
    assert "example" not in completed.stdout
