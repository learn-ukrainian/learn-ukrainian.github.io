#!/usr/bin/env python3
"""Deterministic P6 acceptance checker for ADR-011's real UNLP seed records.

This checker deliberately exercises the committed registry rather than synthetic
fixtures.  It measures canonical serialized UTF-8 response bytes, proves the
five P6 routing cases, and drives the actual FastAPI endpoints in an isolated
in-process harness.  It never reads or writes consumption telemetry and never
prints task identifiers, digest bodies, or runtime flag contents.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# A bare script invocation puts ``scripts/audit`` (not the repository root) on
# sys.path.  Keep the documented ``.venv/bin/python scripts/audit/...`` command
# usable without caller-specific PYTHONPATH configuration.  Remove that audit
# directory first: its ``config.py`` would otherwise shadow ``scripts/config.py``
# while importing the audit package.
AUDIT_DIR = Path(__file__).resolve().parent
sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() != AUDIT_DIR]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_router as state_router
from scripts.research import registry as reg

EXPECTED_CASES = (
    (
        "quality_difficulty_core",
        ("quality", "difficulty-gate", "core", ["scripts/audit/text_difficulty.py"]),
        {"unlp-2026-cefr-assessment"},
        342,
    ),
    (
        "tts",
        ("tts", "tts", None, ["scripts/tts/engine.py"]),
        {"unlp-2025-stress-tts"},
        251,
    ),
    (
        "reviewer_prompt",
        (
            "reviewer",
            "reviewer-prompt",
            None,
            ["agents_extensions/shared/rules/workflow.md"],
        ),
        {"unlp-2026-gec-minimal-edit"},
        280,
    ),
    ("unrelated_ui", ("frontend", "ui", None, ["site/src/app.ts"]), set(), 29),
    ("unrelated_ci", ("infra", "ci", None, [".github/workflows/ci.yml"]), set(), 29),
)

EXPECTED_BODIES = {
    "unlp-2026-cefr-assessment": 2630,
    "unlp-2025-stress-tts": 2629,
    "unlp-2026-gec-minimal-edit": 3483,
}
EXPECTED_RESEARCH_COMPONENT_BYTES = 107
EXPECTED_STATE_MANIFEST_BYTES = {"disabled": 912, "enabled": 1031}


@contextmanager
def _isolated_api(root: Path) -> Iterator[TestClient]:
    """Force an isolated, deterministic API process view for byte assertions."""
    prior_root = reg._ROOT_OVERRIDE
    prior_datetime = state_router.datetime
    prior_flag = os.environ.get(reg.ENV_FLAG)
    prior_footer = os.environ.get("LEARN_UKRAINIAN_TELEMETRY_FOOTER")

    class _FrozenDateTime:
        @staticmethod
        def now(tz: Any = None) -> datetime:
            return datetime(2026, 7, 11, 12, 0, 0, 123456, tzinfo=tz or UTC)

    reg._ROOT_OVERRIDE = root
    state_router.datetime = _FrozenDateTime  # type: ignore[assignment]
    os.environ["LEARN_UKRAINIAN_TELEMETRY_FOOTER"] = "0"
    try:
        with TestClient(api_main.app, raise_server_exceptions=False) as client:
            yield client
    finally:
        reg._ROOT_OVERRIDE = prior_root
        state_router.datetime = prior_datetime
        if prior_flag is None:
            os.environ.pop(reg.ENV_FLAG, None)
        else:
            os.environ[reg.ENV_FLAG] = prior_flag
        if prior_footer is None:
            os.environ.pop("LEARN_UKRAINIAN_TELEMETRY_FOOTER", None)
        else:
            os.environ["LEARN_UKRAINIAN_TELEMETRY_FOOTER"] = prior_footer


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def run(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Run all P6 checks and return only report-safe aggregate measurements."""
    runtime = reg.load_runtime(root=root)
    if runtime is None:
        raise AssertionError("committed research registry is not runtime-exposable")

    tp = fp = fn = 0
    cases: dict[str, dict[str, Any]] = {}
    for name, args, expected, expected_bytes in EXPECTED_CASES:
        response = reg.filtered_manifest(runtime, reg.normalize_context(*args))
        actual = {pointer["id"] for pointer in json.loads(response.body)["records"]}
        _assert_equal(actual, expected, f"{name} record ids")
        _assert_equal(len(response.body), expected_bytes, f"{name} serialized UTF-8 bytes")
        tp += len(actual & expected)
        fp += len(actual - expected)
        fn += len(expected - actual)
        cases[name] = {"records": sorted(actual), "bytes": len(response.body)}

    if tp + fp == 0 or tp + fn == 0:
        raise AssertionError("pilot metrics require explicit non-zero positive denominators")
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    _assert_equal(precision, 1.0, "precision")
    _assert_equal(recall, 1.0, "recall")

    record_bytes: dict[str, int] = {}
    for record_id, expected_bytes in EXPECTED_BODIES.items():
        result = reg.record_body(runtime, record_id)
        if result is None:
            raise AssertionError(f"{record_id}: body unavailable")
        body, _etag = result
        actual_bytes = len(body.encode("utf-8"))
        _assert_equal(actual_bytes, expected_bytes, f"{record_id} normalized UTF-8 bytes")
        if actual_bytes > reg.MAX_RECORD_BYTES:
            raise AssertionError(f"{record_id}: production record cap exceeded")
        record_bytes[record_id] = actual_bytes

    manifest_sizes: dict[str, int] = {}
    with _isolated_api(root) as client:
        os.environ[reg.ENV_FLAG] = "false"
        disabled = client.get("/api/state/manifest")
        _assert_equal(disabled.status_code, 200, "disabled state manifest status")
        manifest_sizes["disabled"] = len(disabled.content)
        _assert_equal(
            manifest_sizes["disabled"], EXPECTED_STATE_MANIFEST_BYTES["disabled"], "disabled state manifest bytes"
        )

        os.environ[reg.ENV_FLAG] = "true"
        enabled = client.get("/api/state/manifest")
        _assert_equal(enabled.status_code, 200, "enabled state manifest status")
        manifest_sizes["enabled"] = len(enabled.content)
        _assert_equal(
            manifest_sizes["enabled"], EXPECTED_STATE_MANIFEST_BYTES["enabled"], "enabled state manifest bytes"
        )
        _assert_equal(
            manifest_sizes["enabled"] - manifest_sizes["disabled"],
            119,
            "research state-manifest delta",
        )
        if manifest_sizes["enabled"] >= reg.MAX_STATE_MANIFEST_BYTES:
            raise AssertionError("production state manifest cap exceeded")
        component = enabled.json()["research"]
        component_bytes = len(reg.canonical_json_bytes(component))
        _assert_equal(component_bytes, EXPECTED_RESEARCH_COMPONENT_BYTES, "research manifest component bytes")
        if component_bytes > reg.MAX_RESEARCH_COMPONENT_BYTES:
            raise AssertionError("production research component cap exceeded")

        quality_params = {
            "role": "quality",
            "task_family": "difficulty-gate",
            "track": "core",
            "owned_path": "scripts/audit/text_difficulty.py",
        }
        first = client.get("/api/knowledge/manifest", params=quality_params)
        _assert_equal((first.status_code, len(first.content)), (200, 342), "quality manifest first read")
        quality_etag = first.headers["etag"]
        repeated = client.get("/api/knowledge/manifest", params=quality_params, headers={"If-None-Match": quality_etag})
        _assert_equal((repeated.status_code, len(repeated.content)), (304, 0), "quality manifest warm read")

        control_params = {"role": "frontend", "task_family": "ui", "owned_path": "site/src/app.ts"}
        isolated = client.get("/api/knowledge/manifest", params=control_params, headers={"If-None-Match": quality_etag})
        _assert_equal((isolated.status_code, len(isolated.content)), (200, 29), "context-isolated manifest read")
        control_etag = isolated.headers["etag"]
        control_warm = client.get(
            "/api/knowledge/manifest", params=control_params, headers={"If-None-Match": control_etag}
        )
        _assert_equal((control_warm.status_code, len(control_warm.content)), (304, 0), "control manifest warm read")

        body = client.get("/api/knowledge/record/unlp-2026-cefr-assessment")
        _assert_equal((body.status_code, len(body.content)), (200, 2630), "CEFR record first read")
        body_warm = client.get(
            "/api/knowledge/record/unlp-2026-cefr-assessment",
            headers={"If-None-Match": body.headers["etag"]},
        )
        _assert_equal((body_warm.status_code, len(body_warm.content)), (304, 0), "CEFR record warm read")

    return {
        "ok": True,
        "cases": cases,
        "metrics": {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall},
        "record_body_bytes": record_bytes,
        "research_manifest_component_bytes": EXPECTED_RESEARCH_COMPONENT_BYTES,
        "state_manifest_bytes": manifest_sizes,
        "warm_reads": {
            "quality_manifest": [200, 342, 304, 0],
            "record_body": [200, 2630, 304, 0],
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check ADR-011 P6 real-record pilot invariants.")
    parser.add_argument("--json", action="store_true", help="Print safe aggregate measurements as JSON.")
    args = parser.parse_args(argv)
    try:
        report = run()
    except AssertionError as exc:
        print(f"research-registry pilot FAILED: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print("research-registry pilot: 5 cases, precision=1.0, recall=1.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
