#!/usr/bin/env python
"""Create and validate local proof for a thread-handoff replacement.

This is deliberately a small, offline protocol.  It proves that the new
thread supplied the challenge contained in its own rollover packet; it never
forks, continues, or resumes a provider conversation or its history.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
STATUS_PASS = "PASS"


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def challenge_digest(challenge: str) -> str:
    return hashlib.sha256(challenge.encode("utf-8")).hexdigest()


def build_pass_proof(
    *,
    rollover_id: str,
    replacement_thread_id: str,
    challenge: str,
    now: datetime,
) -> dict[str, Any]:
    if not rollover_id.strip() or not replacement_thread_id.strip() or not challenge.strip():
        raise ValueError("rollover id, replacement thread id, and challenge are required")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_PASS,
        "rollover_id": rollover_id.strip(),
        "replacement_thread_id": replacement_thread_id.strip(),
        "challenge_sha256": challenge_digest(challenge.strip()),
        "proven_at": isoformat_z(now),
        "proven_by": "scripts/orchestration/thread_handoff_canary.py",
    }


def validate_pass_proof(
    payload: Any,
    *,
    rollover_id: str,
    replacement_thread_id: str,
    challenge: str,
) -> str | None:
    if not isinstance(payload, dict):
        return "canary proof must be a JSON object"
    if payload.get("schema_version") != SCHEMA_VERSION:
        return "canary proof schema version is unsupported"
    if payload.get("status") != STATUS_PASS:
        return "canary proof did not report PASS"
    if payload.get("proven_by") != "scripts/orchestration/thread_handoff_canary.py":
        return "canary proof was not produced by the thread handoff canary script"
    if payload.get("rollover_id") != rollover_id:
        return "canary proof rollover_id does not match the pending rollover"
    if payload.get("replacement_thread_id") != replacement_thread_id:
        return "canary proof replacement_thread_id does not match --new-thread-id"
    if payload.get("challenge_sha256") != challenge_digest(challenge):
        return "canary proof challenge does not match the pending rollover"
    return None


def load_and_validate_pass_proof(
    path: Path,
    *,
    rollover_id: str,
    replacement_thread_id: str,
    challenge: str,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"cannot read canary proof: {type(exc).__name__}: {exc}"
    error = validate_pass_proof(
        payload,
        rollover_id=rollover_id,
        replacement_thread_id=replacement_thread_id,
        challenge=challenge,
    )
    return payload if error is None else None, error


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollover-id", required=True)
    parser.add_argument("--replacement-thread-id", required=True)
    parser.add_argument("--challenge", required=True)
    parser.add_argument("--proof-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        proof = build_pass_proof(
            rollover_id=args.rollover_id,
            replacement_thread_id=args.replacement_thread_id,
            challenge=args.challenge,
            now=utc_now(),
        )
    except ValueError as exc:
        parser.error(str(exc))
    write_json_atomic(args.proof_file, proof)
    print(json.dumps({"status": STATUS_PASS, "proof_file": args.proof_file.as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
