"""Static issue-only workflow hardening and supported event contract."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_issue_workflow_hardening():
    text = (ROOT / ".github/workflows/issue-task-quality.yml").read_text()
    workflow = yaml.safe_load(text)
    events = workflow.get("on", workflow.get(True))
    assert events == {"issues": {"types": ["opened", "edited"]}}
    assert "DevOps" in text
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "issue-task-quality-${{ github.event.issue.number }}",
        "cancel-in-progress": False,
    }
    job = workflow["jobs"]["comment"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    steps = job["steps"]
    assert steps[0]["with"]["persist-credentials"] is False
    external = [step["uses"] for step in steps if "uses" in step and not step["uses"].startswith("./")]
    assert all(re.fullmatch(r"[^@]+@[0-9a-f]{40}", action) for action in external)
    assert steps[1]["uses"].startswith("actions/setup-python@")
    assert steps[2]["uses"] == "./.github/actions/python-ci-env"
    for step in steps:
        assert "github.event." not in step.get("run", "")
    assert steps[-1]["run"] == ".venv/bin/python -m scripts.ci.comment_issue_task_quality"
