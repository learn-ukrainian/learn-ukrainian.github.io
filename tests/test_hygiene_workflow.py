"""Regression checks for the advisory Hygiene workflow."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from packaging.requirements import Requirement

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "hygiene.yml"
V4_RUNTIME_SRC = "packages/v4-runtime/src"
V4_RUNTIME_INSTALL = "./packages/v4-runtime"


def test_hygiene_installs_declared_requirements_with_locked_versions(tmp_path: Path) -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["hygiene-checks"]["steps"]
    install = next(step for step in steps if step.get("name") == "Create local test venv")
    selectors = "\n".join(line for line in install["run"].splitlines() if line.startswith("sed "))
    result = subprocess.run(
        ["bash", "-eu", "-c", selectors],
        cwd=REPO_ROOT,
        env={**os.environ, "RUNNER_TEMP": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    declared = {
        req.name.lower(): req
        for req in (
            Requirement(line.partition("#")[0].strip())
            for line in (tmp_path / "hygiene-requirements.txt").read_text().splitlines()
        )
    }
    locked = {
        req.name.lower(): req
        for req in (
            Requirement(line)
            for line in (tmp_path / "hygiene-constraints.txt").read_text().splitlines()
        )
    }
    assert declared.keys() == locked.keys() == {"pytest", "pyyaml", "jsonschema", "psutil"}
    for name, req in locked.items():
        (pin,) = req.specifier
        assert pin.operator == "=="
        assert pin.version in declared[name].specifier
    assert '-r "$RUNNER_TEMP/hygiene-requirements.txt"' in install["run"]
    assert '-c "$RUNNER_TEMP/hygiene-constraints.txt"' in install["run"]


@pytest.mark.parametrize("missing", [None, "jsonschema"])
def test_hygiene_environment_guard_checks_fixture_imports(missing: str | None) -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["hygiene-checks"]["steps"]
    guard = next(step for step in steps if step.get("name") == "Guard focused test collection and setup")
    focused = next(step for step in steps if step.get("name") == "Run focused agent config tests")
    assert steps.index(guard) < steps.index(focused)
    assert guard.get("env") == focused.get("env")
    args = shlex.split(guard["run"].replace("\\\n", ""))[3:]
    focused_args = shlex.split(focused["run"].replace("\\\n", ""))[3:]
    assert [arg for arg in args if arg.startswith("tests/")] == [
        arg for arg in focused_args if arg.startswith("tests/")
    ]
    assert "--setup-only" in args
    probe = """
import importlib.abc
import sys
import pytest

class MissingDependency(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition('.')[0] == sys.argv[1]:
            raise ModuleNotFoundError(f"No module named '{fullname}'", name=fullname)

sys.meta_path.insert(0, MissingDependency())
raise SystemExit(pytest.main(sys.argv[2:]))
"""
    result = subprocess.run(
        [sys.executable, "-c", probe, missing or "", *args],
        cwd=REPO_ROOT,
        env={**os.environ, **guard["env"], "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_PLUGINS": ""},
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    if missing is None:
        assert result.returncode == 0, output
    else:
        assert result.returncode != 0, output
        assert f"ModuleNotFoundError: No module named '{missing}'" in output


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
