"""Frozen base-code evidence for the additive #9302 routing migration."""

from __future__ import annotations

import gzip
import hashlib
import json
import runpy
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


def test_legacy_catalog_equals_untouched_base():
    assert expanded_legacy_view() == BASELINE["catalog"]


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
