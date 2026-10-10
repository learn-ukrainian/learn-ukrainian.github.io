"""Publication surfaces reject infrastructure text the file scanner never sees."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.audit import lint_public_surfaces
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


def _run_event(tmp_path: Path, payload: dict, event_name: str) -> subprocess.CompletedProcess[str]:
    event = tmp_path / "event.json"
    event.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            "scripts/audit/lint_public_surfaces.py",
            "--event-file",
            str(event),
            "--event-name",
            event_name,
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_cli_reports_the_rule_and_not_the_matched_text(tmp_path: Path) -> None:
    completed = _run_event(
        tmp_path,
        {
            "pull_request": {
                "title": f"wip {_SECRET_PATH}",
                "body": "",
                "head": {"ref": "cursor/example", "sha": ""},
                "base": {"sha": ""},
            }
        },
        "pull_request",
    )
    assert completed.returncode == 1
    assert "title host-path" in completed.stdout
    assert _SECRET_PATH not in completed.stdout
    assert _SECRET_PATH not in completed.stderr
    assert "example" not in completed.stdout


def _pull_request_event(tmp_path: Path, title: str) -> Path:
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "title": title,
                    "body": "",
                    "head": {"ref": "cursor/example", "sha": "a" * 40},
                    "base": {"sha": "b" * 40},
                }
            }
        ),
        encoding="utf-8",
    )
    return event


def test_a_shallow_miss_does_not_fail_a_clean_pull_request(tmp_path: Path, monkeypatch) -> None:
    def missing(_base: str, _head: str) -> str:
        raise subprocess.CalledProcessError(128, ["git", "log"])

    monkeypatch.setattr(lint_public_surfaces, "commit_message_text", missing)
    monkeypatch.setattr(lint_public_surfaces, "_is_shallow_checkout", lambda: True)
    event = _pull_request_event(tmp_path, "Fix the learner card")
    assert lint_public_surfaces.main(["--event-file", str(event), "--event-name", "pull_request"]) == 0


def test_a_shallow_miss_still_flags_a_dirty_title(tmp_path: Path, monkeypatch) -> None:
    def missing(_base: str, _head: str) -> str:
        raise subprocess.CalledProcessError(128, ["git", "log"])

    monkeypatch.setattr(lint_public_surfaces, "commit_message_text", missing)
    monkeypatch.setattr(lint_public_surfaces, "_is_shallow_checkout", lambda: True)
    event = _pull_request_event(tmp_path, f"wip {_SECRET_PATH}")
    assert lint_public_surfaces.main(["--event-file", str(event), "--event-name", "pull_request"]) == 1


def test_a_full_checkout_miss_fails(tmp_path: Path, monkeypatch) -> None:
    def missing(_base: str, _head: str) -> str:
        raise subprocess.CalledProcessError(128, ["git", "log"])

    monkeypatch.setattr(lint_public_surfaces, "commit_message_text", missing)
    monkeypatch.setattr(lint_public_surfaces, "_is_shallow_checkout", lambda: False)
    event = _pull_request_event(tmp_path, "Fix the learner card")
    assert lint_public_surfaces.main(["--event-file", str(event), "--event-name", "pull_request"]) == 1


def test_direct_push_commit_message_is_scanned(tmp_path: Path) -> None:
    completed = _run_event(
        tmp_path,
        {
            "ref": "refs/heads/main",
            "before": "0" * 40,
            "after": "a" * 40,
            "commits": [{"message": f"land {_SECRET_PATH}"}],
        },
        "push",
    )
    assert completed.returncode == 1
    assert "commit host-path" in completed.stdout
    assert _SECRET_PATH not in completed.stdout
    assert _SECRET_PATH not in completed.stderr
