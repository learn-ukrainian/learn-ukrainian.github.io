"""Regression checks for the advisory Hygiene workflow."""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "hygiene.yml"
V4_RUNTIME_SRC = "packages/v4-runtime/src"
V4_RUNTIME_INSTALL = "./packages/v4-runtime"


def test_hygiene_focused_agent_config_tests_can_import_v4_runtime() -> None:
    """Slim Hygiene venv must expose learn_ukrainian_v4_runtime.

    ``scripts/agent_runtime/agent_identity.py`` is a compat alias that imports
    the package. CI Gate installs it; Hygiene historically installed only
    pytest + PyYAML and failed 12 tool-config cases with ModuleNotFoundError.
    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["hygiene-checks"]["steps"]
    focused = next(
        step for step in steps if step.get("name") == "Run focused agent config tests"
    )

    assert "tests/test_agent_runtime_tool_config.py" in focused["run"]

    pythonpath = str((focused.get("env") or {}).get("PYTHONPATH", ""))
    installs_package = any(V4_RUNTIME_INSTALL in str(step.get("run", "")) for step in steps)
    assert V4_RUNTIME_SRC in pythonpath or installs_package, (
        "Hygiene must put packages/v4-runtime on PYTHONPATH or pip-install it "
        "before running test_agent_runtime_tool_config.py"
    )
