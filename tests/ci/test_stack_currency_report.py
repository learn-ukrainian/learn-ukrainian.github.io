"""Pinned-versus-latest report: qualifying output, a missing pin, workflow permissions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.ci import stack_currency_report as report
from tests._host_path_guard import assert_no_host_facts, assert_no_host_paths

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "security-audit.yml"
_PINS = _REPO_ROOT / "scripts" / "config" / "stack_pins.yaml"

_ONE_ROW = """\
pins:
  - name: python
    pinned: "3.12.14"
    source: .python-version
    owner: DevOps
    review_by: "2026-11-16"
    note: interpreter pin
"""


def _table(body: str) -> dict[str, list[str]]:
    parsed: dict[str, list[str]] = {}
    for line in body.splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or line.startswith("| component"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        parsed[cells[0]] = cells
    return parsed


def test_qualifying_report_is_versions_and_repo_paths_only() -> None:
    body = report.render_body(report.build_report(_PINS, lambda _name: "9.8.7"))
    rows = _table(body)

    assert rows["python"] == ["python", "3.12.14", "9.8.7", ".python-version"]
    assert rows["entire"][1] == "0.8.42"
    assert rows["entire"][3] == "scripts/entire_context/provider.py"
    assert rows["uv"][3] == ".github/actions/python-ci-env/action.yml"
    assert rows["gh"][1:] == ["unknown", "9.8.7", ""]
    assert "://" not in body
    assert_no_host_paths(body, "stack currency body")
    assert_no_host_facts(body, "stack currency body")


def test_missing_pin_row_does_not_invent_a_latest(tmp_path: Path) -> None:
    pins = tmp_path / "stack_pins.yaml"
    pins.write_text(
        _ONE_ROW
        + """\
  - name: uv
    source: .github/actions/python-ci-env/action.yml
    owner: DevOps
    review_by: "2026-11-16"
    note: pin value absent
""",
        encoding="utf-8",
    )
    called: list[str] = []

    def latest_of(name: str) -> str:
        called.append(name)
        return "9.8.7"

    built = report.build_report(pins, latest_of)
    by_name = {row["name"]: row for row in built["rows"]}

    assert by_name["python"]["pinned"] == "3.12.14"
    assert by_name["python"]["latest"] == "9.8.7"
    assert by_name["uv"]["pinned"] == "missing"
    assert by_name["uv"]["latest"] == "unknown"
    assert by_name["uv"]["latest_reason"] == "missing_pin"
    assert called == ["python"]


def test_render_refuses_an_address() -> None:
    unsafe = {
        "rows": [
            {"name": "gh", "pinned": "unknown", "latest": "203.0.113.10", "source": "host"},
        ]
    }
    with pytest.raises(report.PublicationRefused):
        report.render_body(unsafe)


def test_component_without_a_verified_upstream_stays_unknown() -> None:
    assert "prometheus" not in report.UPSTREAMS
    assert report.fetch_latest("prometheus") == "unknown"


def test_version_parsers_keep_stable_tags_only() -> None:
    assert report.version_from_npm({"version": "2.1.302"}) == "2.1.302"
    assert report.version_from_github({"tag_name": "v0.11.5", "draft": False, "prerelease": False}) == "0.11.5"
    assert report.version_from_github({"tag_name": "v0.11.5", "draft": False, "prerelease": True}) == "unknown"
    assert report.version_from_node_index([{"version": "v26.0.0-rc.1"}, {"version": "v24.10.0"}]) == "24.10.0"
    assert report.version_from_python_cycles([{"latest": "3.12.15"}, {"latest": "3.15.0"}]) == "3.15.0"
    assert report.version_from_npm({"version": "1.2.3-rc.1"}) == "unknown"


def test_weekly_job_permissions_are_contents_read_and_issues_write() -> None:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    assert workflow["permissions"] == {"contents": "read"}
    triggers = workflow.get("on", workflow.get(True))
    crons = [entry["cron"] for entry in triggers["schedule"]]
    assert "0 9 * * 1" in crons
    assert "23 4 * * *" in crons

    job = workflow["jobs"]["stack-currency"]
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    condition = job["if"]
    assert "github.event_name == 'schedule'" in condition
    assert "0 9 * * 1" in condition
    assert "23 4 * * *" not in condition
    assert "pull_request" not in condition
    assert "workflow_dispatch" not in condition

    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert "dependency-advisory" in script
    assert "gh issue comment" in script
    assert "gh issue create" not in script
    assert "gh pr" not in script
    for banned in ("automerge", "merge queue", "--auto", "gh pr merge"):
        assert banned not in script


def test_collector_writes_a_local_report_and_does_not_publish(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pins = tmp_path / "stack_pins.yaml"
    pins.write_text(_ONE_ROW, encoding="utf-8")
    monkeypatch.setattr(report, "fetch_latest", lambda _name: "9.8.7")
    destination = tmp_path / "stack-currency.json"
    body_out = tmp_path / "stack-currency.md"

    assert report.main(["collect", "--pins", str(pins), "--out", str(destination)]) == 0
    assert report.main(["render", "--report", str(destination), "--body-out", str(body_out)]) == 0
    saved = json.loads(destination.read_text(encoding="utf-8"))
    by_name = {row["name"]: row for row in saved["rows"]}
    assert by_name["python"]["pinned"] == "3.12.14"
    assert by_name["python"]["latest"] == "9.8.7"
    assert "9.8.7" in body_out.read_text(encoding="utf-8")
    source = Path(report.__file__).read_text(encoding="utf-8")
    assert "gh pr" not in source
    assert "issue create" not in source
    assert "subprocess" not in source


def test_help_follows_cli_help_standard(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        report.main(["--help"])
    assert exc.value.code == 0
    text = capsys.readouterr().out
    for heading in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert heading in text
    assert ".venv/bin/python" in text
