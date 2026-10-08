"""Regression checks for the advisory Hygiene workflow."""

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from packaging.requirements import Requirement

from tests.ci.hygiene_import_guard import HygieneImportsOnly

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
        for req in (Requirement(line) for line in (tmp_path / "hygiene-constraints.txt").read_text().splitlines())
    }
    assert declared.keys() == {"pytest", "pyyaml", "jsonschema", "psutil"}
    expected_pins = {
        line
        for line in (REPO_ROOT / "requirements-lock.txt").read_text().splitlines()
        if line and line[0].isalnum() and "==" in line
    }
    assert set((tmp_path / "hygiene-constraints.txt").read_text().splitlines()) == expected_pins
    assert declared.keys() <= locked.keys()
    for name, req in locked.items():
        (pin,) = req.specifier
        assert pin.operator == "=="
        if name in declared:
            assert pin.version in declared[name].specifier
    assert '-r "$RUNNER_TEMP/hygiene-requirements.txt"' in install["run"]
    assert '-c "$RUNNER_TEMP/hygiene-constraints.txt"' in install["run"]


@pytest.mark.parametrize("missing", [None, "jsonschema", "requests"])
@pytest.mark.parametrize("shard_files", [None, "ci-artifacts/pytest-shard-1-files.txt"])
def test_hygiene_environment_guard_checks_fixture_imports(
    missing: str | None,
    shard_files: str | None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if shard_files is None:
        monkeypatch.delenv("LU_PYTEST_SHARD_FILES", raising=False)
    else:
        monkeypatch.setenv("LU_PYTEST_SHARD_FILES", shard_files)
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
    # Derive roots from the install selectors rather than allowing CI Gate's
    # much larger environment. The metadata closure excludes unselected extras.
    install = next(step for step in steps if step.get("name") == "Create local test venv")
    selectors = "\n".join(line for line in install["run"].splitlines() if line.startswith("sed "))
    selected = subprocess.run(
        ["bash", "-eu", "-c", selectors],
        cwd=REPO_ROOT,
        env={**os.environ, "RUNNER_TEMP": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert selected.returncode == 0, selected.stderr
    requirements = tmp_path / "hygiene-requirements.txt"
    cwd = REPO_ROOT
    if missing == "requests":
        # Copy the shared conftest; all other inputs still come from this tree.
        # This is the reviewer's fixture-time mutation, never a live-tree edit.
        cwd = tmp_path / "repo"
        cwd.mkdir()
        # Only focused collection inputs are linked; package helpers resolve
        # through the original tests package, without a hand list of names.
        inputs = [
            ".git",
            "pyproject.toml",
            "scripts",
            "packages",
            *(arg for arg in args if arg.startswith("tests/")),
        ]
        for relative in inputs:
            entry = REPO_ROOT / relative
            target = cwd / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(entry, target_is_directory=entry.is_dir())
        (cwd / "tests/__init__.py").write_text(
            (REPO_ROOT / "tests/__init__.py").read_text() + f"\n__path__.append({str(REPO_ROOT / 'tests')!r})\n"
        )
        conftest = (REPO_ROOT / "tests/conftest.py").read_text()
        (cwd / "tests/conftest.py").write_text(
            conftest + "\n@pytest.fixture(autouse=True)\ndef undeclared_hygiene_dependency():\n    import requests\n"
        )
    probe = """
import importlib.metadata
import site
import sys
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from tests.ci.hygiene_import_guard import HygieneImportsOnly

pending = [(Requirement(line.partition("#")[0].strip()).name, frozenset())
           for line in Path(sys.argv[1]).read_text().splitlines()]
seen = set()
distributions = set()
while pending:
    name, extras = pending.pop()
    name = canonicalize_name(name)
    if (name, extras) in seen:
        continue
    seen.add((name, extras))
    distributions.add(name)
    for text in importlib.metadata.requires(name) or ():
        req = Requirement(text)
        if req.marker is None or any(req.marker.evaluate({"extra": extra})
                                     for extra in extras or {""}):
            pending.append((req.name, frozenset(req.extras)))
allowed = set(sys.stdlib_module_names)
allowed.update(module for module, providers in importlib.metadata.packages_distributions().items()
               if all(canonicalize_name(provider) in distributions for provider in providers))
roots = (Path.cwd().resolve(), Path(sys.argv[2]).resolve())
site_roots = [Path(root).resolve() for root in (*site.getsitepackages(), site.getusersitepackages())]
missing = sys.argv[3]

sys.meta_path.insert(0, HygieneImportsOnly(allowed, roots, site_roots, missing))
import pytest
raise SystemExit(pytest.main(sys.argv[4:]))
"""
    child_env = {**os.environ, **guard["env"], "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_PLUGINS": ""}
    # The child names its focused files explicitly; the parent's shard path
    # may be relative to a different repository and must not filter them.
    child_env.pop("LU_PYTEST_SHARD_FILES", None)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            probe,
            str(requirements),
            str(REPO_ROOT),
            "jsonschema" if missing == "jsonschema" else "",
            *args,
        ],
        cwd=cwd,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    if missing is None:
        assert result.returncode == 0, output
    else:
        assert result.returncode != 0, output
        if missing == "jsonschema":
            assert "ModuleNotFoundError: No module named 'jsonschema'" in output
        else:
            assert "Hygiene dependency not declared: 'requests'" in output


@pytest.mark.parametrize(
    "kind", ["module", "package", "namespace", "external", "escaping_symlink", "site_package", "mixed_namespace"]
)
def test_hygiene_guard_classifies_resolved_locations(kind: str, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    site_root = repo / ".venv" / "site-packages"
    site_root.mkdir(parents=True)
    module = "new_repository_plugin"
    search = [str(repo)]
    if kind == "package":
        (repo / module).mkdir()
        (repo / module / "__init__.py").write_text("")
    elif kind in {"namespace", "mixed_namespace"}:
        (repo / module).mkdir()
        if kind == "mixed_namespace":
            (outside / module).mkdir()
            search.append(str(outside))
    elif kind == "escaping_symlink":
        external = outside / f"{module}.py"
        external.write_text("")
        (repo / f"{module}.py").symlink_to(external)
    else:
        root = {"module": repo, "external": outside, "site_package": site_root}[kind]
        (root / f"{module}.py").write_text("")
        search = [str(root)]
    finder = HygieneImportsOnly(set(), (repo,), [site_root])
    if kind in {"module", "package", "namespace"}:
        assert finder.find_spec(module, search) is not None
    else:
        with pytest.raises(ModuleNotFoundError, match=f"Hygiene dependency not declared: '{module}'"):
            finder.find_spec(module, search)


def test_hygiene_guard_preserves_declared_and_missing_dependency_controls(tmp_path: Path) -> None:
    finder = HygieneImportsOnly({"pytest", "jsonschema"}, (tmp_path,), [], missing="jsonschema")
    assert finder.find_spec("pytest") is None
    with pytest.raises(ModuleNotFoundError, match="No module named 'jsonschema'"):
        finder.find_spec("jsonschema")
    with pytest.raises(ModuleNotFoundError, match="Hygiene dependency not declared: 'nonexistent_dependency'"):
        finder.find_spec("nonexistent_dependency")


def test_hygiene_focused_agent_config_tests_can_import_v4_runtime() -> None:
    """Slim Hygiene venv must expose learn_ukrainian_v4_runtime.

    ``scripts/agent_runtime/agent_identity.py`` is a compat alias that imports
    the package. CI Gate installs it; Hygiene historically installed only
    pytest + PyYAML and failed 12 tool-config cases with ModuleNotFoundError.
    """
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["hygiene-checks"]["steps"]
    focused = next(step for step in steps if step.get("name") == "Run focused agent config tests")

    assert "tests/test_agent_runtime_tool_config.py" in focused["run"]

    pythonpath = str((focused.get("env") or {}).get("PYTHONPATH", ""))
    installs_package = any(V4_RUNTIME_INSTALL in str(step.get("run", "")) for step in steps)
    assert V4_RUNTIME_SRC in pythonpath or installs_package, (
        "Hygiene must put packages/v4-runtime on PYTHONPATH or pip-install it "
        "before running test_agent_runtime_tool_config.py"
    )
