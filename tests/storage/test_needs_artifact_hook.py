"""Tests for the needs_artifact pytest setup hook."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.storage import paths
from tests import conftest


def _item(*args: object, **kwargs: object) -> SimpleNamespace:
    marker = pytest.mark.needs_artifact(*args, **kwargs).mark
    return SimpleNamespace(get_closest_marker=lambda name: marker if name == "needs_artifact" else None)


def test_missing_artifact_skips_with_hydration_command(monkeypatch: pytest.MonkeyPatch) -> None:
    error = paths.MissingArtifactError("group-a", "source.json", "/exact/hydrate-command")

    def missing(group: str, rel: str) -> dict:
        assert (group, rel) == ("group-a", "source.json")
        raise error

    monkeypatch.setattr(paths, "find_entry", missing)
    with pytest.raises(pytest.skip.Exception, match=r"needs_artifact:.*exact/hydrate-command"):
        conftest.pytest_runtest_setup(_item("group-a", "source.json"))


def test_present_artifact_runs_without_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: {"path": "data/source.json"})
    calls = []
    monkeypatch.setattr(paths, "verify_file", lambda path, entry, **kw: calls.append((path, entry, kw)))
    assert conftest.pytest_runtest_setup(_item("group-a", "source.json")) is None
    assert calls == [
        (paths.DATA_ROOT / "source.json", {"path": "data/source.json"}, {"group": "group-a", "rel": "source.json"})
    ]


def test_corrupt_artifact_fails_instead_of_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    error = paths.MissingArtifactError("group-a", "source.json", "/exact/hydrate-command", "sha256 mismatch")
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: {"path": "data/source.json"})
    monkeypatch.setattr(paths, "verify_file", lambda path, entry, **kw: (_ for _ in ()).throw(error))
    with pytest.raises(paths.MissingArtifactError, match="sha256 mismatch"):
        conftest.pytest_runtest_setup(_item("group-a", "source.json"))


def test_needs_artifact_requires_two_positional_arguments() -> None:
    with pytest.raises(pytest.UsageError, match=r"exactly \(group, rel\)"):
        conftest.pytest_runtest_setup(_item("group-a"))


def test_ci_audits_collection_and_runtime_skips_from_all_configured_roots() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    audit = workflow.split("  needs-artifact-audit:", 1)[1].split("  contracts:", 1)[0]
    assert "needs.changes.outputs.docs_only == 'false'" in audit
    assert "pytest --collect-only -m needs_artifact" in audit
    assert "git ls-files | grep -E" in audit
    assert "collected != expected" in audit
    assert "expected - artifact_skips" in audit and "artifact_skips - expected" in audit
    assert "::group::" in audit
    assert "tail -n 200 ci-artifacts/needs-artifact-collected.txt" in audit
    assert "::endgroup::" in audit
    assert "actions/upload-artifact" in audit
    assert "if: failure()" in audit
    assert "path: ci-artifacts/" in audit
    assert "retention-days: 7" in audit


def _extract_needs_artifact_step_run_script() -> str:
    workflow_path = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    doc = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    for job in doc.get("jobs", {}).values():
        for step in job.get("steps", []):
            if step.get("name") == "Verify needs_artifact skip set":
                return str(step["run"])
    raise AssertionError("Step 'Verify needs_artifact skip set' not found in .github/workflows/ci.yml")


@pytest.mark.parametrize(
    ("collection_status", "expect_group", "expect_exit"),
    [
        (2, True, 2),
        (1, True, 1),
        (0, False, 0),
        (5, False, 0),
    ],
)
def test_ci_needs_artifact_collection_failure_branch_behavior(
    tmp_path: Path, collection_status: int, expect_group: bool, expect_exit: int
) -> None:
    """Execute the exact 'Verify needs_artifact skip set' workflow step in a hermetic temp environment.

    Minimal stubs provided:
    - Stub ``git`` executable on PATH returning a sample test file for ``git ls-files`` so the
      pipeline ``git ls-files | grep ...`` succeeds hermetically without a git repository.
    - Stub ``.venv/bin/python`` shim (and ``python`` / ``pytest`` on PATH) simulating pytest collection:
      - (a) Collection error (status 2 or 1): emits error message to stdout and exits with status.
      - (b) Success (status 0): emits collected test ID, generates skipped JUnit XML report, and exits 0.
      - (c) No tests (status 5): emits no test IDs, generates empty JUnit XML report, and exits 5.
      For non-pytest invocations (such as the inline validation script), delegates via ``os.execv`` to
      the real project interpreter (``sys.executable``).
    - Stub ``registry/artifacts/needs-artifact-expected.txt`` with the expected ID for status 0 and empty
      for status 5.
    - ``PYTHONPATH`` containing the repository root so ``scripts.storage.test_baseline`` can be imported.
    """
    run_script = _extract_needs_artifact_step_run_script()

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    vbin_dir = tmp_path / ".venv" / "bin"
    vbin_dir.mkdir(parents=True)

    git_stub = bin_dir / "git"
    git_stub.write_text(
        '#!/bin/sh\nif [ "$1" = "ls-files" ]; then\n  echo "tests/storage/test_demo.py"\n  exit 0\nfi\nexit 0\n',
        encoding="utf-8",
    )
    git_stub.chmod(0o755)

    expected_file = tmp_path / "registry" / "artifacts" / "needs-artifact-expected.txt"
    expected_file.parent.mkdir(parents=True, exist_ok=True)
    if collection_status == 0:
        expected_file.write_text("tests.storage.test_demo::test_sample\n", encoding="utf-8")
    else:
        expected_file.write_text("", encoding="utf-8")

    error_line = "ERROR: simulated collection failure in tests/test_broken.py:1: SyntaxError\n"

    python_stub = vbin_dir / "python"
    python_stub.write_text(
        f"""#!{sys.executable}
import os
import pathlib
import sys

args = sys.argv[1:]
if args and args[0] == "-m" and len(args) > 1 and args[1] == "pytest":
    status = int(os.environ.get("STUB_COLLECTION_STATUS", "0"))
    if "--collect-only" in args:
        if status in (1, 2):
            sys.stdout.write(os.environ.get("STUB_ERROR_LINE", "ERROR: simulated collection failure\\n"))
            sys.exit(status)
        elif status == 5:
            sys.exit(5)
        else:
            sys.stdout.write("tests/storage/test_demo.py::test_sample\\n")
            sys.exit(0)
    else:
        junit_path = None
        for a in args:
            if a.startswith("--junitxml="):
                junit_path = a.split("=", 1)[1]
        if junit_path:
            p = pathlib.Path(junit_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            if status == 0:
                p.write_text(
                    '<?xml version="1.0" encoding="utf-8"?>\\n'
                    '<testsuites>\\n'
                    '  <testsuite name="pytest" tests="1" skipped="1">\\n'
                    '    <testcase classname="tests.storage.test_demo" name="test_sample">\\n'
                    '      <skipped message="needs_artifact: missing artifact">needs_artifact: missing artifact</skipped>\\n'
                    '    </testcase>\\n'
                    '  </testsuite>\\n'
                    '</testsuites>\\n',
                    encoding="utf-8",
                )
                sys.exit(0)
            else:
                p.write_text(
                    '<?xml version="1.0" encoding="utf-8"?>\\n'
                    '<testsuites>\\n'
                    '  <testsuite name="pytest" tests="0" skipped="0">\\n'
                    '  </testsuite>\\n'
                    '</testsuites>\\n',
                    encoding="utf-8",
                )
                sys.exit(5)
    sys.exit(0)

os.execv("{sys.executable}", ["{sys.executable}"] + args)
""",
        encoding="utf-8",
    )
    python_stub.chmod(0o755)

    (bin_dir / "python").symlink_to(python_stub)
    pytest_stub = bin_dir / "pytest"
    pytest_stub.write_text(f"""#!/bin/sh
exec "{python_stub}" -m pytest "$@"
""")
    pytest_stub.chmod(0o755)

    repo_root = str(Path(__file__).resolve().parents[2])
    env = dict(
        os.environ,
        PATH=f"{bin_dir}:{vbin_dir}:{os.environ.get('PATH', '')}",
        PYTHONPATH=f"{repo_root}:{os.environ.get('PYTHONPATH', '')}",
        STUB_COLLECTION_STATUS=str(collection_status),
        STUB_ERROR_LINE=error_line,
    )

    proc = subprocess.run(["bash", "-c", run_script], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert proc.returncode == expect_exit
    if expect_group:
        assert "::group::pytest needs_artifact collection failure" in proc.stdout
        assert error_line.strip() in proc.stdout
        assert "::endgroup::" in proc.stdout
    else:
        assert "::group::" not in proc.stdout
        assert error_line.strip() not in proc.stdout
        if collection_status == 0:
            assert "needs_artifact collected=1 skips=1 expected=1" in proc.stdout
        elif collection_status == 5:
            assert "needs_artifact collected=0 skips=0 expected=0" in proc.stdout
