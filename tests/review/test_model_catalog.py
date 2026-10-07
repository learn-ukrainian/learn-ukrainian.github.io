"""Frozen base-code evidence for the additive #9302 routing migration."""

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


# Literal digests are filled only in the first baseline-strengthening commit.
PINNED_DIGESTS = {
    "SHA256SUMS": "1fb16c2efeea7e031946046d1c02da1bb0cdecf642b5762fd8cddee83f3e146c",
    "SPEC.md": "4ae0e34def54327a2bc219c7c595006fb31d520226bfe9eb72b12153c947a257",
    "baseline.json.gz": "50862470773fc263a6d6ca12d9f4929a3bce6dbfaeb29ff4a1ff7dba916fc110",
    "capture.py": "b89195893ae1c9a3b42978cd0264734c5c70e2dd9599f95d0d4abb4a6605c934",
    "inputs.json": "3078c95cf2275c51e302a9179c9986a60aa3d611aa568f50ec3fc6e915a46fd8",
    "no-cli/SHA256SUMS": "8bbc8c1a409b0dbd02ea61809cff32dd8c6b14e49c044a38e9ed11ce78794b34",
    "no-cli/baseline.json.gz": "95f2f192eec841e1772cc446601514810299b22868dbcd52364818ee654855b3",
    "no-cli/inputs.json": "3078c95cf2275c51e302a9179c9986a60aa3d611aa568f50ec3fc6e915a46fd8",
    "no-cli/occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
    "occurrences.json.gz": "8ca9e434a36e330dab713ddcc8c2c368c18e31666ee18bef2de2505b15aa12c7",
}


def test_frozen_artifacts_are_pinned_independently_of_manifest():
    assert PINNED_DIGESTS
    assert set(PINNED_DIGESTS) == {str(p.relative_to(FIXTURE)) for p in FIXTURE.rglob("*") if p.is_file()}
    for name, expected in PINNED_DIGESTS.items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == expected, name


def test_frozen_hashes_and_matrix_denominator():
    for row in (FIXTURE / "SHA256SUMS").read_text().splitlines():
        digest, name = row.split()
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == digest
    assert INPUTS["base_sha"] == CAPTURE["BASE_SHA"]
    for surface in ("reviewer", "roles", "capacity", "dispatch", "adapters", "launchers"):
        assert len(INPUTS[surface]) == len(BASELINE[surface])
    assert {row["risk"] for row in INPUTS["reviewer"]} == {"low", "medium", "high", "critical"}
    assert {row["review_profile"] for row in INPUTS["reviewer"]} == {"code", "infra"}
    ledger = json.loads(gzip.decompress((FIXTURE / "occurrences.json.gz").read_bytes()))
    assert ledger and all(row["disposition"] and row["purpose"] and row["owner"] for row in ledger)


def test_legacy_catalog_equals_untouched_base():
    assert expanded_legacy_view() == BASELINE["catalog"]


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
        [
            sys.executable,
            str(FIXTURE / "capture.py"),
            "--source-root",
            str(source),
            "--output",
            str(output),
            "--project-python",
            sys.executable,
        ],
        cwd=tmp_path,
        env={
            "PATH": str(host_bin),
            "TMPDIR": str(tmp_path),
            "HOME": str(host_home),
            "LAUNCHER_MODEL": "unregistered-model",
            "CODEX_HOME": str(host_home),
            "LEARN_UK_AGY_MODEL": "unregistered-model",
            "LU_ACPX_TRANSPORT": "shadow",
            "LEARN_UK_KIMI_BIN": str(host_bin / "kimi"),
            "TZ": "Pacific/Honolulu",
        },
        capture_output=True,
        text=True,
        timeout=600,
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
        "exit_status": 0,
        "value": ["second", "first"],
        "stdout": "receipt\n",
        "stderr": "",
    }
    assert capsys.readouterr().out == ""


def test_capture_matrix_is_frozen():
    assert CAPTURE["reviewer_inputs"](load_model_catalog()) == INPUTS["reviewer"]


def test_no_cli_capture_equals_separate_frozen_surface(tmp_path):
    source = Path(__file__).resolve().parents[2]
    output = tmp_path / "capture"
    result = subprocess.run(
        [
            sys.executable,
            str(FIXTURE / "capture.py"),
            "--configuration",
            "no-cli",
            "--source-root",
            str(source),
            "--output",
            str(output),
            "--project-python",
            sys.executable,
        ],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin", "TMPDIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    expected = FIXTURE / "no-cli"
    for name in ("baseline.json.gz", "inputs.json", "occurrences.json.gz", "SHA256SUMS"):
        assert (output / name).read_bytes() == (expected / name).read_bytes(), name
    actual = json.loads(gzip.decompress((output / "baseline.json.gz").read_bytes()))
    assert len(actual["launchers"]) == 70
    errors = [row.get("error", "") for row in actual["adapters"]]
    assert any("grok" in error and "PATH" in error for error in errors)
    assert any("cursor-agent" in error for error in errors)
    assert any(
        row.get("value", {}).get("cmd", [])[:2] == ["npx", "@anthropic-ai/claude-code@latest"]
        for row in actual["adapters"]
    )
    assert any("model probe for cursor could not verify" in row["stderr"] for row in actual["dispatch"])


def test_no_cli_environment_has_only_pinned_npx_probe(tmp_path):
    env = CAPTURE["capture_environment"](tmp_path, "no-cli")
    for name in CAPTURE["CLI_VERSIONS"]:
        assert shutil.which(name, path=env["PATH"]) is None
    assert list((tmp_path / "home").iterdir()) == []
    npx = shutil.which("npx", path=env["PATH"])
    probe = subprocess.run(
        [npx, "@anthropic-ai/claude-code@latest", "--version"], env=env, capture_output=True, text=True, timeout=5
    )
    assert (probe.returncode, probe.stdout, probe.stderr) == (0, "2.1.289 (Claude Code)\n", "")
    for argv in ([npx, "--version"], [npx, "@anthropic-ai/claude-code@latest", "-p", "fixture"]):
        assert subprocess.run(argv, env=env, capture_output=True, timeout=5).returncode == 97


def test_extended_capture_denominator_and_current_contract():
    catalog = load_model_catalog()
    assert set(BASELINE["routing_holders"]["roles"]) == set(catalog["roles"])
    assert set(BASELINE["routing_holders"]["seats"]) == set(catalog["seats"])
    pins = {row["model"] for row in INPUTS["dispatch"]}
    assert {pin for mapping in catalog["budget_substitution_models"].values() for pin in mapping} <= pins
    assert {row["review_attempt"] for row in INPUTS["dispatch"]} == {None, "frozen-review-attempt.yaml"}
    contract = CAPTURE["approval_contract_rows"](Path(__file__).resolve().parents[2], catalog)
    assert contract == BASELINE["approval"]
    assert len(contract["rows"]) == len(catalog["models"]) * 9
    assert {row["outcome"] for row in contract["rows"]} == {"approved", "missing_approval", "operator_disposition"}
    assert all(not row["self_approval_counts"] for row in contract["rows"])
