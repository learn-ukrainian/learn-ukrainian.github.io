"""Publication surfaces reject infrastructure text the file scanner never sees."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
from io import BytesIO
from pathlib import Path

import pytest

from scripts.audit import lint_public_surfaces
from scripts.audit.lint_public_surfaces import scan_text
from scripts.common import github_client
from scripts.opsec.needles import Needles

_NEEDLES = Needles()
_ROOT = Path(__file__).resolve().parents[2]
_SECRET_PATH = "/home/example/repo"


@pytest.mark.parametrize(
    "event_text, expected_code, expected_stdout, expected_stderr",
    [
        (
            json.dumps({"pull_request": {"title": "Fix the learner card", "body": "", "head": {"ref": "fix/card"}}}),
            0,
            "OPSEC publication surfaces clean.\n",
            "",
        ),
        (
            json.dumps({"pull_request": {"title": f"wip {_SECRET_PATH}", "body": "", "head": {"ref": "fix/card"}}}),
            1,
            "title host-path line=1\n",
            "OPSEC publication surfaces blocked: 1 finding(s).\n",
        ),
        ("{", 1, "", "OPSEC publication surfaces: event payload could not be read.\n"),
    ],
    ids=["clean", "flagged", "malformed"],
)
def test_cli_in_the_pr_body_workflow_sparse_checkout(
    tmp_path: Path, monkeypatch, event_text, expected_code, expected_stdout, expected_stderr
) -> None:
    sparse_files = {
        "scripts/audit/lint_pr_closing_references.py",
        "scripts/audit/lint_public_surfaces.py",
        "scripts/audit/lint_opsec_leaks.py",
        "scripts/opsec/__init__.py",
        "scripts/opsec/needles.py",
        ".python-version",
    }
    checkout = tmp_path / "checkout"
    for relative in sparse_files:
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_ROOT / relative, target)
    assert {path.relative_to(checkout).as_posix() for path in checkout.rglob("*") if path.is_file()} == sparse_files
    event = tmp_path / "event.json"
    event.write_text(event_text, encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(_ROOT))
    monkeypatch.setenv("LU_PUBLICATION_LIVE", "1")
    environment = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "LU_PUBLICATION_LIVE", "GITHUB_TOKEN", "GH_TOKEN"):
        environment.pop(name, None)
    environment["LU_OPSEC_NEEDLES_FILE"] = ""
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "scripts/audit/lint_public_surfaces.py",
            "--event-file",
            str(event),
            "--event-name",
            "pull_request",
        ],
        cwd=checkout,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == expected_code
    assert completed.stdout == expected_stdout
    assert completed.stderr == expected_stderr


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


def test_current_pull_request_uses_shared_client(monkeypatch, capsys) -> None:
    live = {"title": "Fix the learner card", "body": "", "head": {"ref": "cursor/example"}}

    def response(request, *, timeout):
        assert request.full_url == "https://api.github.com/repos/o/r/pulls/7"
        assert request.get_method() == "GET"
        assert request.get_header("Authorization") == "Bearer synthetic-token"
        assert request.get_header("Accept") == "application/vnd.github+json"
        assert request.get_header("User-agent") == "lint-public-surfaces"
        assert request.get_header("X-github-api-version") == "2022-11-28"
        assert timeout == 30
        return BytesIO(json.dumps(live).encode("utf-8"))

    monkeypatch.setattr(github_client, "http_open", response)
    assert lint_public_surfaces.current_pull_request("o/r", "7", "synthetic-token") == live
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize(
    "error",
    [
        OSError(_SECRET_PATH),
        urllib.error.URLError(_SECRET_PATH),
        urllib.error.HTTPError("https://api.github.com/repos/o/r/pulls/7", 403, _SECRET_PATH, {}, None),
        TimeoutError(_SECRET_PATH),
        github_client.GitHubRateLimited(0),
    ],
    ids=["io", "url", "http", "timeout", "rate-limit"],
)
def test_current_pull_request_read_failure_is_not_printed(monkeypatch, capsys, error) -> None:
    def unavailable(_request, *, timeout):
        raise error

    monkeypatch.setattr(github_client, "http_open", unavailable)
    with pytest.raises(RuntimeError):
        lint_public_surfaces.current_pull_request("o/r", "7", "synthetic-token")
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize(
    "raw, expected",
    [
        (b"\xff", "UnicodeDecodeError"),
        (b"{", "JSONDecodeError"),
        (b"[]", "unexpected-payload"),
        (b"{}", "unexpected-payload"),
    ],
    ids=["encoding", "json", "array", "missing-title"],
)
def test_current_pull_request_rejects_invalid_metadata(monkeypatch, capsys, raw, expected) -> None:
    monkeypatch.setattr(github_client, "http_open", lambda _request, **_kwargs: BytesIO(raw))
    with pytest.raises(RuntimeError, match=f"^{expected}$"):
        lint_public_surfaces.current_pull_request("o/r", "7", "synthetic-token")
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("matched", [False, True], ids=["clean", "rule-match"])
def test_live_pull_request_replaces_a_stale_title(tmp_path: Path, monkeypatch, capsys, matched) -> None:
    monkeypatch.setenv("LU_PUBLICATION_LIVE", "1")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setattr(
        github_client,
        "http_open",
        lambda _request, **_kwargs: BytesIO(
            json.dumps(
                {
                    "title": f"wip {_SECRET_PATH}" if matched else "Fix the learner card",
                    "body": "",
                    "head": {"ref": "cursor/example"},
                }
            ).encode("utf-8")
        ),
    )
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(
            {
                "pull_request": {
                    "number": 7,
                    "title": "Fix the learner card" if matched else f"wip {_SECRET_PATH}",
                    "body": "",
                    "head": {"ref": "cursor/example", "sha": ""},
                    "base": {"sha": ""},
                }
            }
        ),
        encoding="utf-8",
    )
    assert lint_public_surfaces.main(["--event-file", str(event), "--event-name", "pull_request"]) == int(matched)
    captured = capsys.readouterr()
    assert captured.out == ("title host-path line=1\n" if matched else "OPSEC publication surfaces clean.\n")
    assert captured.err == ("OPSEC publication surfaces blocked: 1 finding(s).\n" if matched else "")


def test_a_missed_live_read_fails_without_the_title(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("LU_PUBLICATION_LIVE", "1")
    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("PR_NUMBER", "7")

    def unavailable(_request, *, timeout):
        raise urllib.error.URLError(_SECRET_PATH)

    monkeypatch.setattr(github_client, "http_open", unavailable)
    event = _pull_request_event(tmp_path, f"wip {_SECRET_PATH}")
    assert lint_public_surfaces.main(["--event-file", str(event), "--event-name", "pull_request"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "OPSEC publication surfaces: current pull request text is unavailable.\n"


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
