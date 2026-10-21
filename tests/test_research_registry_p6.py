"""P6 real-record pilot regressions for ADR-011.

The checker is intentionally run against the real three-record registry.  Its
API harness freezes only response-local time and disables response telemetry;
it does not inspect mutable consumption events or live task state.
"""

from __future__ import annotations

import json

import pytest

from scripts.audit import check_research_registry_pilot as pilot


def test_json_cli_output_is_a_single_parseable_document(capsys: pytest.CaptureFixture[str]) -> None:
    assert pilot.main(["--json"]) == 0

    output = capsys.readouterr().out
    report = json.loads(output)

    assert report["ok"] is True
    assert report["metrics"] == {"tp": 3, "fp": 0, "fn": 0, "precision": 1.0, "recall": 1.0}
