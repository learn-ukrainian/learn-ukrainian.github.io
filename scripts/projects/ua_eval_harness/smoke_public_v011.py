#!/usr/bin/env python3
"""Credential-free end-to-end smoke test for public UA evaluation v0.1.1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.ua_eval_harness.evaluate_model import score_saved_run
from scripts.projects.ua_eval_harness.verify_release_freeze import (
    DEFAULT_OUTPUT as V010_FREEZE,
)
from scripts.projects.ua_eval_harness.verify_release_freeze import (
    validate_freeze as validate_v010_freeze,
)
from scripts.projects.ua_eval_harness.verify_release_freeze_v011 import (
    DEFAULT_OUTPUT as V011_FREEZE,
)
from scripts.projects.ua_eval_harness.verify_release_freeze_v011 import (
    validate_freeze as validate_v011_freeze,
)

V1_BASELINES = ROOT / "data/projects/ua_eval_harness/baselines/v1"
V2_BASELINES = ROOT / "data/projects/ua_eval_harness/baselines/v2"
RUNS = (
    (
        "identity",
        V1_BASELINES / "identity.responses.jsonl",
        V1_BASELINES / "identity.report.json",
    ),
    (
        "deterministic fixture rules",
        V1_BASELINES / "fixture-rules.responses.jsonl",
        V1_BASELINES / "fixture-rules.report.json",
    ),
    (
        "gpt-5.6-terra saved run",
        V1_BASELINES / "gpt-5.6-terra.responses.jsonl",
        V1_BASELINES / "gpt-5.6-terra.report.json",
    ),
    (
        "gemma-4-31b-it saved run",
        V2_BASELINES / "gemma-4-31b-it.responses.jsonl",
        V2_BASELINES / "gemma-4-31b-it.report.json",
    ),
)


class SmokeError(ValueError):
    """The public package cannot reproduce its frozen results."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SmokeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SmokeError(f"expected JSON object in {path}")
    return value


def run_smoke() -> list[dict[str, Any]]:
    """Verify both freezes and reproduce all four saved aggregate reports."""
    validate_v010_freeze(_read_json(V010_FREEZE))
    validate_v011_freeze(_read_json(V011_FREEZE))
    summaries: list[dict[str, Any]] = []
    for name, responses_path, report_path in RUNS:
        actual = score_saved_run(responses_path.relative_to(ROOT))
        expected = _read_json(report_path)
        if actual != expected:
            raise SmokeError(
                f"re-scored report does not match frozen bytes: {name}"
            )
        summaries.append(
            {
                "name": name,
                "responses": actual["exact_sentence"]["total"],
                "edit_f0_5": actual["edit_correction"]["f0_5"],
                "headline_calque_recall": actual["headline_calque"]["recall"],
                "exact_sentence_accuracy": actual["exact_sentence"]["accuracy"],
            }
        )
    return summaries


def main() -> int:
    try:
        summaries = run_smoke()
    except (SmokeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for summary in summaries:
        print(
            f"{summary['name']}: {summary['responses']} responses, "
            f"edit F0.5={summary['edit_f0_5']:.4f}, "
            f"headline calque R="
            f"{summary['headline_calque_recall']:.4f}, "
            f"exact={summary['exact_sentence_accuracy']:.4f}"
        )
    print(
        "public v0.1.1 smoke passed: both freezes and all saved scoring "
        "results reproduced without provider credentials"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
