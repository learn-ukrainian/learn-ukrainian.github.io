"""Actual wheel proofs in an empty cwd, with no checkout/Git/scripts access."""

from __future__ import annotations

import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

pytest_plugins = ("test_v4_protected_parent_mechanism",)

REPO_ROOT = Path(__file__).resolve().parents[3]

PROBE = r'''
import contextlib, hashlib, importlib, importlib.util, io, json, runpy, sys, time
from pathlib import Path
installed, dependencies, checkout, module = map(Path, sys.argv[1:])
checkout = checkout.resolve()
declared_paths = [
    path for path in sys.path
    if path and not Path(path).resolve().is_relative_to(checkout)
]
sys.path[:] = [str(dependencies), str(installed), *declared_paths]
assert importlib.util.find_spec("scripts") is None
from learn_ukrainian_v4_runtime import resources
historical = {hashlib.sha256(p.read_bytes()).hexdigest() for p in (installed / resources.NAMESPACE / "provenance/v1/blobs/sha256").iterdir()}
assert len(historical) == 17
blob_reads = set()
def audit(event, args):
    if event == "subprocess.Popen":
        raise AssertionError("runtime must not spawn Git or historical source")
    if event == "compile":
        raw = args[0]
        if isinstance(raw, str): raw = raw.encode()
        if isinstance(raw, bytes):
            assert hashlib.sha256(raw).hexdigest() not in historical, "historical implementation compiled"
    if event == "exec":
        assert not args[0].co_filename.endswith(".blob"), "historical implementation executed"
    if event == "open" and isinstance(args[0], str):
        path = Path(args[0])
        if path.suffix == ".blob": blob_reads.add(path.name)
        assert not path.is_absolute() or not path.is_relative_to(checkout), "checkout read"
sys.addaudithook(audit)
from learn_ukrainian_v4_runtime.provenance import verify_current_identity, validate_package_bindings
from learn_ukrainian_v4_runtime import v4_a3_heldout_family_assignment as a3
identity = verify_current_identity()
validate_package_bindings(json.loads(a3.DEFAULT_RECEIPT.read_bytes()))
# Exercise the complete current module import surface under the same audit hook.
for name in identity["installed_files"]:
    if name.endswith(".py") and name not in {"__init__.py", "_build_identity.py"}:
        importlib.import_module(resources.NAMESPACE + "." + name[:-3])
assert len(blob_reads) == 17
assert not any(name == "scripts" or name.startswith("scripts.") for name in sys.modules)
output = io.StringIO()
sys.argv = [str(module)]
started = time.monotonic()
with contextlib.redirect_stdout(output):
    runpy.run_module(resources.NAMESPACE + "." + str(module), run_name="__main__")
payload = json.loads(output.getvalue())
if str(module) == "v4_a13_cleanup_recovery":
    assert payload["recovery_state"]["epic_closed"] is False
elif str(module) == "v4_per_slot_private_factory":
    counters = payload["execution_counters"]
    assert (counters["slots_stage_complete"], counters["slots_residual"], counters["dataset_rows_emitted"]) == (0, 100, 0)
else:
    gate = next(value for key, value in payload.items() if key.endswith("_gate"))
    assert (gate["slots_stage_complete"], gate["slots_residual"]) == (0, 100)
assert not any(name == "scripts" or name.startswith("scripts.") for name in sys.modules)
print(json.dumps({"cli": str(module), "elapsed": round(time.monotonic() - started, 3), "public_commit": identity["public_commit"], "historical_blobs_hashed_without_execution": len(blob_reads), "output": payload}))
'''


@pytest.fixture(scope="module")
def isolated_install(built_wheel, tmp_path_factory):
    target = tmp_path_factory.mktemp("source-free-installed")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "--no-compile", "--target", str(target), str(built_wheel)],
        check=True, capture_output=True, timeout=120,
    )
    return target


def _distribution_name(requirement: str) -> str | None:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return match.group(1) if match else None


@pytest.fixture(scope="module")
def external_dependencies(tmp_path_factory):
    """Stage only the wheel's declared dependency closure outside the checkout."""
    target = tmp_path_factory.mktemp("source-free-dependencies").resolve()
    assert not target.is_relative_to(REPO_ROOT)
    package_metadata = tomllib.loads(
        (REPO_ROOT / "packages/v4-runtime/pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    distributions = {
        re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower(): dist
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    pending = {
        name
        for requirement in package_metadata["dependencies"]
        if (name := _distribution_name(requirement))
    }
    selected = set()
    while pending:
        name = pending.pop()
        normalized = re.sub(r"[-_.]+", "-", name).lower()
        if normalized in selected:
            continue
        distribution = distributions.get(normalized)
        assert distribution is not None, f"declared runtime dependency is not installed: {name}"
        selected.add(normalized)
        for requirement in distribution.requires or ():
            dependency = _distribution_name(requirement)
            if dependency:
                pending.add(dependency)

    for normalized in sorted(selected):
        distribution = distributions[normalized]
        for listed in distribution.files or ():
            relative = Path(str(listed))
            if relative.is_absolute() or ".." in relative.parts:
                continue
            source = Path(distribution.locate_file(listed))
            if not source.is_file():
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                assert destination.read_bytes() == source.read_bytes(), f"dependency collision: {relative}"
            else:
                shutil.copyfile(source, destination)
    return target


@pytest.mark.parametrize("module", [
    "v4_a7_original_row_factory", "v4_a8_admission_assembly", "v4_a9_evaluation_package",
    "v4_per_slot_private_factory", "v4_a13_cleanup_recovery",
])
def test_default_cli_without_checkout_or_historical_execution(module, isolated_install, external_dependencies, tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", "-c", PROBE, str(isolated_install), str(external_dependencies), str(REPO_ROOT), module],
        cwd=tmp_path, env={**os.environ, "PATH": ""}, capture_output=True, text=True, timeout=110,
    )
    assert result.returncode == 0, result.stderr
    proof = json.loads(result.stdout)
    assert proof["historical_blobs_hashed_without_execution"] == 17
    print(result.stdout.strip())
