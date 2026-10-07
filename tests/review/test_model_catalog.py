"""Frozen routing evidence for #9302 with the approved #9951 Cursor revision."""

from __future__ import annotations

import gzip
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from scripts.review.model_catalog import load_model_catalog
from scripts.review.role_resolution import expanded_legacy_view

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/routing_baseline"
BASELINE = json.loads(gzip.decompress((FIXTURE / "baseline.json.gz").read_bytes()))
INPUTS = json.loads((FIXTURE / "inputs.json").read_bytes())
CAPTURE = runpy.run_path(str(FIXTURE / "capture.py"))


def test_frozen_hashes_and_matrix_denominator():
    for row in (FIXTURE / "SHA256SUMS").read_text().splitlines():
        digest, name = row.split()
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest
    assert INPUTS["base_sha"] == CAPTURE["BASE_SHA"]
    for surface in ("reviewer", "capacity", "dispatch", "adapters", "launchers"):
        assert len(INPUTS[surface]) == len(BASELINE[surface])
    assert {row["risk"] for row in INPUTS["reviewer"]} == {"low", "medium", "high", "critical"}
    assert {row["review_profile"] for row in INPUTS["reviewer"]} == {"code", "infra"}
    ledger = json.loads(gzip.decompress((FIXTURE / "occurrences.json.gz").read_bytes()))
    assert ledger and all(row["disposition"] and row["purpose"] and row["owner"] for row in ledger)


def test_legacy_catalog_equals_approved_routing_baseline():
    assert expanded_legacy_view() == BASELINE["catalog"]


@pytest.mark.parametrize("entrypoint,args", [
    ("scripts/review/model_catalog.py", ["--resolve-role", "bounded_advisor"]),
    ("scripts/lint/lint_model_catalog.py", ["--as-of", "2026-10-07"]),
])
def test_direct_catalog_callers_without_repository_pythonpath(entrypoint, args, tmp_path):
    source = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-I", str(source / entrypoint), *args],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    if entrypoint.endswith("lint_model_catalog.py"):
        assert payload["ok"] is True
    else:
        assert payload["candidates"][0]["model_id"] == "gpt-6.1-sol"


@pytest.mark.parametrize("host_clis", ["absent", "present"])
def test_fresh_capture_equals_every_frozen_surface(tmp_path, host_clis):
    source = Path(__file__).resolve().parents[2]
    output = tmp_path / "capture"
    host_bin = tmp_path / "host-bin"
    host_bin.mkdir()
    for name in ("bash", "git", "cat"):
        (host_bin / name).symlink_to(shutil.which(name, path="/usr/bin:/bin"))
    if host_clis == "present":
        for name in (*CAPTURE["CLI_VERSIONS"], "npx"):
            stub = host_bin / name
            stub.write_text("#!/bin/sh\nprintf 'ambient CLI must not run\\n' >&2\nexit 99\n")
            stub.chmod(0o755)
    host_home = tmp_path / "host-home"
    host_home.mkdir()
    result = subprocess.run(
        [sys.executable, str(FIXTURE / "capture.py"), "--source-root", str(source),
         "--output", str(output), "--project-python", sys.executable],
        cwd=tmp_path, env={"PATH": str(host_bin), "TMPDIR": str(tmp_path), "HOME": str(host_home),
                          "LAUNCHER_MODEL": "unregistered-model", "CODEX_HOME": str(host_home),
                          "LEARN_UK_AGY_MODEL": "unregistered-model", "LU_ACPX_TRANSPORT": "shadow",
                          "LEARN_UK_KIMI_BIN": str(host_bin / "kimi"), "TZ": "Pacific/Honolulu"},
        capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(gzip.decompress((output / "baseline.json.gz").read_bytes()))
    assert actual.keys() == BASELINE.keys()
    assert len(actual["launchers"]) == len(BASELINE["launchers"]) == 70
    for surface in BASELINE:
        assert actual[surface] == BASELINE[surface], f"frozen surface differs: {surface}"
    assert json.loads((output / "inputs.json").read_bytes()) == INPUTS
    assert (output / "occurrences.json.gz").read_bytes() == (FIXTURE / "occurrences.json.gz").read_bytes()


def test_capture_environment_controls_lookup_and_version_probes(tmp_path):
    env = CAPTURE["capture_environment"](tmp_path)
    assert env["PATH"] == str(tmp_path / "bin")
    assert env["HOME"] == str(tmp_path / "home")
    assert env["TZ"] == "UTC"
    for name, version in CAPTURE["CLI_VERSIONS"].items():
        binary = shutil.which(name, path=env["PATH"])
        assert binary == str(tmp_path / "bin" / name)
        probe = subprocess.run([binary, "--version"], env=env, capture_output=True, text=True, timeout=5)
        assert (probe.returncode, probe.stdout, probe.stderr) == (0, version + "\n", "")
        invoke = subprocess.run([binary, "-p", "fixture"], env=env, capture_output=True, text=True, timeout=5)
        assert invoke.returncode == 97
        assert invoke.stderr == "capture stub refuses provider execution\n"
    assert shutil.which("npx", path=env["PATH"]) is None


def test_capture_encodes_structures_without_reordering_arrays():
    @dataclass
    class Row:
        values: frozenset[str]
        path: Path

    value = {"rows": [Row(frozenset({"b", "a"}), Path("fixture")), "last"]}
    assert json.loads(CAPTURE["encode"](value)) == {"rows": [{"values": ["a", "b"], "path": "fixture"}, "last"]}


@pytest.mark.parametrize("exception", [ValueError("refused"), SystemExit(2)])
def test_capture_preserves_refusals(exception):
    def refuse():
        raise exception

    result = CAPTURE["observed"](refuse)
    assert result["exit_status"] == (2 if isinstance(exception, SystemExit) else 1)
    assert result["exception"] == type(exception).__name__
    assert result["error"] == str(exception)


def test_capture_preserves_success_and_streams(capsys):
    def succeed():
        print("receipt")
        return ["second", "first"]

    assert CAPTURE["observed"](succeed) == {
        "exit_status": 0, "value": ["second", "first"], "stdout": "receipt\n", "stderr": "",
    }
    assert capsys.readouterr().out == ""


def test_capture_matrix_is_frozen():
    assert CAPTURE["reviewer_inputs"](load_model_catalog()) == INPUTS["reviewer"]
