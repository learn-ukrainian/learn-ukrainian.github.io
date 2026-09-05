#!/usr/bin/env python3
"""Fail-closed held-out scoring receipts for V4 admitted rows.

This is the shared, reusable scoring engine A9 wires (never replaces): given
a batch of already-*admitted* rows (from the shared
``v4_original_row_admission`` engine's own ``admitted`` disposition), it
would score each one against its held-out reference. It never opens A3's
held-out membership file and never receives one -- there is no
``heldout_reference`` parameter here, deliberately, so this engine cannot
score anything by construction until a held-out reference is supplied through
some other, still-to-be-designed channel that keeps membership private. Every
row it is asked to score today is reported ``scored: false`` with a typed
``HELDOUT_REFERENCE_UNAVAILABLE`` residual code -- never a fabricated score
standing in for the missing reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v4-evaluation-scorer-v1"
INPUT_SCHEMA_VERSION = "v4-evaluation-scorer-input-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNSCORABLE_RESIDUAL_CODE = "HELDOUT_REFERENCE_UNAVAILABLE"


class EvaluationScorerError(ValueError):
    """The scoring batch shape is not safe to evaluate."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def score_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a text-free, never-fabricated score receipt for one admitted
    row. This function is never given source text, a held-out reference, or
    held-out membership -- only a row's already-public ``row_id`` and
    ``row_content_sha256`` -- so it can only ever report the row unscorable;
    a real score requires a real reference channel this engine does not
    have."""
    if not isinstance(row, Mapping):
        raise EvaluationScorerError("row must be an object")
    row_id = row.get("row_id")
    if not isinstance(row_id, str) or not row_id:
        raise EvaluationScorerError("ROW_ID_INVALID")
    row_content_sha256 = row.get("row_content_sha256")
    if not isinstance(row_content_sha256, str) or SHA256_RE.fullmatch(row_content_sha256) is None:
        raise EvaluationScorerError("ROW_CONTENT_SHA256_INVALID")
    result = {
        "row_id": row_id,
        "row_content_sha256": row_content_sha256,
        "scored": False,
        "score": None,
        "residual_code": UNSCORABLE_RESIDUAL_CODE,
    }
    result["receipt_sha256"] = sha256_value(result)
    return result


def score_rows(*, outcome_sha256: str, admitted_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not isinstance(admitted_rows, Sequence) or isinstance(admitted_rows, (str, bytes)):
        raise EvaluationScorerError("admitted_rows must be a list")
    if not isinstance(outcome_sha256, str) or SHA256_RE.fullmatch(outcome_sha256) is None:
        raise EvaluationScorerError("OUTCOME_SHA256_INVALID")
    scores = [score_row(row) for row in admitted_rows]
    ids = [item["row_id"] for item in scores]
    if len(ids) != len(set(ids)):
        raise EvaluationScorerError("row IDs must be unique in a scoring batch")
    result = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "machine_receipt_text_free",
        "outcome_sha256": outcome_sha256,
        "scores": scores,
        "counts": {
            "input_rows": len(scores),
            "scored_rows": sum(item["scored"] for item in scores),
            "unscored_rows": sum(not item["scored"] for item in scores),
        },
    }
    result["receipt_sha256"] = sha256_value(result)
    return result


def verify_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise EvaluationScorerError("receipt must be an object")
    body = dict(receipt)
    supplied = body.pop("receipt_sha256", None)
    if not isinstance(supplied, str) or supplied != sha256_value(body):
        raise EvaluationScorerError("receipt hash drift")
    if body.get("schema_version") != SCHEMA_VERSION:
        raise EvaluationScorerError("receipt schema drift")
    if set(body) != {"schema_version", "visibility", "outcome_sha256", "scores", "counts"} or body.get("visibility") != "machine_receipt_text_free":
        raise EvaluationScorerError("receipt schema drift")
    if not isinstance(body.get("outcome_sha256"), str) or SHA256_RE.fullmatch(body["outcome_sha256"]) is None:
        raise EvaluationScorerError("receipt outcome SHA-256 drift")
    scores, counts = body.get("scores"), body.get("counts")
    if not isinstance(scores, list) or not isinstance(counts, Mapping):
        raise EvaluationScorerError("receipt schema drift")
    if counts != {
        "input_rows": len(scores),
        "scored_rows": sum(item.get("scored") is True for item in scores if isinstance(item, Mapping)),
        "unscored_rows": sum(item.get("scored") is False for item in scores if isinstance(item, Mapping)),
    }:
        raise EvaluationScorerError("receipt count drift")
    required_score_keys = {"row_id", "row_content_sha256", "scored", "score", "residual_code", "receipt_sha256"}
    for item in scores:
        if not isinstance(item, Mapping) or set(item) != required_score_keys:
            raise EvaluationScorerError("score receipt schema drift")
        item_body = dict(item)
        item_hash = item_body.pop("receipt_sha256")
        if not isinstance(item_hash, str) or item_hash != sha256_value(item_body):
            raise EvaluationScorerError("score receipt hash drift")
        if item.get("scored") is not False or item.get("score") is not None or item.get("residual_code") != UNSCORABLE_RESIDUAL_CODE:
            raise EvaluationScorerError("this engine build cannot legitimately produce a real score -- refusing")
    return dict(receipt)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="versioned JSON object containing outcome_sha256 and admitted_rows")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping) or set(payload) != {"schema_version", "outcome_sha256", "admitted_rows"} or payload.get("schema_version") != INPUT_SCHEMA_VERSION:
            raise EvaluationScorerError("input schema drift")
        receipt = score_rows(outcome_sha256=payload["outcome_sha256"], admitted_rows=payload["admitted_rows"])
        args.output.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    except (EvaluationScorerError, OSError, json.JSONDecodeError) as exc:
        print(f"V4 evaluation scorer: FAIL: {exc}", file=sys.stderr)
        return 1
    print(canonical_json({"receipt_sha256": receipt["receipt_sha256"], **receipt["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
