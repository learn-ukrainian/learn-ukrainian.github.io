"""Unit coverage for the dependency-advisory tracking issue helper (#9871)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.ci import dependency_advisory_issue as helper

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "security-audit.yml"


def _pip_report() -> dict:
    return {
        "dependencies": [
            {"name": "requests", "version": "2.31.0", "vulns": []},
            {
                "name": "urllib3",
                "version": "1.26.0",
                "vulns": [
                    {"id": "PYSEC-2023-0001", "fix_versions": ["1.26.18", "2.0.7"], "aliases": []},
                    {"id": "GHSA-XXXX-YYYY-ZZZZ", "fix_versions": [], "aliases": []},
                ],
            },
        ]
    }


def _npm_vulns() -> dict:
    return {
        "minimist": {
            "severity": "critical",
            "fixAvailable": {"name": "minimist", "version": "1.2.8"},
            "via": [
                {
                    "source": 1067342,
                    "name": "minimist",
                    "title": "Prototype Pollution in minimist",
                    "url": "https://github.com/advisories/GHSA-xvch-5gv4-984h",
                    "severity": "critical",
                }
            ],
        },
        "transitive-pkg": {
            "severity": "high",
            "fixAvailable": False,
            "via": ["minimist"],
        },
        "moderate-pkg": {
            "severity": "moderate",
            "fixAvailable": True,
            "via": [
                {
                    "source": 1,
                    "name": "moderate-pkg",
                    "title": "Moderate thing",
                    "url": "https://github.com/advisories/GHSA-0000-0000-0001",
                    "severity": "moderate",
                }
            ],
        },
    }


def test_collect_python_findings() -> None:
    findings = helper.collect_python_findings(_pip_report())
    assert findings == [
        {
            "ecosystem": "python",
            "package": "urllib3",
            "advisory_id": "PYSEC-2023-0001",
            "severity": "unknown",
            "fixed_version": "1.26.18, 2.0.7",
        },
        {
            "ecosystem": "python",
            "package": "urllib3",
            "advisory_id": "GHSA-XXXX-YYYY-ZZZZ",
            "severity": "unknown",
            "fixed_version": "none",
        },
    ]


def test_collect_python_findings_ignores_malformed_entries() -> None:
    assert helper.collect_python_findings({"dependencies": "nope"}) == []
    assert helper.collect_python_findings({"dependencies": [{"name": "x", "vulns": None}]}) == []


def test_collect_npm_findings_high_critical_only() -> None:
    findings = helper.collect_npm_findings(_npm_vulns(), [], target="site")
    advisories = {(f["package"], f["advisory_id"], f["severity"]) for f in findings}
    assert ("minimist", "GHSA-XVCH-5GV4-984H", "critical") in advisories
    # The transitive chain inherits the blocking severity of its root advisory.
    assert ("transitive-pkg", "transitive dependency", "critical") in advisories
    # Moderate findings do not block today, so they are not reported.
    assert all(f["package"] != "moderate-pkg" for f in findings)


def test_collect_npm_findings_fixed_version() -> None:
    findings = helper.collect_npm_findings(_npm_vulns(), [], target="site")
    minimist = next(f for f in findings if f["package"] == "minimist")
    assert minimist["fixed_version"] == "1.2.8"
    assert minimist["ecosystem"] == "npm (site)"


def test_collect_npm_findings_honors_suppressions() -> None:
    findings = helper.collect_npm_findings(_npm_vulns(), ["GHSA-xvch-5gv4-984h"], target="root")
    # Suppressing the minimist advisory also clears the transitive chain on it.
    assert findings == []


def test_build_issue_body_lists_every_field() -> None:
    findings = helper.collect_python_findings(_pip_report()) + helper.collect_npm_findings(
        _npm_vulns(), [], target="site"
    )
    body = helper.build_issue_body(findings)
    assert "| Ecosystem | Package | Advisory | Severity | Fixed version |" in body
    assert "urllib3" in body
    assert "PYSEC-2023-0001" in body
    assert "1.26.18, 2.0.7" in body
    assert "minimist" in body
    assert "GHSA-XVCH-5GV4-984H" in body
    assert "critical" in body
    assert "#9871" in body
    # Rows are sorted deterministically.
    assert body.index("minimist") < body.index("urllib3")


def test_build_issue_body_escapes_pipes_and_newlines() -> None:
    body = helper.build_issue_body(
        [
            {
                "ecosystem": "python",
                "package": "pkg|evil\nname",
                "advisory_id": "PYSEC-1",
                "severity": "unknown",
                "fixed_version": "none",
            }
        ]
    )
    assert "pkg\\|evil name" in body
    assert "\nname" not in body


def test_collect_npm_findings_reports_effective_package_severity() -> None:
    """The issue body shows the effective package severity, not one via entry's."""
    vulns = {
        "minimist": {
            "severity": "critical",
            "fixAvailable": {"name": "minimist", "version": "1.2.8"},
            "via": [
                {
                    "source": 1067342,
                    "name": "minimist",
                    "title": "Prototype Pollution in minimist",
                    "url": "https://github.com/advisories/GHSA-xvch-5gv4-984h",
                    "severity": "critical",
                }
            ],
        },
        # Own advisory is High, but the transitive link to critical minimist
        # raises the effective package severity to Critical.
        "wrapper": {
            "severity": "high",
            "fixAvailable": False,
            "via": [
                {
                    "source": 7,
                    "name": "wrapper",
                    "title": "Wrapper issue",
                    "url": "https://github.com/advisories/GHSA-0000-0000-0002",
                    "severity": "high",
                },
                "minimist",
            ],
        },
    }
    findings = helper.collect_npm_findings(vulns, [], target="root")
    wrapper_rows = [f for f in findings if f["package"] == "wrapper"]
    assert wrapper_rows
    assert all(f["severity"] == "critical" for f in wrapper_rows)


def _completed(returncode: int, stdout: str, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def _fake_repo(root: Path, *, site_lock: bool = True) -> Path:
    root.mkdir()
    (root / "requirements-lock.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    (root / "package.json").write_text("{}\n", encoding="utf-8")
    (root / "package-lock.json").write_text("{}\n", encoding="utf-8")
    (root / "site").mkdir()
    (root / "site" / "package.json").write_text("{}\n", encoding="utf-8")
    if site_lock:
        (root / "site" / "package-lock.json").write_text("{}\n", encoding="utf-8")
    return root


def _stub_audits(pip: subprocess.CompletedProcess, npm: subprocess.CompletedProcess):
    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        if "pip_audit" in cmd:
            return pip
        return npm

    return fake_run


_CLEAN_PIP = _completed(0, json.dumps({"dependencies": []}))
_CLEAN_NPM = _completed(0, json.dumps({"vulnerabilities": {}}))


def test_run_collect_clean_audit_returns_no_findings(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    with patch.object(helper.subprocess, "run", side_effect=_stub_audits(_CLEAN_PIP, _CLEAN_NPM)):
        assert helper.run_collect(repo) == []


def test_run_collect_pip_audit_exit_2_raises(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    pip = _completed(2, json.dumps({"dependencies": []}))
    with patch.object(helper.subprocess, "run", side_effect=_stub_audits(pip, _CLEAN_NPM)):
        with pytest.raises(RuntimeError, match=r"pip-audit failed with exit code 2"):
            helper.run_collect(repo)


def test_run_json_command_unparseable_json_raises(tmp_path: Path) -> None:
    with patch.object(helper.subprocess, "run", return_value=_completed(0, "not json")):
        with pytest.raises(RuntimeError, match=r"pip-audit: failed to parse JSON output"):
            helper._run_json_command(["pip_audit"], cwd=tmp_path, timeout=1, label="pip-audit")


def test_run_json_command_non_object_json_raises(tmp_path: Path) -> None:
    with patch.object(helper.subprocess, "run", return_value=_completed(0, "[1, 2]")):
        with pytest.raises(RuntimeError, match=r"unexpected report format"):
            helper._run_json_command(["npm"], cwd=tmp_path, timeout=1, label="npm audit (root)")


def test_run_collect_unparseable_tool_output_raises(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    pip = _completed(1, "traceback, not json")
    with patch.object(helper.subprocess, "run", side_effect=_stub_audits(pip, _CLEAN_NPM)):
        with pytest.raises(RuntimeError, match=r"failed to parse JSON output"):
            helper.run_collect(repo)


def test_run_collect_npm_error_payload_raises(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    npm = _completed(1, json.dumps({"error": {"summary": "audit endpoint exploded"}}))
    with patch.object(helper.subprocess, "run", side_effect=_stub_audits(_CLEAN_PIP, npm)):
        with pytest.raises(RuntimeError, match=r"npm audit reported an error"):
            helper.run_collect(repo)


def test_run_collect_missing_lockfile_raises(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo", site_lock=False)
    with patch.object(helper.subprocess, "run", side_effect=_stub_audits(_CLEAN_PIP, _CLEAN_NPM)):
        with pytest.raises(RuntimeError, match=r"package\.json or package-lock\.json missing"):
            helper.run_collect(repo)


def test_daily_schedule_runs_only_the_advisory_issue_job() -> None:
    """The daily cron refreshes only the tracking issue; blocking jobs stay weekly (#9871)."""
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))
    crons = [entry["cron"] for entry in triggers["schedule"]]
    assert "23 4 * * *" in crons  # daily advisory refresh
    assert "0 9 * * 1" in crons  # weekly blocking audit
    jobs = workflow["jobs"]
    for name in ("pip-audit", "npm-audit"):
        assert "github.event.schedule != '23 4 * * *'" in jobs[name]["if"], name
    advisory_condition = jobs["advisory-issue"]["if"]
    assert "github.event.schedule == '23 4 * * *'" in advisory_condition


def test_help_follows_cli_help_standard(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        helper.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    for heading in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert heading in out
    assert ".venv/bin/python" in out


def test_collect_help_documents_repo_root_default(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        helper.main(["collect", "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--repo-root" in out
    assert "default:" in out


def test_decide_action() -> None:
    findings = [{"ecosystem": "python", "package": "x", "advisory_id": "a", "severity": "s", "fixed_version": "f"}]
    assert helper.decide_action(findings, "") == "create"
    assert helper.decide_action(findings, "123") == "update"
    assert helper.decide_action([], "123") == "close"
    assert helper.decide_action([], "") == "none"


def test_plan_writes_body_and_outputs_for_findings(tmp_path: Path, monkeypatch, capsys) -> None:
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(
        json.dumps({"findings": helper.collect_python_findings(_pip_report())}),
        encoding="utf-8",
    )
    body_out = tmp_path / "body.md"
    github_output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    rc = helper.main(
        ["plan", "--findings", str(findings_file), "--issue-number", "42", "--body-out", str(body_out)]
    )
    assert rc == 0
    assert "urllib3" in body_out.read_text(encoding="utf-8")
    written = github_output.read_text(encoding="utf-8")
    assert "action=update" in written
    assert "issue_number=42" in written
    assert "action=update" in capsys.readouterr().out


def test_plan_close_action_on_empty_findings(tmp_path: Path, monkeypatch) -> None:
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps({"findings": []}), encoding="utf-8")
    body_out = tmp_path / "body.md"
    github_output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    rc = helper.main(
        ["plan", "--findings", str(findings_file), "--issue-number", "42", "--body-out", str(body_out)]
    )
    assert rc == 0
    assert "action=close" in github_output.read_text(encoding="utf-8")
    assert not body_out.exists()


def test_plan_none_action_when_clean_and_no_issue(tmp_path: Path, monkeypatch) -> None:
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps({"findings": []}), encoding="utf-8")
    github_output = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))
    rc = helper.main(
        ["plan", "--findings", str(findings_file), "--issue-number", "", "--body-out", str(tmp_path / "b.md")]
    )
    assert rc == 0
    assert "action=none" in github_output.read_text(encoding="utf-8")


def test_plan_rejects_malformed_findings_file(tmp_path: Path, monkeypatch) -> None:
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    with pytest.raises(ValueError):
        helper.main(
            ["plan", "--findings", str(findings_file), "--issue-number", "", "--body-out", str(tmp_path / "b.md")]
        )
